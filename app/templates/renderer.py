import re


def render_template(template, contact):
    def replace_variable(match):
        variable = match.group(1).strip()

        if not hasattr(contact, variable):
            raise ValueError(
                f"Unknown template variable: {{{{{variable}}}}}"
            )

        return str(getattr(contact, variable))

    rendered = re.sub(
        r"\{\{(.*?)\}\}",
        replace_variable,
        template
    )

    lines = rendered.splitlines()

    if not lines or not lines[0].startswith("Subject:"):
        raise ValueError("Template must start with 'Subject:'")

    subject = lines[0].replace("Subject:", "", 1).strip()

    body = "\n".join(lines[1:]).strip()

    return subject, body