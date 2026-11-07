"""Run mock and real repository fixtures in the order that poisoned SSG imports."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path


def test_mock_repository_restores_ssg_imports(tmp_path):
    project = Path(__file__).resolve().parents[2]
    real = tmp_path / "real-content"
    for name in ("ssg", "linux_os", "products"):
        (real / name).mkdir(parents=True)
    (real / "ssg" / "__init__.py").write_text('SOURCE = "regular SSG package"\n')
    for name in (
        "build_yaml",
        "products",
        "rules",
        "templates",
        "profiles",
        "controls",
        "yaml",
        "constants",
    ):
        (real / "ssg" / f"{name}.py").write_text('SOURCE = "regular SSG module"\n')

    suite = tmp_path / "suite"
    suite.mkdir()
    (suite / "pytest.ini").write_text("[pytest]\nasyncio_default_fixture_loop_scope = function\n")
    (suite / "conftest.py").write_text(
        "from tests.conftest import (\n"
        "    initialized_content_repo, mock_content_repo, real_content_repo, temp_dir,\n"
        ")\n"
    )
    cases = {
        "test_unit_first.py": """
            import importlib
            from pathlib import Path

            def test_namespace_import(initialized_content_repo):
                import ssg
                assert ssg.__file__ is None
                assert list(ssg.__path__) == [str(initialized_content_repo.path / "ssg")]
                Path(__file__).with_name("mock-path.txt").write_text(str(initialized_content_repo.path))
                (initialized_content_repo.path / "ssg" / "transient.py").write_text("value = 1\\n")
                importlib.invalidate_caches()
                import ssg.transient
                assert ssg.transient.value == 1
        """,
        "test_integration_next.py": """
            import sys
            from pathlib import Path

            def test_real_package_import(real_content_repo):
                import ssg
                import ssg.products
                assert ssg.SOURCE == "regular SSG package"
                assert ssg.products.SOURCE == "regular SSG module"
                assert "ssg.transient" not in sys.modules
                mock_path = Path(__file__).with_name("mock-path.txt").read_text()
                assert mock_path not in sys.path
        """,
        "test_unit_after_real.py": """
            import sys
            from types import ModuleType

            def test_replace_cached_submodule(initialized_content_repo, monkeypatch):
                import ssg
                import ssg.products
                assert ssg.SOURCE == "regular SSG package"
                ssg.expected_products = ssg.products
                ssg.expected_path = [p for p in sys.path if p != str(initialized_content_repo.path)]
                monkeypatch.syspath_prepend(str(initialized_content_repo.path / "extra"))
                sys.modules["ssg.products"] = ModuleType("ssg.products")
                sys.modules["ssg.transient"] = ModuleType("ssg.transient")
        """,
        "test_verify_teardown.py": """
            import sys

            def test_existing_package_restored():
                import ssg
                import ssg.products
                assert ssg.SOURCE == "regular SSG package"
                assert sys.modules["ssg.products"] is ssg.expected_products
                assert "ssg.transient" not in sys.modules
                assert sys.path == ssg.expected_path
        """,
    }
    for name, content in cases.items():
        (suite / name).write_text(textwrap.dedent(content))

    env = dict(os.environ)
    env.update(
        {
            "PYTHONPATH": str(project),
            "CONTENT_REPO": str(real),
            "CONTENT_AGENT_CONTENT__MANAGED_PATH": str(tmp_path / "managed"),
            "CONTENT_AGENT_BUILD__BUILD_DIR": str(tmp_path / "builds"),
            "CONTENT_AGENT_JOBS__DATABASE": str(tmp_path / "jobs.db"),
            "CONTENT_AGENT_LOGGING__FILE": str(tmp_path / "server.log"),
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(suite / "pytest.ini"),
            "--confcutdir",
            str(suite),
            *(str(suite / name) for name in cases),
            "-q",
        ],
        cwd=suite,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "4 passed" in result.stdout
