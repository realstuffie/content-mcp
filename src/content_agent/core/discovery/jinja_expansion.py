"""Expand content files with ComplianceAsCode's Jinja2, from current files and per product.

ssg.jinja makes one Jinja2 environment the first time a file is expanded and
keeps it for the life of the process. That suits the build, which reads each
file once for one product. The server keeps running while files change, and
expands files for many products. The environment holds on to:

- Compiled templates. Its loader treats one as current while the file's mtime is
  unchanged, so a file rewritten with its old mtime kept its old contents.
- The macros in shared/macros, compiled once when the environment is made.
- The variables of the expansion that made it, as globals. Macros read their
  variables from there, so after a rhel9 expansion, an ubuntu2204 rule's
  describe_package_install() still said `dnf install`.

expand_yaml() keeps one environment for each set of variables and puts it in
ssg.jinja before expanding. It turns each environment's template cache off, so
every expansion reads its file. When a macro file, a product.yml or a
product_properties file changes, it drops all of them.

Making an environment compiles the macros, about 0.5 s. A bytecode cache in a
temporary directory, which ssg.jinja supports, cuts that to about 13 ms for
every environment after the first. The bytecode cache checks a hash of each
template's source, so it never serves old contents.
"""

import atexit
import importlib
import logging
import shutil
import tempfile
from collections import OrderedDict
from types import ModuleType
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

# Environments kept at once, about 2 MB each. One is made again in about 13 ms.
MAX_ENVIRONMENTS = 16

# Environments by their variables, least recently used first
_environments: "OrderedDict[str, Any]" = OrderedDict()
# The state of ENVIRONMENT_INPUTS when the kept environments were made
_inputs: ContentState | None = None
_bytecode_dir: str | None = None


def expand_yaml(ssg_yaml: Any, path: Any, substitutions: dict[str, Any]) -> Any:
    """Expand a YAML file with ssg_yaml.open_and_expand(), from current files.

    Callers pass the ssg.yaml module they got from get_ssg_modules(). The
    caller's `substitutions` dict is left unchanged.
    """
    jinja = _ssg_jinja(ssg_yaml)
    if jinja is None:
        return ssg_yaml.open_and_expand(str(path), substitutions)

    _drop_stale_environments()
    key = _variables_key(substitutions)
    environment = _environments.get(key)
    if environment is not None:
        _environments.move_to_end(key)
    _set_environment(jinja, environment)
    variables = dict(substitutions)
    variables.update(jinja2_cache_enabled="true", jinja2_cache_dir=_bytecode_cache_dir())
    try:
        return ssg_yaml.open_and_expand(str(path), variables)
    finally:
        made = _environment(jinja)
        if made is not None:
            made.cache = None
            _keep(key, made)


def _ssg_jinja(ssg_yaml: Any) -> Any:
    """Return the ssg.jinja module next to `ssg_yaml`, or None for a stand-in."""
    if not isinstance(ssg_yaml, ModuleType):
        return None
    package = ssg_yaml.__name__.rpartition(".")[0]
    try:
        return importlib.import_module(f"{package}.jinja")
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


def _variables_key(substitutions: dict[str, Any]) -> str:
    """Return a key that is equal for equal variables."""
    return repr(sorted(substitutions.items(), key=lambda item: str(item[0])))


def _keep(key: str, environment: Any) -> None:
    _environments[key] = environment
    _environments.move_to_end(key)
    while len(_environments) > MAX_ENVIRONMENTS:
        _environments.popitem(last=False)


def _drop_stale_environments() -> None:
    """Drop every kept environment if a macro or product file changed."""
    global _inputs
    if _inputs is not None and _inputs.is_current():
        return
    if _environments:
        logger.debug("Dropping the Jinja2 environments, their inputs changed")
    _environments.clear()
    # Taken before the next environment reads the files
    try:
        _inputs = take_content_state(get_content_repository().path, ENVIRONMENT_INPUTS)
    except Exception as e:
        logger.debug(f"Could not record the Jinja2 environment inputs: {e}")
        _inputs = None


def _bytecode_cache_dir() -> str:
    global _bytecode_dir
    if _bytecode_dir is None:
        _bytecode_dir = tempfile.mkdtemp(prefix="content-mcp-jinja-")
        atexit.register(shutil.rmtree, _bytecode_dir, ignore_errors=True)
    return _bytecode_dir
