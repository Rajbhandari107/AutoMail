import os

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

from app.database.db import get_connection, initialize_database
from app.contacts.manager import Contact
from app.contacts.repository import ContactRepository
from app.campaigns.repository import CampaignRepository
from app.campaigns.manager import CampaignManager
from app.campaigns.service import CampaignService



# --------------------------------------------------
# Application
# --------------------------------------------------

router = APIRouter()

initialize_database()

app = FastAPI(
    title="AutoMail API",
    description="Backend API for AutoMail",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Repositories
# --------------------------------------------------

campaign_repository = CampaignRepository(
    get_connection
)

contact_repository = ContactRepository(
    get_connection
)


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


# --------------------------------------------------
# Request / Response Models
# --------------------------------------------------


class CampaignCreateRequest(BaseModel):
    name: str
    contact_ids: list[int]
    template: str = "internship.txt"
    attachment_path: str | None = "attachments/Resume.pdf"
    delay_seconds: int = 2


class CampaignCreateResponse(BaseModel):
    campaign_id: int
    name: str
    status: str
    recipient_count: int


class CampaignResponse(BaseModel):
    id: int
    name: str
    status: str
    template: str | None = None
    attachment_path: str | None = None
    delay_seconds: int | None = None
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


class ContactCreateRequest(BaseModel):
    name: str
    email: str
    company: str
    role: str


class ContactUpdateRequest(BaseModel):
    name: str
    email: str
    company: str
    role: str


class ContactResponse(BaseModel):
    id: int
    name: str
    email: str
    company: str
    role: str
    created_at: str


# --------------------------------------------------
# Helpers
# --------------------------------------------------


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
            campaign_repository.was_contact_sent
        )
    )

    return CampaignManager(
        repository=campaign_repository,
        campaign_service=service
    )


# --------------------------------------------------
# Health
# --------------------------------------------------


@router.get("/health")
def health_check():

    return {
        "status": "ok",
        "service": "AutoMail"
    }


# --------------------------------------------------
# Contacts
# --------------------------------------------------


@router.get(
    "/contacts",
    response_model=list[ContactResponse]
)
def get_contacts():

    contacts = contact_repository.get_all()

    return [
        ContactResponse(
            **dict(contact)
        )
        for contact in contacts
    ]


@router.get(
    "/contacts/{contact_id}",
    response_model=ContactResponse
)
def get_contact(
    contact_id: int
):

    contact = contact_repository.get_by_id(
        contact_id
    )

    if contact is None:

        raise HTTPException(
            status_code=404,
            detail="Contact not found."
        )

    return ContactResponse(
        **dict(contact)
    )


@router.post(
    "/contacts",
    response_model=ContactResponse,
    status_code=201
)
def create_contact(
    request: ContactCreateRequest
):

    name = request.name.strip()
    email = request.email.strip().lower()
    company = request.company.strip()
    role = request.role.strip()

    if not name or not email or not company or not role:

        raise HTTPException(
            status_code=400,
            detail="All contact fields are required."
        )

    existing = contact_repository.get_by_email(
        email
    )

    if existing:

        raise HTTPException(
            status_code=409,
            detail=(
                "A contact with this email "
                "already exists."
            )
        )

    contact = Contact(
        name=name,
        email=email,
        company=company,
        role=role
    )

    try:

        contact_id = contact_repository.create(
            contact
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    created_contact = (
        contact_repository.get_by_id(
            contact_id
        )
    )

    return ContactResponse(
        **dict(created_contact)
    )


@router.put(
    "/contacts/{contact_id}",
    response_model=ContactResponse
)
def update_contact(
    contact_id: int,
    request: ContactUpdateRequest
):

    existing = contact_repository.get_by_id(
        contact_id
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Contact not found."
        )

    name = request.name.strip()
    email = request.email.strip().lower()
    company = request.company.strip()
    role = request.role.strip()

    if not name or not email or not company or not role:

        raise HTTPException(
            status_code=400,
            detail="All contact fields are required."
        )

    existing_email = (
        contact_repository.get_by_email(
            email
        )
    )

    if (
        existing_email
        and existing_email["id"] != contact_id
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "A contact with this email "
                "already exists."
            )
        )

    contact = Contact(
        name=name,
        email=email,
        company=company,
        role=role
    )

    try:

        contact_repository.update(
            contact_id,
            contact
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    updated_contact = (
        contact_repository.get_by_id(
            contact_id
        )
    )

    return ContactResponse(
        **dict(updated_contact)
    )


@router.delete(
    "/contacts/{contact_id}"
)
def delete_contact(
    contact_id: int
):

    existing = contact_repository.get_by_id(
        contact_id
    )

    if existing is None:

        raise HTTPException(
            status_code=404,
            detail="Contact not found."
        )

    try:

        contact_repository.delete(
            contact_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    return {
        "message": "Contact deleted successfully.",
        "contact_id": contact_id
    }


# --------------------------------------------------
# Campaigns
# --------------------------------------------------


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

    if not request.contact_ids:

        raise HTTPException(
            status_code=400,
            detail=(
                "At least one contact "
                "must be selected."
            )
        )

    if request.delay_seconds < 0:

        raise HTTPException(
            status_code=400,
            detail="Delay cannot be negative."
        )

    # --------------------------------------------
    # Validate template
    # --------------------------------------------

    template_name = os.path.basename(
        request.template
    )

    if template_name != request.template:

        raise HTTPException(
            status_code=400,
            detail="Invalid template name."
        )

    template_path = os.path.join(
        BASE_DIR,
        "templates",
        template_name
    )

    if not os.path.isfile(template_path):

        raise HTTPException(
            status_code=404,
            detail=(
                f"Template not found: "
                f"{template_name}"
            )
        )

    # --------------------------------------------
    # Load selected contacts
    # --------------------------------------------

    selected_contacts = []

    for contact_id in request.contact_ids:

        contact = contact_repository.get_by_id(
            contact_id
        )

        if contact is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Contact #{contact_id} "
                    f"not found."
                )
            )

        selected_contacts.append(
            Contact(
                name=contact["name"],
                email=contact["email"],
                company=contact["company"],
                role=contact["role"]
            )
        )

    # --------------------------------------------
    # Create campaign
    # --------------------------------------------

    manager = build_campaign_manager()

    try:

        campaign_id, recipient_ids = (
            manager.create_campaign(
                name=name,
                contacts=selected_contacts,
                template=template_name,
                attachment_path=request.attachment_path,
                delay_seconds=request.delay_seconds
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
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

    campaigns = campaign_repository.get_all()

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

    campaign = campaign_repository.get_campaign(
        campaign_id
    )

    if campaign is None:

        raise HTTPException(
            status_code=404,
            detail="Campaign not found."
        )

    recipients = (
        campaign_repository
        .get_recipients(campaign_id)
    )

    counts = (
        campaign_repository
        .get_recipient_counts(campaign_id)
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


# --------------------------------------------------
# Campaign Recipient Management
# --------------------------------------------------


@router.delete(
    "/campaigns/{campaign_id}/recipients/{recipient_id}"
)
def remove_campaign_recipient(
    campaign_id: int,
    recipient_id: int
):

    try:

        campaign_repository.remove_recipient(
            campaign_id,
            recipient_id
        )

    except ValueError as error:

        message = str(error)

        if "does not exist" in message:

            raise HTTPException(
                status_code=404,
                detail=message
            )

        raise HTTPException(
            status_code=400,
            detail=message
        )

    return {
        "message": (
            "Recipient removed from campaign."
        ),
        "campaign_id": campaign_id,
        "recipient_id": recipient_id
    }


# --------------------------------------------------
# Dry Run
# --------------------------------------------------


@router.post(
    "/campaigns/{campaign_id}/dry-run",
    response_model=DryRunResponse
)
def dry_run_campaign(
    campaign_id: int
):

    campaign = campaign_repository.get_campaign(
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

    recipients = (
        campaign_repository
        .get_recipients(campaign_id)
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
            **campaign_repository
            .get_recipient_counts(
                campaign_id
            )
        )
    )


# --------------------------------------------------
# Register router with FastAPI
# --------------------------------------------------

app.include_router(router)