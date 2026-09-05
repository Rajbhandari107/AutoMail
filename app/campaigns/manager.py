class CampaignManager:

    def __init__(self, repository, campaign_service):
        self.repository = repository
        self.campaign_service = campaign_service

    def create_campaign(self, name, contacts):
        campaign_id = self.repository.create(name)

        recipient_ids = []

        for contact in contacts:
            recipient_id = self.repository.add_recipient(
                campaign_id,
                contact
            )

            recipient_ids.append(recipient_id)

        return campaign_id, recipient_ids

    def start_campaign(
        self,
        campaign_id,
        contacts,
        recipient_ids,
        template_renderer,
        attachment_path=None,
        recipient_override=None,
        dry_run=True,
        delay_seconds=10
    ):
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
    