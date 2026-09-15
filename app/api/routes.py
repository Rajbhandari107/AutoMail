import os
import uuid
from datetime import datetime

from app.auth import get_gmail_credentials
from app.email_sender import send_email

from fastapi import (
    APIRouter,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database.db import (
    get_connection,
    initialize_database,
)
from app.contacts.manager import Contact
from app.contacts.repository import ContactRepository
from app.campaigns.repository import CampaignRepository
from app.campaigns.manager import CampaignManager
from app.campaigns.service import CampaignService




# ==================================================
# Application
# ==================================================

router = APIRouter()

initialize_database()

app = FastAPI(
    title="AutoMail API",
    description="Backend API for AutoMail",
    version="1.0.0",
)


# ==================================================
# CORS
# ==================================================

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


# ==================================================
# Paths
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

ATTACHMENTS_DIR = os.path.join(
    BASE_DIR,
    "attachments",
)

TEMPLATES_DIR = os.path.join(
    BASE_DIR,
    "templates",
)

os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


# ==================================================
# Attachment configuration
# ==================================================

MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# ==================================================
# Pydantic models
# ==================================================

class CampaignCreateRequest(BaseModel):
    name: str
    contact_ids: list[int]
    template: str = "internship.txt"
    attachment_path: str | None = None
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


# ==================================================
# Repository helpers
# ==================================================

def get_contact_repository():
    return ContactRepository(
        get_connection
    )


def get_campaign_repository():
    return CampaignRepository(
        get_connection
    )


# ==================================================
# Campaign manager
# ==================================================

def build_campaign_manager():
    campaign_repository = get_campaign_repository()

    credentials = get_gmail_credentials()

    def email_sender(**kwargs):
        return send_email(
            credentials=credentials,
            **kwargs,
        )

    service = CampaignService(
        email_sender=email_sender,
        logger=None,
        contact_already_sent=(
            campaign_repository.was_contact_sent
        ),
    )

    return CampaignManager(
        repository=campaign_repository,
        campaign_service=service,
    )


# ==================================================
# Attachment validation
# ==================================================

def validate_attachment_path(
    attachment_path: str | None,
):
    """
    Validate that an attachment path refers to a file
    stored inside the AutoMail attachments directory.
    """

    if not attachment_path:
        return None

    normalized = attachment_path.replace(
        "\\",
        "/",
    )

    if not normalized.startswith(
        "attachments/"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid attachment path. "
                "Attachments must be stored "
                "inside the attachments directory."
            ),
        )

    filename = normalized[
        len("attachments/"):
    ]

    if not filename or "/" in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid attachment path.",
        )

    absolute_path = os.path.abspath(
        os.path.join(
            ATTACHMENTS_DIR,
            filename,
        )
    )

    attachments_root = os.path.abspath(
        ATTACHMENTS_DIR
    )

    if not absolute_path.startswith(
        attachments_root + os.sep
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid attachment path.",
        )

    if not os.path.isfile(
        absolute_path
    ):
        raise HTTPException(
            status_code=404,
            detail="Attachment file not found.",
        )

    return normalized


# ==================================================
# Health
# ==================================================

@router.get("/health")
def health_check():

    return {
        "status": "ok",
        "service": "AutoMail",
    }


# ==================================================
# Attachment upload
# ==================================================

@router.post("/attachments")
async def upload_attachment(
    file: UploadFile = File(...),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    original_filename = os.path.basename(
        file.filename
    )

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only PDF, DOC, and DOCX files "
                "are allowed."
            ),
        )

    if (
        file.content_type
        and file.content_type
        not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file content type.",
        )

    file_data = await file.read()

    if len(file_data) > MAX_ATTACHMENT_SIZE:
        raise HTTPException(
            status_code=400,
            detail=(
                "File is too large. "
                "Maximum size is 5 MB."
            ),
        )

    unique_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    destination_path = os.path.join(
        ATTACHMENTS_DIR,
        unique_filename,
    )

    try:
        with open(
            destination_path,
            "wb",
        ) as output_file:
            output_file.write(file_data)

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not save attachment: {error}"
            ),
        )

    relative_path = os.path.join(
        "attachments",
        unique_filename,
    ).replace("\\", "/")

    return {
        "filename": original_filename,
        "stored_filename": unique_filename,
        "path": relative_path,
        "size": len(file_data),
        "content_type": file.content_type,
        "uploaded_at": datetime.now().isoformat(
            timespec="seconds"
        ),
    }


# ==================================================
# Contacts
# ==================================================

@router.get(
    "/contacts",
    response_model=list[ContactResponse],
)
def get_contacts():

    repository = get_contact_repository()

    contacts = repository.get_all()

    return [
        ContactResponse(
            **dict(contact)
        )
        for contact in contacts
    ]


@router.get(
    "/contacts/{contact_id}",
    response_model=ContactResponse,
)
def get_contact(
    contact_id: int,
):

    repository = get_contact_repository()

    contact = repository.get_by_id(
        contact_id
    )

    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found.",
        )

    return ContactResponse(
        **dict(contact)
    )


@router.post(
    "/contacts",
    response_model=ContactResponse,
    status_code=201,
)
def create_contact(
    request: ContactCreateRequest,
):

    repository = get_contact_repository()

    name = request.name.strip()
    email = request.email.strip().lower()
    company = request.company.strip()
    role = request.role.strip()

    if not name or not email or not company or not role:
        raise HTTPException(
            status_code=400,
            detail="All contact fields are required.",
        )

    existing = repository.get_by_email(
        email
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "A contact with this email "
                "already exists."
            ),
        )

    contact = Contact(
        name=name,
        email=email,
        company=company,
        role=role,
    )

    try:
        contact_id = repository.create(
            contact
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    created_contact = (
        repository.get_by_id(
            contact_id
        )
    )

    return ContactResponse(
        **dict(created_contact)
    )


@router.put(
    "/contacts/{contact_id}",
    response_model=ContactResponse,
)
def update_contact(
    contact_id: int,
    request: ContactUpdateRequest,
):

    repository = get_contact_repository()

    existing = repository.get_by_id(
        contact_id
    )

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found.",
        )

    name = request.name.strip()
    email = request.email.strip().lower()
    company = request.company.strip()
    role = request.role.strip()

    if not name or not email or not company or not role:
        raise HTTPException(
            status_code=400,
            detail="All contact fields are required.",
        )

    existing_email = (
        repository.get_by_email(
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
            ),
        )

    contact = Contact(
        name=name,
        email=email,
        company=company,
        role=role,
    )

    try:
        repository.update(
            contact_id,
            contact,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    updated_contact = (
        repository.get_by_id(
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
    contact_id: int,
):

    repository = get_contact_repository()

    existing = repository.get_by_id(
        contact_id
    )

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found.",
        )

    try:
        repository.delete(
            contact_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    return {
        "message": (
            "Contact deleted successfully."
        ),
        "contact_id": contact_id,
    }


# ==================================================
# Campaign creation
# ==================================================

@router.post(
    "/campaigns",
    response_model=CampaignCreateResponse,
)
def create_campaign(
    request: CampaignCreateRequest,
):

    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Campaign name cannot be empty.",
        )

    if not request.contact_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least one contact "
                "must be selected."
            ),
        )

    if request.delay_seconds < 0:
        raise HTTPException(
            status_code=400,
            detail="Delay cannot be negative.",
        )

    # ----------------------------------------------
    # Validate template
    # ----------------------------------------------

    template_name = os.path.basename(
        request.template
    )

    if template_name != request.template:
        raise HTTPException(
            status_code=400,
            detail="Invalid template name.",
        )

    template_path = os.path.join(
        TEMPLATES_DIR,
        template_name,
    )

    if not os.path.isfile(
        template_path
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Template not found: "
                f"{template_name}"
            ),
        )

    # ----------------------------------------------
    # Validate attachment
    # ----------------------------------------------

    attachment_path = (
        validate_attachment_path(
            request.attachment_path
        )
    )

    # ----------------------------------------------
    # Load contacts
    # ----------------------------------------------

    contact_repository = (
        get_contact_repository()
    )

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
                ),
            )

        selected_contacts.append(
            Contact(
                name=contact["name"],
                email=contact["email"],
                company=contact["company"],
                role=contact["role"],
            )
        )

    # ----------------------------------------------
    # Create campaign
    # ----------------------------------------------

    manager = build_campaign_manager()

    try:

        campaign_id, recipient_ids = (
            manager.create_campaign(
                name=name,
                contacts=selected_contacts,
                template=template_name,
                attachment_path=attachment_path,
                delay_seconds=request.delay_seconds,
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return CampaignCreateResponse(
        campaign_id=campaign_id,
        name=name,
        status="DRAFT",
        recipient_count=len(
            recipient_ids
        ),
    )


# ==================================================
# Campaign list
# ==================================================

@router.get(
    "/campaigns",
    response_model=list[CampaignResponse],
)
def get_campaigns():

    repository = get_campaign_repository()

    campaigns = repository.get_all()

    return [
        CampaignResponse(
            **dict(campaign)
        )
        for campaign in campaigns
    ]


# ==================================================
# Campaign details
# ==================================================

@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignDetailResponse,
)
def get_campaign(
    campaign_id: int,
):

    repository = get_campaign_repository()

    campaign = repository.get_campaign(
        campaign_id
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found.",
        )

    recipients = (
        repository.get_recipients(
            campaign_id
        )
    )

    counts = (
        repository.get_recipient_counts(
            campaign_id
        )
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
        ),
    )


# ==================================================
# Campaign recipient management
# ==================================================

@router.delete(
    "/campaigns/{campaign_id}/recipients/{recipient_id}"
)
def remove_campaign_recipient(
    campaign_id: int,
    recipient_id: int,
):

    try:

        repository = get_campaign_repository()

        repository.remove_recipient(
            campaign_id,
            recipient_id,
        )

    except ValueError as error:

        message = str(error)

        if "does not exist" in message:
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )

    return {
        "message": (
            "Recipient removed from campaign."
        ),
        "campaign_id": campaign_id,
        "recipient_id": recipient_id,
    }


# ==================================================
# Campaign dry run
# ==================================================

@router.post("/campaigns/{campaign_id}/send")
def send_campaign(campaign_id: int):
    repository = get_campaign_repository()

    # ----------------------------------------
    # 1. Campaign must exist
    # ----------------------------------------

    campaign = repository.get_campaign(campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found.",
        )

    # ----------------------------------------
    # 2. Campaign must still be DRAFT
    # ----------------------------------------

    if campaign["status"] != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Campaign #{campaign_id} cannot be sent "
                f"because its status is "
                f"{campaign['status']}."
            ),
        )

    # ----------------------------------------
    # 3. Campaign must have recipients
    # ----------------------------------------

    recipients = repository.get_recipients(
        campaign_id
    )

    if not recipients:
        raise HTTPException(
            status_code=400,
            detail="Campaign has no recipients.",
        )

    # ----------------------------------------
    # 4. Only PENDING recipients can be sent
    # ----------------------------------------

    pending_recipients = [
        recipient
        for recipient in recipients
        if recipient["status"] == "PENDING"
    ]

    if not pending_recipients:
        raise HTTPException(
            status_code=400,
            detail="Campaign has no pending recipients.",
        )

    # ----------------------------------------
    # 5. Validate template
    # ----------------------------------------

    template_name = campaign["template"]

    if not template_name:
        raise HTTPException(
            status_code=400,
            detail="Campaign does not have a template.",
        )

    safe_template_name = os.path.basename(
        template_name
    )

    if safe_template_name != template_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid template name.",
        )

    template_path = os.path.join(
        TEMPLATES_DIR,
        safe_template_name
    )

    if not os.path.isfile(template_path):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Template not found: "
                f"{safe_template_name}"
            ),
        )

    # ----------------------------------------
    # 6. Validate attachment
    # ----------------------------------------

    attachment_path = campaign["attachment_path"]

    if attachment_path:
        validate_attachment_path(
            attachment_path
        )

    # ----------------------------------------
    # 7. Authenticate Gmail BEFORE
    #    changing campaign to RUNNING
    # ----------------------------------------

    try:
        manager = build_campaign_manager()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gmail authentication failed: {error}"
            ),
        )

    # ----------------------------------------
    # 8. Send all pending recipients
    # ----------------------------------------

    pending_recipient_ids = [
        recipient["id"]
        for recipient in pending_recipients
    ]

    try:
        results = manager.start_campaign(
            campaign_id=campaign_id,
            dry_run=False,
            delay_seconds=campaign["delay_seconds"],
            recipient_ids=pending_recipient_ids,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Campaign send failed: {error}",
        )

    # ----------------------------------------
    # 9. Return execution summary
    # ----------------------------------------

    counts = repository.get_recipient_counts(
        campaign_id
    )

    return {
        "campaign_id": campaign_id,
        "status": repository.get_campaign(
            campaign_id
        )["status"],
        "results": results,
        "counts": counts,
    }



# ==================================================
# Single-recipient test send
# ==================================================

@router.post(
    "/campaigns/{campaign_id}/send-test/{recipient_id}"
)
def send_test_email(
    campaign_id: int,
    recipient_id: int,
):
    repository = get_campaign_repository()

    campaign = repository.get_campaign(campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found."
        )

    if campaign["status"] != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Campaign #{campaign_id} cannot be "
                f"test-sent because its status is "
                f"{campaign['status']}."
            ),
        )

    recipients = repository.get_recipients(
        campaign_id
    )

    recipient = next(
        (
            item
            for item in recipients
            if item["id"] == recipient_id
        ),
        None,
    )

    if recipient is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Recipient #{recipient_id} "
                f"does not belong to campaign "
                f"#{campaign_id}."
            ),
        )

    if recipient["status"] != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Recipient #{recipient_id} cannot "
                f"be test-sent because its status is "
                f"{recipient['status']}."
            ),
        )

    template_name = campaign["template"]

    if not template_name:
        raise HTTPException(
            status_code=400,
            detail="Campaign does not have a template."
        )

    safe_template_name = os.path.basename(
        template_name
    )

    if safe_template_name != template_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid template name."
        )

    template_path = os.path.join(
        TEMPLATES_DIR,
        safe_template_name
    )

    if not os.path.isfile(template_path):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Template not found: "
                f"{safe_template_name}"
            ),
        )

    attachment_path = campaign["attachment_path"]

    if attachment_path:
        validate_attachment_path(
            attachment_path
        )

    manager = build_campaign_manager()

    try:
        results = manager.start_campaign(
            campaign_id=campaign_id,
            dry_run=False,
            delay_seconds=0,
            recipient_ids=[recipient_id],
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Test email failed: {error}"
        )

    result = results[0]

    return {
        "campaign_id": campaign_id,
        "recipient_id": recipient_id,
        "recipient": recipient["email"],
        "status": result["status"],
        "message_id": result.get("message_id"),
    }


@router.post("/campaigns/{campaign_id}/reset")
def reset_campaign(campaign_id: int):
    repository = get_campaign_repository()

    campaign = repository.get_campaign(campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found."
        )

    if campaign["status"] != "RUNNING":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Campaign #{campaign_id} cannot be reset "
                f"because its status is "
                f"{campaign['status']}."
            ),
        )

    try:
        repository.reset_to_draft(campaign_id)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return {
        "campaign_id": campaign_id,
        "status": "DRAFT",
        "message": "Campaign reset to DRAFT."
    }
def dry_run_campaign(
    campaign_id: int,
):

    repository = get_campaign_repository()

    campaign = repository.get_campaign(
        campaign_id
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found.",
        )

    if campaign["status"] != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Campaign #{campaign_id} is "
                f"{campaign['status']}, not DRAFT."
            ),
        )

    recipients = (
        repository.get_recipients(
            campaign_id
        )
    )

    if not recipients:
        raise HTTPException(
            status_code=400,
            detail="Campaign has no recipients.",
        )

    manager = build_campaign_manager()

    try:

        results = manager.start_campaign(
            campaign_id=campaign_id,
            dry_run=True,
            delay_seconds=0,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return DryRunResponse(
        campaign_id=campaign_id,
        mode="DRY_RUN",
        results=[
            DryRunResult(
                status=result["status"],
                recipient=result["recipient"],
            )
            for result in results
        ],
        counts=RecipientCountsResponse(
            **repository.get_recipient_counts(
                campaign_id
            )
        ),
    )


# ==================================================
# Register router
# ==================================================

app.include_router(router)