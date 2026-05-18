import logging

import resend

logger = logging.getLogger(__name__)


def send(
    html: str,
    subject: str,
    api_key: str,
    to: str,
    from_email: str,
    from_name: str,
) -> bool:
    """Send an HTML email via the Resend API. Returns True on success, False on failure."""
    resend.api_key = api_key
    params: resend.Emails.SendParams = {
        "from": f"{from_name} <{from_email}>",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    try:
        response = resend.Emails.send(params)
        logger.info("Email sent successfully, id=%s", getattr(response, "id", response))
        return True
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)
        return False
