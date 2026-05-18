import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from premailer import transform

from src import Newsletter

logger = logging.getLogger(__name__)

# Project root is two levels above this file (src/render_email.py -> src/ -> project root)
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def render(newsletter: Newsletter) -> str:
    """Render the newsletter HTML email using Jinja2 and inline CSS via premailer."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template("newsletter.html.j2")
    html = template.render(newsletter=newsletter)
    try:
        html = transform(html)
    except Exception as exc:
        logger.warning("premailer transform failed, using raw HTML: %s", exc)
    return html
