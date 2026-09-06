import os
import sys

from app.auth import get_gmail_credentials
from app.config import EMAIL_ADDRESS
from app.contacts.manager import load_contacts
from app.contacts.importer import import_contacts
from app.contacts.repository import ContactRepository
from app.email_sender import send_email
from app.templates.renderer import render_template
from app.campaigns.service import CampaignService
from app.campaigns.repository import CampaignRepository
from app.campaigns.manager import CampaignManager
from app.tracking.logger import CampaignLogger
from app.database.db import get_connection, initialize_database


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

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

LOG_PATH = os.path.join(
    BASE_DIR,
    "data",
    "campaign_logs.csv"
)


def load_template():

    with open(
        TEMPLATE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


def build_application():

    initialize_database()

    campaign_repository = CampaignRepository(
        get_connection
    )

    contact_repository = ContactRepository(
        get_connection
    )

    template = load_template()

    def render_for_contact(contact):

        return render_template(
            template,
            contact
        )

    logger = CampaignLogger(
        LOG_PATH
    )

    credentials = None

    def gmail_sender(
        recipient,
        subject,
        body,
        attachment_path=None
    ):

        nonlocal credentials

        if credentials is None:
            credentials = get_gmail_credentials()

        return send_email(
            credentials=credentials,
            recipient=recipient,
            subject=subject,
            body=body,
            attachment_path=attachment_path
        )

    campaign_service = CampaignService(
        email_sender=gmail_sender,
        logger=logger,
        contact_already_sent=(
            campaign_repository.was_contact_sent
        )
    )

    campaign_manager = CampaignManager(
        repository=campaign_repository,
        campaign_service=campaign_service
    )

    return (
        campaign_repository,
        contact_repository,
        campaign_manager,
        render_for_contact
    )


def import_contacts_command():

    initialize_database()

    contact_repository = ContactRepository(
        get_connection
    )

    result = import_contacts(
        CONTACTS_PATH,
        contact_repository
    )

    print(
        "\nContact import complete"
    )

    print(
        f"Total: {result['total']}"
    )

    print(
        f"Imported: {result['imported']}"
    )

    print(
        f"Skipped: {result['skipped']}"
    )


def create_campaign():

    (
        repository,
        contact_repository,
        manager,
        _
    ) = build_application()

    contacts = (
        contact_repository
        .get_contacts_as_objects()
    )

    if not contacts:

        print(
            "No contacts found in SQLite."
        )

        print(
            "Run: "
            "python -m app.main import-contacts"
        )

        return

    campaign_id, recipient_ids = (
        manager.create_campaign(
            name="Internship Outreach",
            contacts=contacts
        )
    )

    print(
        f"Created campaign #{campaign_id}"
    )

    print(
        "Status: DRAFT"
    )

    print(
        f"Recipients: {len(recipient_ids)}"
    )


def run_campaign(
    campaign_id,
    dry_run
):

    (
        repository,
        _,
        manager,
        render_for_contact
    ) = build_application()

    campaign = repository.get_campaign(
        campaign_id
    )

    if campaign is None:

        print(
            f"Campaign #{campaign_id} not found."
        )

        return

    if campaign["status"] != "DRAFT":

        print(
            f"Campaign #{campaign_id} is "
            f"{campaign['status']}, not DRAFT."
        )

        return

    if dry_run:

        print(
            f"Starting DRY RUN for campaign "
            f"#{campaign_id}"
        )

    else:

        print(
            f"Starting REAL SEND for campaign "
            f"#{campaign_id}"
        )

        print(
            "WARNING: Emails will actually be sent."
        )

    results = manager.start_campaign(
        campaign_id=campaign_id,
        template_renderer=render_for_contact,
        attachment_path=RESUME_PATH,
        recipient_override=(
            EMAIL_ADDRESS
            if dry_run
            else None
        ),
        dry_run=dry_run,
        delay_seconds=2
    )

    print(
        "\nCampaign summary"
    )

    for result in results:

        print(
            f"{result['recipient']} → "
            f"{result['status']}"
        )

    counts = repository.get_recipient_counts(
        campaign_id
    )

    print(
        "\nRecipient progress"
    )

    print(
        f"Total: {counts['TOTAL']}"
    )

    print(
        f"Pending: {counts['PENDING']}"
    )

    print(
        f"Sent: {counts['SENT']}"
    )

    print(
        f"Failed: {counts['FAILED']}"
    )

    print(
        f"Skipped: {counts['SKIPPED']}"
    )


def show_history():

    (
        repository,
        _,
        _,
        _
    ) = build_application()

    campaigns = repository.get_all()

    if not campaigns:

        print(
            "No campaigns found."
        )

        return

    print(
        "\nCampaign history"
    )

    for campaign in campaigns:

        print(
            f"#{campaign['id']} | "
            f"{campaign['name']} | "
            f"{campaign['status']} | "
            f"{campaign['created_at']}"
        )


def show_contacts():

    initialize_database()

    repository = ContactRepository(
        get_connection
    )

    contacts = repository.get_all()

    if not contacts:

        print(
            "No contacts found."
        )

        return

    print(
        "\nContacts"
    )

    for contact in contacts:

        print(
            f"#{contact['id']} | "
            f"{contact['name']} | "
            f"{contact['email']} | "
            f"{contact['company']} | "
            f"{contact['role']}"
        )


def show_help():

    print(
        """
AutoMail CLI

Commands:

    python -m app.main create
        Create a new DRAFT campaign from SQLite contacts.

    python -m app.main dry-run <campaign_id>
        Safely test a campaign without sending emails.

    python -m app.main send <campaign_id>
        Actually send the campaign.

    python -m app.main history
        Show campaign history.

    python -m app.main import-contacts
        Import contacts from CSV into SQLite.

    python -m app.main contacts
        Show contacts stored in SQLite.

Examples:

    python -m app.main create

    python -m app.main dry-run 20

    python -m app.main send 20

    python -m app.main history

    python -m app.main import-contacts

    python -m app.main contacts
"""
    )


def main():

    if len(sys.argv) < 2:

        show_help()

        return

    command = sys.argv[1].lower()

    if command == "create":

        create_campaign()

    elif command == "dry-run":

        if len(sys.argv) < 3:

            print(
                "Usage: "
                "python -m app.main "
                "dry-run <campaign_id>"
            )

            return

        campaign_id = int(
            sys.argv[2]
        )

        run_campaign(
            campaign_id=campaign_id,
            dry_run=True
        )

    elif command == "send":

        if len(sys.argv) < 3:

            print(
                "Usage: "
                "python -m app.main "
                "send <campaign_id>"
            )

            return

        campaign_id = int(
            sys.argv[2]
        )

        run_campaign(
            campaign_id=campaign_id,
            dry_run=False
        )

    elif command == "history":

        show_history()

    elif command == "import-contacts":

        import_contacts_command()

    elif command == "contacts":

        show_contacts()

    elif command in (
        "help",
        "-h",
        "--help"
    ):

        show_help()

    else:

        print(
            f"Unknown command: {command}"
        )

        show_help()


if __name__ == "__main__":
    main()