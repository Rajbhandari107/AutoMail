import csv
import os
from datetime import datetime


class CampaignLogger:

    def __init__(self, log_file):
        self.log_file = log_file

        os.makedirs(
            os.path.dirname(log_file),
            exist_ok=True
        )

        if not os.path.exists(log_file):
            self._create_log_file()

    def _create_log_file(self):
        with open(
            self.log_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "recipient",
                "status",
                "message_id",
                "error"
            ])

    def log(
        self,
        recipient,
        status,
        message_id="",
        error=""
    ):
        with open(
            self.log_file,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                datetime.now().isoformat(timespec="seconds"),
                recipient,
                status,
                message_id,
                error
            ])
    def was_sent(self, recipient):
        if not os.path.exists(self.log_file):
            return False

        with open(
            self.log_file,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                if (
                    row["recipient"].strip().lower() == recipient.lower()
                    and row["status"] == "SENT"
                ):
                    return True

        return False