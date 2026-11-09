"""Expand content files with ComplianceAsCode's Jinja2, always from the current files.

ssg.jinja makes one Jinja2 environment the first time a file is expanded and
keeps it for the life of the process. That suits the build, which reads each
file once. The server keeps running while files change, and the environment
holds on to:

- Compiled templates. Its loader treats one as current while the file's mtime is
  unchanged, so a file rewritten with its old mtime kept its old contents.
- The macros in shared/macros, compiled once when the environment is made.
- The variables of the expansion that made it, as globals.

expand_yaml() turns the template cache off, so every expansion reads its file.
It also drops the environment when a macro file, a product.yml or a
product_properties file changes, so ssg.jinja makes a new one.
"""

import importlib
import logging
from typing import Any

from content_agent.core.discovery.content_state import ContentState, take_content_state
from content_agent.core.integration import get_content_repository

logger = logging.getLogger(__name__)

# The files a Jinja2 environment is made from, besides the variables
ENVIRONMENT_INPUTS = (
    "shared/macros/*.jinja",
    "products/*/product.yml",
    "product_properties/*.yml",
)

# ssg.jinja's current environment, and the state of its inputs when it was made
_environment_made_from: tuple[Any, ContentState] | None = None


def expand_yaml(ssg_yaml: Any, path: Any, substitutions: dict[str, Any]) -> Any:
    """Expand a YAML file with ssg_yaml.open_and_expand(), from current files.

    Callers pass the ssg.yaml module they got from get_ssg_modules().
    """
    jinja = _ssg_jinja()
    if jinja is None:
        return ssg_yaml.open_and_expand(str(path), substitutions)

    inputs = _drop_stale_environment(jinja)
    try:
        return ssg_yaml.open_and_expand(str(path), substitutions)
    finally:
        _record_new_environment(jinja, inputs)
        environment = _environment(jinja)
        if environment is not None:
            environment.cache = None


def _ssg_jinja() -> Any:
    try:
        return importlib.import_module("ssg.jinja")
    except ImportError:
        return None


def _environment(jinja: Any) -> Any:
    if hasattr(jinja, "_jinja_env"):
        return jinja._jinja_env
    # Before October 2025, ssg.jinja kept the environment on this function
    return getattr(getattr(jinja, "_get_jinja_environment", None), "env", None)


def _set_environment(jinja: Any, environment: Any) -> None:
    if hasattr(jinja, "_jinja_env"):
        jinja._jinja_env = environment
    elif hasattr(jinja, "_get_jinja_environment"):
        jinja._get_jinja_environment.env = environment


def _drop_stale_environment(jinja: Any) -> ContentState | None:
    """Drop the environment if its inputs changed or it wasn't made here.

    Returns the inputs' state when the next expansion will make a new
    environment, taken before it reads them.
    """
    global _environment_made_from
    environment = _environment(jinja)
    if environment is not None and _environment_made_from is not None:
        made, inputs = _environment_made_from
        if made is environment and inputs.is_current():
            return None
    if environment is not None:
        logger.debug("Dropping the Jinja2 environment, its inputs changed")
        _set_environment(jinja, None)
    _environment_made_from = None
    try:
        return take_content_state(get_content_repository().path, ENVIRONMENT_INPUTS)
    except Exception as e:
        logger.debug(f"Could not record the Jinja2 environment inputs: {e}")
        return None


def _record_new_environment(jinja: Any, inputs: ContentState | None) -> None:
    global _environment_made_from
    environment = _environment(jinja)
    if inputs is not None and environment is not None and _environment_made_from is None:
        _environment_made_from = (environment, inputs)
