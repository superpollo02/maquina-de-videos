"""Quality Assurance Gates for Pre-Render and Post-Render in EducAI."""

from core.qa.post_render import validate_post_render
from core.qa.pre_render import validate_pre_render

__all__ = ["validate_pre_render", "validate_post_render"]
