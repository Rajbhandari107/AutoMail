import os

from app.auth import get_gmail_credentials
from app.config import EMAIL_ADDRESS
from app.email_sender import send_email


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

    print("Gmail authentication successful!")
    print(f"Sending email to: {EMAIL_ADDRESS}")
    print(f"Attachment: {RESUME_PATH}")

    result = send_email(
        credentials=credentials,
        recipient=EMAIL_ADDRESS,
        subject="AutoMail Test — Resume Attachment",
        body=(
            "Hello!\n\n"
            "This is a test email sent using AutoMail.\n\n"
            "The resume is attached."
        ),
        attachment_path=RESUME_PATH
    )

    print("Email sent successfully!")
    print("Message ID:", result["id"])


if __name__ == "__main__":
    main()