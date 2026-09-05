import time


class CampaignService:

    def __init__(
        self,
        email_sender,
        logger,
        contact_already_sent=None
    ):
        self.email_sender = email_sender
        self.logger = logger
        self.contact_already_sent = contact_already_sent
        self.status = "DRAFT"

    def send_one(
        self,
        contact,
        subject,
        body,
        attachment_path=None,
        recipient_override=None,
        dry_run=False,
        recipient_id=None,
        update_recipient=None
    ):
        contact_email = contact.email
        recipient = recipient_override or contact_email

        # Do not resend a contact that has already
        # successfully been sent in a previous campaign.
        if (
            self.contact_already_sent
            and self.contact_already_sent(contact_email)
        ):
            print(
                f"Skipping {contact_email} — already sent"
            )

            if recipient_id and update_recipient:
                update_recipient(
                    recipient_id=recipient_id,
                    status="SKIPPED"
                )

            return {
                "status": "SKIPPED",
                "recipient": recipient
            }

        # Safe testing mode.
        if dry_run:
            print(
                f"[DRY RUN] Would send email to {recipient}"
            )

            return {
                "status": "DRY_RUN",
                "recipient": recipient
            }

        # Real sending.
        print(
            f"Sending email to {recipient}"
        )

        try:
            result = self.email_sender(
                recipient=recipient,
                subject=subject,
                body=body,
                attachment_path=attachment_path
            )

            message_id = result.get(
                "id",
                ""
            )

            self.logger.log(
                recipient=recipient,
                status="SENT",
                message_id=message_id
            )

            if recipient_id and update_recipient:
                update_recipient(
                    recipient_id=recipient_id,
                    status="SENT",
                    message_id=message_id
                )

            print(
                f"Email sent successfully to {recipient}"
            )

            return {
                "status": "SENT",
                "recipient": recipient,
                "message_id": message_id
            }

        except Exception as error:

            self.logger.log(
                recipient=recipient,
                status="FAILED",
                error=str(error)
            )

            if recipient_id and update_recipient:
                update_recipient(
                    recipient_id=recipient_id,
                    status="FAILED",
                    error=str(error)
                )

            print(
                f"Email failed for {recipient}"
            )

            print(
                f"Error: {error}"
            )

            return {
                "status": "FAILED",
                "recipient": recipient,
                "error": str(error)
            }

    def run_campaign(
        self,
        contacts,
        template_renderer,
        attachment_path=None,
        recipient_override=None,
        dry_run=True,
        delay_seconds=10,
        campaign_id=None,
        mark_started=None,
        mark_completed=None,
        mark_failed=None,
        recipient_ids=None,
        update_recipient=None
    ):
        results = []

        # A dry run does not change campaign state.
        if dry_run:
            self.status = "DRY_RUN"

        else:
            self.status = "RUNNING"

            if campaign_id and mark_started:
                mark_started(campaign_id)

        print(
            f"\nCampaign status: {self.status}"
        )

        try:

            for index, contact in enumerate(contacts):

                print(
                    f"\nProcessing: {contact.name}"
                )

                recipient_id = None

                if recipient_ids:
                    recipient_id = recipient_ids[index]

                try:

                    subject, body = (
                        template_renderer(contact)
                    )

                    result = self.send_one(
                        contact=contact,
                        subject=subject,
                        body=body,
                        attachment_path=attachment_path,
                        recipient_override=recipient_override,
                        dry_run=dry_run,
                        recipient_id=recipient_id,
                        update_recipient=update_recipient
                    )

                    results.append(result)

                except Exception as error:

                    print(
                        f"Failed to process "
                        f"{contact.email}: {error}"
                    )

                    self.logger.log(
                        recipient=contact.email,
                        status="FAILED",
                        error=str(error)
                    )

                    if recipient_id and update_recipient:
                        update_recipient(
                            recipient_id=recipient_id,
                            status="FAILED",
                            error=str(error)
                        )

                    results.append({
                        "status": "FAILED",
                        "recipient": contact.email,
                        "error": str(error)
                    })

                if index < len(contacts) - 1:
                    time.sleep(
                        delay_seconds
                    )

            if not dry_run:

                self.status = "COMPLETED"

                if campaign_id and mark_completed:
                    mark_completed(campaign_id)

            print(
                f"\nCampaign status: {self.status}"
            )

        except Exception:

            self.status = "FAILED"

            if campaign_id and mark_failed:
                mark_failed(campaign_id)

            print(
                f"\nCampaign status: {self.status}"
            )

            raise

        return results