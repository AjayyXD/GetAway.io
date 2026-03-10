import os
import datetime

import mysql.connector
from mysql.connector import Error


class Database:
    """Handles all MySQL interactions for the GetAway leave portal."""

    HOST = os.environ.get("DB_HOST")
    USER = os.environ.get("DB_USER")
    PASSWORD = os.environ.get("DB_PASSWORD")
    DATABASE = os.environ.get("DB_NAME")

    # -- Connection ----------------------------------------------------------

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=self.HOST,
                user=self.USER,
                passwd=self.PASSWORD,
                database=self.DATABASE,
            )
        except Error as e:
            print(f"[DB] Connection error: {e}")
            return None

    # -- Users ---------------------------------------------------------------

    def get_user_data(self, user_id, role):
        """Fetch login-relevant fields for a user based on their role."""
        id_column = "student_id" if role == "Student" else "id"

        field_map = {
            "Student": "name, password_hash, suspended",
            "Admin":   "name, password_hash, role",
        }
        fields = field_map.get(role, "name, password_hash")
        query = f"SELECT {fields} FROM {role} WHERE {id_column} = %s"

        return self._fetch_one(query, (user_id,))

    # -- Leave submission ----------------------------------------------------

    def insert_leave_request(self, leave_data, is_suspended):
        """
        Insert a new leave request.
        - Leaves >= 3 working days also require Dean and HOD approval.
        - Suspended students bypass warden approval (pre-set to Approved).
        """
        needs_extended_approval = leave_data["working_days"] >= 2

        columns = [
            "leave_id", "rollno", "reason",
            "start_date", "out_time", "end_date", "in_time",
            "fa_status", "address", "parent_phone", "student_phone",
            "total_days", "working_days",
        ]
        values = [
            leave_data["leave_id"],
            leave_data["rollno"],
            leave_data["reason"],
            leave_data["start_date"],
            leave_data["out_time"],
            leave_data["end_date"],
            leave_data["in_time"],
            "Pending",
            leave_data["address"],
            leave_data["parent_phone"],
            leave_data["student_phone"],
            leave_data["total_days"],
            leave_data["working_days"],
        ]

        if is_suspended:
            columns.append("warden_status")
            values.append("Approved")

        if needs_extended_approval:
            columns.extend(["dean_status", "hod_status"])
            values.extend(["Pending", "Pending"])

        placeholders = ", ".join(["%s"] * len(columns))
        col_list = ", ".join(columns)
        query = f"INSERT INTO leaves ({col_list}) VALUES ({placeholders})"

        connection = self.get_connection()
        if connection is None:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(query, values)
            inserted_row_id = cursor.lastrowid

            year = datetime.datetime.now().strftime("%y")
            final_leave_id = f"LR{year}-{inserted_row_id:06d}"
            cursor.execute(
                "UPDATE leaves SET leave_id = %s WHERE id = %s",
                (final_leave_id, inserted_row_id),
            )
            connection.commit()
            return True
        except Error as e:
            print(f"[DB] Failed to insert leave request: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

    # -- Leave queries -------------------------------------------------------

    _APPROVER_COLUMNS = """
        Student.name, leaves.leave_id, leaves.rollno, leaves.reason,
        leaves.start_date, leaves.out_time, leaves.end_date, leaves.in_time,
        leaves.address, leaves.parent_phone, leaves.student_phone,
        leaves.FA_Remarks, leaves.total_days, leaves.working_days
    """

    def view_leaves(self, role, user_id):
        """Return leaves relevant to the given role and user."""
        query_map = {
            "Student": (
                "SELECT * FROM leaves WHERE rollno = %s ORDER BY id DESC",
                (user_id,),
            ),
            "FA": (
                f"""
                SELECT Student.name, leaves.leave_id, leaves.rollno, leaves.reason,
                       leaves.start_date, leaves.out_time, leaves.end_date, leaves.in_time,
                       leaves.student_phone, leaves.working_days, leaves.total_days,
                       leaves.parent_phone, leaves.address
                FROM leaves
                JOIN Student ON leaves.rollno = Student.student_id
                WHERE Student.fa_id = %s AND leaves.fa_status = 'Pending'
                ORDER BY leaves.leave_id DESC
                """,
                (user_id,),
            ),
            "Warden": (
                f"""
                SELECT {self._APPROVER_COLUMNS}
                FROM leaves
                JOIN Student ON leaves.rollno = Student.student_id
                WHERE Student.warden_id = %s
                  AND leaves.fa_status = 'Approved'
                  AND leaves.warden_status = 'Pending'
                  AND Student.suspended = 0
                ORDER BY leaves.leave_id DESC
                """,
                (user_id,),
            ),
            "Admin": (
                f"""
                SELECT {self._APPROVER_COLUMNS}
                FROM leaves
                JOIN Student ON leaves.rollno = Student.student_id
                WHERE leaves.warden_status = 'Approved'
                  AND leaves.admin_status = 'Pending'
                  AND leaves.dean_status != 'Pending'
                  AND leaves.hod_status != 'Pending'
                ORDER BY leaves.leave_id DESC
                """,
                (),
            ),
            "Dean": (
                f"""
                SELECT {self._APPROVER_COLUMNS}
                FROM leaves
                JOIN Student ON leaves.rollno = Student.student_id
                WHERE leaves.warden_status = 'Approved'
                  AND leaves.dean_status = 'Pending'
                ORDER BY leaves.leave_id DESC
                """,
                (),
            ),
            "Hod": (
                f"""
                SELECT {self._APPROVER_COLUMNS}
                FROM leaves
                JOIN Student ON leaves.rollno = Student.student_id
                WHERE leaves.warden_status = 'Approved'
                  AND leaves.hod_status = 'Pending'
                ORDER BY leaves.leave_id DESC
                """,
                (),
            ),
            "academics2": (
                f"""
                SELECT {self._APPROVER_COLUMNS}
                FROM leaves
                JOIN Student ON leaves.rollno = Student.student_id
                WHERE leaves.admin_status = 'Approved'
                ORDER BY leaves.leave_id DESC
                """,
                (),
            ),
        }

        entry = query_map.get(role)
        if entry is None:
            return []

        query, params = entry
        return self._fetch_all(query, params)

    # -- Leave approvals -----------------------------------------------------

    def update_leave_status(self, leave_id, status_column, status, remarks=None):
        """
        Generic leave status update. Sets the given status column to the given status.
        Optionally sets FA_Remarks when remarks are provided.
        """
        connection = self.get_connection()
        if connection is None:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(
                f"UPDATE leaves SET {status_column} = %s WHERE leave_id = %s",
                (status, leave_id),
            )
            if remarks is not None:
                cursor.execute(
                    "UPDATE leaves SET FA_Remarks = %s WHERE leave_id = %s",
                    (remarks, leave_id),
                )
            connection.commit()
            return True
        except Error as e:
            print(f"[DB] Status update failed for {leave_id}: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

    def approve_leave(self, leave_id, status_column, remarks=None):
        return self.update_leave_status(leave_id, status_column, "Approved", remarks=remarks)

    def reject_leave(self, leave_id, status_column, remarks=None):
        return self.update_leave_status(leave_id, status_column, "Rejected", remarks=remarks)

    # -- Internal helpers ----------------------------------------------------

    def _fetch_one(self, query, params=()):
        connection = self.get_connection()
        if connection is None:
            return None
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            print(f"[DB] Query error: {e}")
            return None
        finally:
            cursor.close()
            connection.close()

    def _fetch_all(self, query, params=()):
        connection = self.get_connection()
        if connection is None:
            return None
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            print(f"[DB] Query error: {e}")
            return None
        finally:
            cursor.close()
            connection.close()