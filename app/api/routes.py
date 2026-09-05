from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.db import get_connection, initialize_database
from app.campaigns.repository import CampaignRepository
from app.campaigns.manager import CampaignManager
from app.campaigns.service import CampaignService
from app.contacts.manager import load_contacts
from app.templates.renderer import render_template


router = APIRouter()

initialize_database()

repository = CampaignRepository(
    get_connection
)


class CampaignCreateRequest(BaseModel):
    name: str


def get_contacts():
    return load_contacts(
        "data/contacts.csv"
    )


def get_template_renderer():
    with open(
        "templates/internship.txt",
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


def build_campaign_manager():
    def email_sender(**kwargs):
        raise RuntimeError(
            "Real email sending is not available "
            "through this API yet."
        )

    service = CampaignService(
        email_sender=email_sender,
        logger=None,
        contact_already_sent=(
            repository.was_contact_sent
        )
    )

    return CampaignManager(
        repository=repository,
        campaign_service=service
    )


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "AutoMail"
    }


@router.post("/campaigns")
def create_campaign(
    request: CampaignCreateRequest
):
    contacts = get_contacts()

    if not contacts:
        raise HTTPException(
            status_code=400,
            detail="No contacts available."
        )

    manager = build_campaign_manager()

    campaign_id, recipient_ids = (
        manager.create_campaign(
            name=request.name,
            contacts=contacts
        )
    )

    return {
        "campaign_id": campaign_id,
        "name": request.name,
        "status": "DRAFT",
        "recipient_count": len(recipient_ids)
    }


@router.get("/campaigns")
def get_campaigns():
    campaigns = repository.get_all()

    return [
        dict(campaign)
        for campaign in campaigns
    ]


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int):
    campaign = repository.get_campaign(
        campaign_id
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found."
        )

    recipients = repository.get_recipients(
        campaign_id
    )

    counts = repository.get_recipient_counts(
        campaign_id
    )

    return {
        "campaign": dict(campaign),
        "recipients": [
            dict(recipient)
            for recipient in recipients
        ],
        "counts": counts
    }


@router.post("/campaigns/{campaign_id}/dry-run")
def dry_run_campaign(
    campaign_id: int
):
    campaign = repository.get_campaign(
        campaign_id
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found."
        )

    recipients = repository.get_recipients(
        campaign_id
    )

    if not recipients:
        raise HTTPException(
            status_code=400,
            detail="Campaign has no recipients."
        )

    contacts = get_contacts()

    recipient_ids = [
        recipient["id"]
        for recipient in recipients
    ]

    manager = build_campaign_manager()

    results = manager.start_campaign(
        campaign_id=campaign_id,
        contacts=contacts,
        recipient_ids=recipient_ids,
        template_renderer=get_template_renderer(),
        dry_run=True,
        delay_seconds=0
    )

    return {
        "campaign_id": campaign_id,
        "mode": "DRY_RUN",
        "results": results,
        "counts": repository.get_recipient_counts(
            campaign_id
        )
    }