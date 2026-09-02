import csv
import re
from dataclasses import dataclass


@dataclass
class Contact:
    name: str
    email: str
    company: str
    role: str


def is_valid_email(email):
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def load_contacts(file_path):
    contacts = []
    seen_emails = set()

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=2):
            name = row["name"].strip()
            email = row["email"].strip().lower()
            company = row["company"].strip()
            role = row["role"].strip()

            if not name or not email or not company or not role:
                raise ValueError(
                    f"Missing required information on row {row_number}"
                )

            if not is_valid_email(email):
                raise ValueError(
                    f"Invalid email on row {row_number}: {email}"
                )

            if email in seen_emails:
                raise ValueError(
                    f"Duplicate email on row {row_number}: {email}"
                )

            seen_emails.add(email)

            contacts.append(
                Contact(
                    name=name,
                    email=email,
                    company=company,
                    role=role
                )
            )

    return contacts