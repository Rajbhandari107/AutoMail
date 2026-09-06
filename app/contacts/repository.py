from datetime import datetime

from app.contacts.manager import Contact


class ContactRepository:

    def __init__(self, get_connection):
        self.get_connection = get_connection

    def create(self, contact):

        connection = self.get_connection()
        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        try:

            cursor.execute(
                """
                INSERT INTO contacts (
                    name,
                    email,
                    company,
                    role,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    contact.name,
                    contact.email,
                    contact.company,
                    contact.role,
                    created_at
                )
            )

            contact_id = cursor.lastrowid

            connection.commit()

            return contact_id

        finally:

            connection.close()

    def get_all(self):

        connection = self.get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    company,
                    role,
                    created_at
                FROM contacts
                ORDER BY id
                """
            )

            return cursor.fetchall()

        finally:

            connection.close()

    def get_by_id(self, contact_id):

        connection = self.get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    company,
                    role,
                    created_at
                FROM contacts
                WHERE id = ?
                """,
                (contact_id,)
            )

            return cursor.fetchone()

        finally:

            connection.close()

    def get_by_email(self, email):

        connection = self.get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    company,
                    role,
                    created_at
                FROM contacts
                WHERE LOWER(email) = LOWER(?)
                """,
                (email,)
            )

            return cursor.fetchone()

        finally:

            connection.close()

    def get_contacts_as_objects(self):

        rows = self.get_all()

        return [
            Contact(
                name=row["name"],
                email=row["email"],
                company=row["company"],
                role=row["role"]
            )
            for row in rows
        ]