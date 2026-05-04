"""Jinja2 template rendering for notification emails."""

import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

_template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

_env = Environment(
    loader=FileSystemLoader(_template_dir),
    autoescape=select_autoescape(["html"]),
)


def render_template(template_name: str, **kwargs: object) -> str:
    """Render a Jinja2 HTML template by name with the given context variables."""
    return _env.get_template(template_name).render(**kwargs)
