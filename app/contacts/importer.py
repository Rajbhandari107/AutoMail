from app.contacts.manager import load_contacts


def import_contacts(
    file_path,
    repository
):

    contacts = load_contacts(
        file_path
    )

    imported = 0
    skipped = 0

    for contact in contacts:

        existing = repository.get_by_email(
            contact.email
        )

        if existing:

            skipped += 1

            continue

        repository.create(
            contact
        )

        imported += 1

    return {
        "imported": imported,
        "skipped": skipped,
        "total": len(contacts)
    }