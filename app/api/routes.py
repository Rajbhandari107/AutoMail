import os

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


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
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


class CampaignCreateRequest(BaseModel):
    name: str


class CampaignCreateResponse(BaseModel):
    campaign_id: int
    name: str
    status: str
    recipient_count: int


class CampaignResponse(BaseModel):
    id: int
    name: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None


class RecipientResponse(BaseModel):
    id: int
    campaign_id: int
    name: str
    email: str
    company: str
    role: str
    status: str
    message_id: str | None = None
    error: str | None = None
    sent_at: str | None = None


class RecipientCountsResponse(BaseModel):
    TOTAL: int
    PENDING: int
    SENT: int
    FAILED: int
    SKIPPED: int


class CampaignDetailResponse(BaseModel):
    campaign: CampaignResponse
    recipients: list[RecipientResponse]
    counts: RecipientCountsResponse


class DryRunResult(BaseModel):
    status: str
    recipient: str


class DryRunResponse(BaseModel):
    campaign_id: int
    mode: str
    results: list[DryRunResult]
    counts: RecipientCountsResponse


def get_contacts():

    return load_contacts(
        CONTACTS_PATH
    )


def get_template_renderer():

    with open(
        TEMPLATE_PATH,
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


@router.post(
    "/campaigns",
    response_model=CampaignCreateResponse
)
def create_campaign(
    request: CampaignCreateRequest
):

    name = request.name.strip()

    if not name:

        raise HTTPException(
            status_code=400,
            detail="Campaign name cannot be empty."
        )

    contacts = get_contacts()

    if not contacts:

        raise HTTPException(
            status_code=400,
            detail="No contacts available."
        )

    manager = build_campaign_manager()

    campaign_id, recipient_ids = (
        manager.create_campaign(
            name=name,
            contacts=contacts
        )
    )

    return CampaignCreateResponse(
        campaign_id=campaign_id,
        name=name,
        status="DRAFT",
        recipient_count=len(recipient_ids)
    )


@router.get(
    "/campaigns",
    response_model=list[CampaignResponse]
)
def get_campaigns():

    campaigns = repository.get_all()

    return [
        CampaignResponse(
            **dict(campaign)
        )
        for campaign in campaigns
    ]


@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignDetailResponse
)
def get_campaign(
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

    counts = repository.get_recipient_counts(
        campaign_id
    )

    return CampaignDetailResponse(
        campaign=CampaignResponse(
            **dict(campaign)
        ),
        recipients=[
            RecipientResponse(
                **dict(recipient)
            )
            for recipient in recipients
        ],
        counts=RecipientCountsResponse(
            **counts
        )
    )


@router.post(
    "/campaigns/{campaign_id}/dry-run",
    response_model=DryRunResponse
)
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

    if campaign["status"] != "DRAFT":

        raise HTTPException(
            status_code=400,
            detail=(
                f"Campaign #{campaign_id} is "
                f"{campaign['status']}, not DRAFT."
            )
        )

    recipients = repository.get_recipients(
        campaign_id
    )

    if not recipients:

        raise HTTPException(
            status_code=400,
            detail="Campaign has no recipients."
        )

    manager = build_campaign_manager()

    try:

        results = manager.start_campaign(
            campaign_id=campaign_id,
            template_renderer=get_template_renderer(),
            dry_run=True,
            delay_seconds=0
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return DryRunResponse(
        campaign_id=campaign_id,
        mode="DRY_RUN",
        results=[
            DryRunResult(
                status=result["status"],
                recipient=result["recipient"]
            )
            for result in results
        ],
        counts=RecipientCountsResponse(
            **repository.get_recipient_counts(
                campaign_id
            )
        )
    )