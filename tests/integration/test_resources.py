"""Integration tests for MCP resource handlers."""

import json

import pytest

from content_agent.server.handlers.resources import handle_resource_read, list_resources
from tests.conftest import requires_content_repo


class TestResourceListing:
    """Test resource listing."""

    def test_list_resources(self):
        """Test listing available resources."""
        resources = list_resources()

        assert isinstance(resources, list)
        assert len(resources) > 0

        # Check structure
        for resource in resources:
            assert "uri" in resource
            assert "name" in resource
            assert "description" in resource
            assert "mimeType" in resource

        # Check specific resources exist
        uris = [r["uri"] for r in resources]
        assert "cac://products" in uris
        assert "cac://rules" in uris
        assert "cac://templates" in uris


@requires_content_repo
class TestResourceRead:
    """Test resource reading (requires real content)."""

    @pytest.mark.asyncio
    async def test_read_products_resource(self, real_content_repo):
        """Test reading products resource."""
        content = await handle_resource_read("cac://products")

        # Should be valid JSON
        data = json.loads(content)
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_read_specific_product(self, real_content_repo):
        """Test reading specific product resource."""
        try:
            content = await handle_resource_read("cac://products/rhel9")
            data = json.loads(content)

            assert "product_id" in data
            assert data["product_id"] == "rhel9"
        except ValueError:
            # Product might not exist in test environment
            pytest.skip("Product rhel9 not available")

    @pytest.mark.asyncio
    async def test_read_rules_resource(self, real_content_repo):
        """Test reading rules resource."""
        content = await handle_resource_read("cac://rules")

        # Should be valid JSON array
        data = json.loads(content)
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_read_templates_resource(self, real_content_repo):
        """Test reading templates resource."""
        content = await handle_resource_read("cac://templates")

        # Should be valid JSON array
        data = json.loads(content)
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_invalid_uri_scheme(self, real_content_repo):
        """Test reading resource with invalid URI scheme."""
        with pytest.raises(ValueError, match="Invalid URI scheme"):
            await handle_resource_read("http://products")

    @pytest.mark.asyncio
    async def test_invalid_resource_type(self, real_content_repo):
        """Test reading unknown resource type."""
        with pytest.raises(ValueError, match="Unknown resource type"):
            await handle_resource_read("cac://unknown")

    @pytest.mark.asyncio
    async def test_invalid_resource_path(self, real_content_repo):
        """Test reading resource with invalid path."""
        with pytest.raises(ValueError):
            await handle_resource_read("cac://products/invalid/extra/path")

    @pytest.mark.asyncio
    async def test_nonexistent_product(self, real_content_repo):
        """Test reading non-existent product."""
        with pytest.raises(ValueError, match="not found"):
            await handle_resource_read("cac://products/nonexistent_product_12345")

    @pytest.mark.asyncio
    async def test_nonexistent_rule(self, real_content_repo):
        """Test reading non-existent rule."""
        with pytest.raises(ValueError, match="not found"):
            await handle_resource_read("cac://rules/nonexistent_rule_12345")


class TestResourceURIParsing:
    """Test URI parsing logic."""

    @pytest.mark.asyncio
    async def test_uri_with_trailing_slash(self, initialized_content_repo):
        """Test URI with trailing slash."""
        # Should handle trailing slash gracefully
        try:
            await handle_resource_read("cac://products/")
        except ValueError as e:
            # May fail but shouldn't crash
            assert "not found" in str(e).lower() or "invalid" in str(e).lower()

    @pytest.mark.asyncio
    async def test_empty_path(self, initialized_content_repo):
        """Test URI with empty path."""
        with pytest.raises(ValueError, match="Invalid resource path"):
            await handle_resource_read("cac://")
