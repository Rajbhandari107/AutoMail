from app.campaigns.service import CampaignService
from app.contacts.manager import Contact


def make_contact(name, email):
    return Contact(
        name=name,
        email=email,
        company="Test Company",
        role="Test Role"
    )


def make_renderer(contact):
    return (
        "Test Subject",
        f"Hello {contact.name}"
    )


def test_all_recipients_succeed():
    sent_recipients = []

    def fake_sender(**kwargs):
        sent_recipients.append(kwargs["recipient"])
        return {"id": "message-123"}

    service = CampaignService(
        email_sender=fake_sender,
        logger=None
    )

    completed = []
    failed = []

    contacts = [
        make_contact("John", "john@example.com"),
        make_contact("Sarah", "sarah@example.com")
    ]

    results = service.run_campaign(
        contacts=contacts,
        template_renderer=make_renderer,
        dry_run=False,
        delay_seconds=0,
        mark_completed=lambda campaign_id: completed.append(
            campaign_id
        ),
        mark_failed=lambda campaign_id: failed.append(
            campaign_id
        ),
        campaign_id=1
    )

    assert len(results) == 2
    assert all(
        result["status"] == "SENT"
        for result in results
    )

    assert service.status == "COMPLETED"
    assert completed == [1]
    assert failed == []

    assert sent_recipients == [
        "john@example.com",
        "sarah@example.com"
    ]


def test_one_recipient_fails_campaign_fails():
    def fake_sender(**kwargs):
        if kwargs["recipient"] == "sarah@example.com":
            raise RuntimeError("Simulated email failure")

        return {"id": "message-123"}

    service = CampaignService(
        email_sender=fake_sender,
        logger=None
    )

    completed = []
    failed = []

    contacts = [
        make_contact("John", "john@example.com"),
        make_contact("Sarah", "sarah@example.com")
    ]

    results = service.run_campaign(
        contacts=contacts,
        template_renderer=make_renderer,
        dry_run=False,
        delay_seconds=0,
        mark_completed=lambda campaign_id: completed.append(
            campaign_id
        ),
        mark_failed=lambda campaign_id: failed.append(
            campaign_id
        ),
        campaign_id=2
    )

    assert results[0]["status"] == "SENT"
    assert results[1]["status"] == "FAILED"

    assert service.status == "FAILED"
    assert completed == []
    assert failed == [2]


def test_all_recipients_fail_campaign_fails():
    def fake_sender(**kwargs):
        raise RuntimeError("Simulated email failure")

    service = CampaignService(
        email_sender=fake_sender,
        logger=None
    )

    completed = []
    failed = []

    contacts = [
        make_contact("John", "john@example.com"),
        make_contact("Sarah", "sarah@example.com")
    ]

    results = service.run_campaign(
        contacts=contacts,
        template_renderer=make_renderer,
        dry_run=False,
        delay_seconds=0,
        mark_completed=lambda campaign_id: completed.append(
            campaign_id
        ),
        mark_failed=lambda campaign_id: failed.append(
            campaign_id
        ),
        campaign_id=3
    )

    assert all(
        result["status"] == "FAILED"
        for result in results
    )

    assert service.status == "FAILED"
    assert completed == []
    assert failed == [3]


def test_dry_run_does_not_change_campaign_status():
    def fake_sender(**kwargs):
        raise AssertionError(
            "Fake sender should not be called during dry run"
        )

    service = CampaignService(
        email_sender=fake_sender,
        logger=None
    )

    completed = []
    failed = []

    contacts = [
        make_contact("John", "john@example.com"),
        make_contact("Sarah", "sarah@example.com")
    ]

    results = service.run_campaign(
        contacts=contacts,
        template_renderer=make_renderer,
        dry_run=True,
        delay_seconds=0,
        mark_completed=lambda campaign_id: completed.append(
            campaign_id
        ),
        mark_failed=lambda campaign_id: failed.append(
            campaign_id
        ),
        campaign_id=4
    )

    assert all(
        result["status"] == "DRY_RUN"
        for result in results
    )

    assert service.status == "DRY_RUN"
    assert completed == []
    assert failed == []


def test_already_sent_contact_is_skipped():
    def fake_sender(**kwargs):
        raise AssertionError(
            "Sender should not be called for an already-sent contact"
        )

    service = CampaignService(
        email_sender=fake_sender,
        logger=None,
        contact_already_sent=lambda email: True
    )

    contacts = [
        make_contact("John", "john@example.com")
    ]

    results = service.run_campaign(
        contacts=contacts,
        template_renderer=make_renderer,
        dry_run=False,
        delay_seconds=0
    )

    assert len(results) == 1
    assert results[0]["status"] == "SKIPPED"
    assert results[0]["recipient"] == "john@example.com"