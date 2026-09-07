from datetime import datetime


class CampaignRepository:

    def __init__(self, get_connection):
        self.get_connection = get_connection

    def create(
        self,
        name,
        template="internship.txt",
        attachment_path=None,
        delay_seconds=2
    ):
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
                template,
                attachment_path,
                delay_seconds,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                "DRAFT",
                template,
                attachment_path,
                delay_seconds,
                created_at
            )
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

    def get_campaign(self, campaign_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                status,
                template,
                attachment_path,
                delay_seconds,
                created_at,
                started_at,
                completed_at
            FROM campaigns
            WHERE id = ?
            """,
            (campaign_id,)
        )

        campaign = cursor.fetchone()

        connection.close()

        return campaign

    def mark_started(self, campaign_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        campaign = self.get_campaign(campaign_id)

        if campaign is None:
            connection.close()
            raise ValueError(
                f"Campaign #{campaign_id} does not exist."
            )

        if campaign["status"] != "DRAFT":
            connection.close()
            raise ValueError(
                f"Campaign #{campaign_id} cannot be started "
                f"because its status is "
                f"{campaign['status']}."
            )

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

        campaign = self.get_campaign(campaign_id)

        if campaign is None:
            connection.close()
            raise ValueError(
                f"Campaign #{campaign_id} does not exist."
            )

        if campaign["status"] != "RUNNING":
            connection.close()
            raise ValueError(
                f"Campaign #{campaign_id} cannot be completed "
                f"because its status is "
                f"{campaign['status']}."
            )

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

        campaign = self.get_campaign(campaign_id)

        if campaign is None:
            connection.close()
            raise ValueError(
                f"Campaign #{campaign_id} does not exist."
            )

        if campaign["status"] != "RUNNING":
            connection.close()
            raise ValueError(
                f"Campaign #{campaign_id} cannot be marked "
                f"failed because its status is "
                f"{campaign['status']}."
            )

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
        allowed_statuses = {
            "SENT",
            "FAILED",
            "SKIPPED"
        }

        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid recipient status: {status}"
            )

        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                status
            FROM campaign_recipients
            WHERE id = ?
            """,
            (recipient_id,)
        )

        recipient = cursor.fetchone()

        if recipient is None:
            connection.close()
            raise ValueError(
                f"Recipient #{recipient_id} does not exist."
            )

        if recipient["status"] != "PENDING":
            connection.close()
            raise ValueError(
                f"Recipient #{recipient_id} cannot change "
                f"from {recipient['status']} to {status}."
            )

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

    def get_all(self):

        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                status,
                template,
                attachment_path,
                delay_seconds,
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

    def remove_recipient(
        self,
        campaign_id,
        recipient_id
    ):
        connection = self.get_connection()
        cursor = connection.cursor()

        try:
            campaign = self.get_campaign(
                campaign_id
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign #{campaign_id} does not exist."
                )

            if campaign["status"] != "DRAFT":
                raise ValueError(
                    f"Campaign #{campaign_id} cannot be edited "
                    f"because its status is "
                    f"{campaign['status']}."
                )

            cursor.execute(
                """
                SELECT id
                FROM campaign_recipients
                WHERE id = ?
                AND campaign_id = ?
                """,
                (
                    recipient_id,
                    campaign_id
                )
            )

            recipient = cursor.fetchone()

            if recipient is None:
                raise ValueError(
                    f"Recipient #{recipient_id} "
                    f"does not belong to campaign "
                    f"#{campaign_id}."
                )

            cursor.execute(
                """
                DELETE FROM campaign_recipients
                WHERE id = ?
                AND campaign_id = ?
                """,
                (
                    recipient_id,
                    campaign_id
                )
            )

            connection.commit()

        finally:
            connection.close()