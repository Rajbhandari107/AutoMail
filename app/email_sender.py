import base64
import mimetypes
import os
from email.message import EmailMessage

from googleapiclient.discovery import build


def send_email(credentials, recipient, subject, body, attachment_path=None):
    message = EmailMessage()

    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    if attachment_path:
        if not os.path.exists(attachment_path):
            raise FileNotFoundError(
                f"Attachment not found: {attachment_path}"
            )

        mime_type, _ = mimetypes.guess_type(attachment_path)

        if mime_type is None:
            mime_type = "application/octet-stream"

        maintype, subtype = mime_type.split("/", 1)

        with open(attachment_path, "rb") as file:
            message.add_attachment(
                file.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(attachment_path)
            )

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    gmail_service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    result = gmail_service.users().messages().send(
        userId="me",
        body={"raw": encoded_message}
    ).execute()

    return result