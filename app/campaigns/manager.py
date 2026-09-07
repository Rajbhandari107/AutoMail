import os

from app.contacts.manager import Contact
from app.templates.renderer import render_template


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

TEMPLATES_DIR = os.path.join(
    BASE_DIR,
    "templates"
)


class CampaignManager:

    def __init__(self, repository, campaign_service):
        self.repository = repository
        self.campaign_service = campaign_service

    def create_campaign(
        self,
        name,
        contacts,
        template="internship.txt",
        attachment_path="attachments/Resume.pdf",
        delay_seconds=2
    ):
        if not name or not name.strip():
            raise ValueError(
                "Campaign name cannot be empty."
            )

        if not contacts:
            raise ValueError(
                "Cannot create a campaign without contacts."
            )

        if delay_seconds < 0:
            raise ValueError(
                "Delay cannot be negative."
            )

        campaign_id = self.repository.create(
            name=name.strip(),
            template=template,
            attachment_path=attachment_path,
            delay_seconds=delay_seconds
        )

        recipient_ids = []

        for contact in contacts:

            recipient_id = (
                self.repository.add_recipient(
                    campaign_id,
                    contact
                )
            )

            recipient_ids.append(
                recipient_id
            )

        return campaign_id, recipient_ids

    def _build_template_renderer(
        self,
        template_name
    ):
        if not template_name:
            raise ValueError(
                "Campaign does not have a template."
            )

        # Only allow a filename, not arbitrary paths.
        safe_name = os.path.basename(
            template_name
        )

        if safe_name != template_name:
            raise ValueError(
                "Invalid template name."
            )

        template_path = os.path.join(
            TEMPLATES_DIR,
            safe_name
        )

        if not os.path.isfile(
            template_path
        ):
            raise ValueError(
                f"Template not found: {safe_name}"
            )

        with open(
            template_path,
            "r",
            encoding="utf-8"
        ) as file:

            template = file.read()

        def render_for_contact(contact):

            return render_template(
                template,
                contact
            )

        return render_for_contact

    def start_campaign(
        self,
        campaign_id,
        attachment_path=None,
        recipient_override=None,
        dry_run=True,
        delay_seconds=None
    ):
        campaign = self.repository.get_campaign(
            campaign_id
        )

        if campaign is None:
            raise ValueError(
                f"Campaign #{campaign_id} does not exist."
            )

        recipients = (
            self.repository.get_recipients(
                campaign_id
            )
        )

        if not recipients:
            raise ValueError(
                f"Campaign #{campaign_id} has no recipients."
            )

        template_renderer = (
            self._build_template_renderer(
                campaign["template"]
            )
        )

        if attachment_path is None:
            attachment_path = (
                campaign["attachment_path"]
            )

        if delay_seconds is None:
            delay_seconds = (
                campaign["delay_seconds"]
                if campaign["delay_seconds"] is not None
                else 2
            )

        contacts = []

        for recipient in recipients:

            contacts.append(
                Contact(
                    name=recipient["name"],
                    email=recipient["email"],
                    company=recipient["company"],
                    role=recipient["role"]
                )
            )

        recipient_ids = [
            recipient["id"]
            for recipient in recipients
        ]

        return self.campaign_service.run_campaign(
            contacts=contacts,
            template_renderer=template_renderer,
            attachment_path=attachment_path,
            recipient_override=recipient_override,
            dry_run=dry_run,
            delay_seconds=delay_seconds,
            campaign_id=campaign_id,
            mark_started=self.repository.mark_started,
            mark_completed=self.repository.mark_completed,
            mark_failed=self.repository.mark_failed,
            recipient_ids=recipient_ids,
            update_recipient=self.repository.update_recipient
        )