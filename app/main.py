import os

from app.auth import get_gmail_credentials
from app.config import EMAIL_ADDRESS
from app.contacts.manager import load_contacts
from app.email_sender import send_email
from app.templates.renderer import render_template


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONTACTS_PATH = os.path.join(
    BASE_DIR,
    "data",
    "contacts.csv"
)

TEMPLATE_PATH = os.path.join(
    BASE_DIR,
    "templates",
    "internship.txt"
)

RESUME_PATH = os.path.join(
    BASE_DIR,
    "attachments",
    "Resume.pdf"
)


def main():
    credentials = get_gmail_credentials()

    if not credentials or not credentials.valid:
        print("Gmail authentication failed.")
        return

    contacts = load_contacts(CONTACTS_PATH)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
        template = file.read()

    print(f"Loaded {len(contacts)} contacts.")

    # TEST: send only to yourself
    contact = contacts[0]

    subject, body = render_template(
        template,
        contact
    )

    print(f"Sending test email to: {EMAIL_ADDRESS}")
    print(f"Subject: {subject}")

    result = send_email(
        credentials=credentials,
        recipient=EMAIL_ADDRESS,
        subject=subject,
        body=body,
        attachment_path=RESUME_PATH
    )

    print("Email sent successfully!")
    print("Message ID:", result["id"])


if __name__ == "__main__":
    main()