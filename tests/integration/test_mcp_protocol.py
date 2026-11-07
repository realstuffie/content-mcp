"""Exercise MCP messages through SDK sessions and the actual stdio entry point."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml
from mcp.shared.memory import create_connected_server_and_client_session

from content_agent.server.mcp_server import ContentAgentServer

RULE = "protocol_test_rule"
TITLE = 'SSH access — accès sécurisé 日本語 "quoted"'


@pytest.fixture
def protocol_repo(initialized_content_repo):
    """A small repository with every readable resource, including build timestamps."""
    from content_agent.core.integration import get_ssg_modules

    root = initialized_content_repo.path
    rule = root / "linux_os" / "guide" / RULE / "rule.yml"
    rule.parent.mkdir(parents=True)
    rule.write_text(
        yaml.safe_dump(
            {
                "documentation_complete": True,
                "title": TITLE,
                "description": "Disable direct root login over SSH.\nPreserve this text.",
                "rationale": "Restrict privileged access.",
                "severity": "medium",
                "template": {"name": "package_installed", "vars": {"pkgname": "openssh"}},
            },
            allow_unicode=True,
        )
    )
    get_ssg_modules().yaml.open_and_expand.side_effect = lambda path, substitutions: yaml.safe_load(
        Path(path).read_text()
    )
    (root / "products" / "rhel9" / "profiles" / "test.profile").write_text(
        f"title: Test profile\ndescription: Protocol fixture\nselections:\n  - {RULE}\n"
    )
    template = root / "shared" / "templates" / "package_installed"
    template.mkdir()
    (template / "template.yml").write_text("supported_languages:\n  - bash\n  - oval\n")
    (root / "controls" / "test.yml").write_text(
        "id: test\ntitle: Test policy\ncontrols:\n"
        f"  - id: R1\n    title: SSH access\n    rules: [{RULE}]\n    status: automated\n"
        "  - id: R2\n    title: Manual review\n    rules: []\n    status: pending\n"
    )
    (root / "policy.md").write_text(f"# Policy\n\n## R1\n\n{TITLE}\n")
    built = root / "build" / "rhel9" / "rules"
    built.mkdir(parents=True)
    (built / f"{RULE}.json").write_text(json.dumps({"title": TITLE, "description": "SSH"}))
    (root / "build" / "ssg-rhel9-ds.xml").write_text(
        '<Benchmark xmlns="http://checklists.nist.gov/xccdf/1.2">'
        '<Profile id="test"/><Rule id="test"/></Benchmark>'
    )
    return root


@pytest.fixture
def mcp_session(protocol_repo):
    server = ContentAgentServer()
    return create_connected_server_and_client_session(
        server.server, read_timeout_seconds=timedelta(seconds=5)
    )


def _json_content(result):
    assert not result.isError
    assert len(result.content) == 1
    assert result.content[0].type == "text"
    text = result.content[0].text
    # Some existing tools put a readable summary before the JSON payload.
    start = re.search(r"^[\[{]", text, re.MULTILINE)
    assert start is not None, text
    return json.loads(text[start.start() :])


@pytest.mark.parametrize(
    "uri",
    [
        "cac://products",
        "cac://products/rhel9",
        "cac://rules",
        f"cac://rules/{RULE}",
        "cac://templates",
        "cac://templates/package_installed",
        "cac://profiles",
        "cac://profiles/rhel9/test",
        "cac://controls",
        "cac://build",
        "cac://build/rhel9",
        f"cac://build/rhel9/rules/{RULE}",
    ],
)
async def test_resource_content_is_json(mcp_session, uri):
    async with mcp_session as mcp_session:
        result = await mcp_session.read_resource(uri)
        assert len(result.contents) == 1
        content = result.contents[0]
        assert str(content.uri) == uri
        data = json.loads(content.text)
        assert data
        if uri == f"cac://rules/{RULE}":
            assert data["title"] == TITLE
            datetime.fromisoformat(data["last_modified"])
        if uri == "cac://build/rhel9":
            assert data["exists"]
            datetime.fromisoformat(data["build_time"])
            assert data["rules_count"] == data["profiles_count"] == 1
