from datetime import datetime


class CampaignRepository:

    def __init__(self, get_connection):
        self.get_connection = get_connection

    def create(self, name):
        connection = self.get_connection()
        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            INSERT INTO campaigns (
                name,
                status,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (name, "DRAFT", created_at)
        )

        campaign_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return campaign_id

    def add_recipient(self, campaign_id, contact):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO campaign_recipients (
                campaign_id,
                name,
                email,
                company,
                role,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                contact.name,
                contact.email,
                contact.company,
                contact.role,
                "PENDING"
            )
        )

        recipient_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return recipient_id

    def mark_started(self, campaign_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        started_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            UPDATE campaigns
            SET status = ?, started_at = ?
            WHERE id = ?
            """,
            (
                "RUNNING",
                started_at,
                campaign_id
            )
        )

        connection.commit()
        connection.close()

    def mark_completed(self, campaign_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        completed_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            UPDATE campaigns
            SET status = ?, completed_at = ?
            WHERE id = ?
            """,
            (
                "COMPLETED",
                completed_at,
                campaign_id
            )
        )

        connection.commit()
        connection.close()

    def mark_failed(self, campaign_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE campaigns
            SET status = ?
            WHERE id = ?
            """,
            (
                "FAILED",
                campaign_id
            )
        )

        connection.commit()
        connection.close()

    def update_recipient(
        self,
        recipient_id,
        status,
        message_id="",
        error=""
    ):
        connection = self.get_connection()
        cursor = connection.cursor()

        sent_at = None

        if status == "SENT":
            sent_at = datetime.now().isoformat(
                timespec="seconds"
            )

        cursor.execute(
            """
            UPDATE campaign_recipients
            SET
                status = ?,
                message_id = ?,
                error = ?,
                sent_at = ?
            WHERE id = ?
            """,
            (
                status,
                message_id,
                error,
                sent_at,
                recipient_id
            )
        )

        connection.commit()
        connection.close()

    def get_all(self):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                status,
                created_at,
                started_at,
                completed_at
            FROM campaigns
            ORDER BY id DESC
            """
        )

        campaigns = cursor.fetchall()

        connection.close()

        return campaigns

    def get_recipients(self, campaign_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                campaign_id,
                name,
                email,
                company,
                role,
                status,
                message_id,
                error,
                sent_at
            FROM campaign_recipients
            WHERE campaign_id = ?
            ORDER BY id
            """,
            (campaign_id,)
        )

        recipients = cursor.fetchall()

        connection.close()

        return recipients

    def get_recipient_counts(self, campaign_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                status,
                COUNT(*) AS count
            FROM campaign_recipients
            WHERE campaign_id = ?
            GROUP BY status
            """,
            (campaign_id,)
        )

        rows = cursor.fetchall()

        connection.close()

        counts = {
            "PENDING": 0,
            "SENT": 0,
            "FAILED": 0,
            "SKIPPED": 0
        }

        for row in rows:
            counts[row["status"]] = row["count"]

        counts["TOTAL"] = sum(
            counts.values()
        )

        return counts

    def was_contact_sent(self, email):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM campaign_recipients
            WHERE LOWER(email) = LOWER(?)
              AND status = 'SENT'
            LIMIT 1
            """,
            (email,)
        )

        result = cursor.fetchone()

        connection.close()

        return result is not None