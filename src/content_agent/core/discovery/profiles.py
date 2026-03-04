"""Profile discovery implementation."""

import logging
from pathlib import Path

from content_agent.core.integration import get_content_repository
from content_agent.models import DiscoveryResult, ProfileDetails, ProfileSummary

logger = logging.getLogger(__name__)


class ProfileDiscovery:
    """Profile discovery and information retrieval."""

    def __init__(self) -> None:
        """Initialize profile discovery."""
        self.content_repo = get_content_repository()

    def list_profiles(self, product: str | None = None) -> DiscoveryResult[ProfileSummary]:
        """List profiles for a product or all products.

        Args:
            product: Optional product filter

        Returns:
            DiscoveryResult with ProfileSummary items and any parse errors
        """
        logger.debug(f"Listing profiles for product: {product or 'all'}")
        result: DiscoveryResult[ProfileSummary] = DiscoveryResult()

        products_dir = self.content_repo.path / "products"
        if not products_dir.exists():
            return result

        # Determine which products to search
        if product:
            product_dirs = [products_dir / product]
        else:
            product_dirs = [d for d in products_dir.iterdir() if d.is_dir()]

        for product_dir in product_dirs:
            if not product_dir.exists():
                continue

            product_id = product_dir.name
            profiles_dir = product_dir / "profiles"

            if not profiles_dir.exists():
                continue

            for profile_file in profiles_dir.glob("*.profile"):
                try:
                    summary = self._load_profile_summary(
                        profile_file.stem, product_id, profile_file
                    )
                    result.items.append(summary)
                except Exception as e:
                    error_msg = f"Failed to load profile {profile_file.stem}: {e}"
                    logger.warning(error_msg)
                    result.errors.append(error_msg)

        result.items.sort(key=lambda p: (p.product, p.profile_id))
        logger.info(f"Found {len(result.items)} profiles")
        return result

    def get_profile_details(self, profile_id: str, product: str) -> ProfileDetails | None:
        """Get detailed information about a profile.

        Args:
            profile_id: Profile identifier
            product: Product identifier

        Returns:
            ProfileDetails or None if not found
        """
        logger.debug(f"Getting details for profile: {profile_id} in {product}")

        profile_path = (
            self.content_repo.path / "products" / product / "profiles" / f"{profile_id}.profile"
        )

        if not profile_path.exists():
            logger.warning(f"Profile not found: {profile_id} in {product}")
            return None

        with open(profile_path) as f:
            content = f.read()

        # Parse profile format (YAML-like but custom)
        data = self._parse_profile(content)

        # Get selections (rule IDs)
        selections = data.get("selections", [])

        # Get variables
        variables = data.get("variables", {})

        # Determine control file
        control_file = None
        if "controls" in data:
            control_file = data["controls"]

        details = ProfileDetails(
            profile_id=profile_id,
            title=data.get("title", profile_id),
            description=data.get("description", ""),
            product=product,
            extends=data.get("extends"),
            selections=selections,
            variables=variables,
            file_path=str(profile_path.relative_to(self.content_repo.path)),
            rule_count=len(selections),
            control_file=control_file,
        )

        logger.debug(f"Loaded details for profile {profile_id}")
        return details

    def _load_profile_summary(
        self, profile_id: str, product: str, profile_path: Path
    ) -> ProfileSummary:
        """Load profile summary.

        Args:
            profile_id: Profile identifier
            product: Product identifier
            profile_path: Path to profile file

        Returns:
            ProfileSummary

        Raises:
            Exception: If parsing or model construction fails
        """
        with open(profile_path) as f:
            content = f.read()

        data = self._parse_profile(content)
        selections = data.get("selections", [])

        return ProfileSummary(
            profile_id=profile_id,
            title=data.get("title", profile_id),
            description=(data.get("description") or "")[:200],  # Truncate
            product=product,
            rule_count=len(selections),
        )

    def _parse_profile(self, content: str) -> dict:
        """Parse profile file content.

        Profile files have a custom YAML-like format with special syntax.

        Args:
            content: Profile file content

        Returns:
            Parsed data dict
        """
        data = {
            "title": None,
            "description": None,
            "extends": None,
            "selections": [],
            "variables": {},
            "controls": None,
        }

        lines = content.split("\n")
        current_section = None
        description_lines = []

        for line in lines:
            line = line.rstrip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse key-value pairs
            if line.startswith("documentation_complete:"):
                continue
            elif line.startswith("title:"):
                data["title"] = line.split(":", 1)[1].strip().strip("'\"")
            elif line.startswith("description:"):
                desc = line.split(":", 1)[1].strip()
                if desc:
                    description_lines.append(desc.strip("'\""))
                current_section = "description"
            elif line.startswith("extends:"):
                data["extends"] = line.split(":", 1)[1].strip()
            elif line.startswith("selections:"):
                current_section = "selections"
            elif line.startswith("controls:"):
                data["controls"] = line.split(":", 1)[1].strip()
            elif current_section == "description":
                # Multi-line description
                if line.startswith(" ") or line.startswith("\t"):
                    description_lines.append(line.strip())
                else:
                    current_section = None
            elif current_section == "selections":
                # Selection line (starts with -)
                if line.strip().startswith("-"):
                    selection = line.strip()[1:].strip()
                    # Handle !unselect
                    if selection.startswith("!unselect"):
                        continue
                    data["selections"].append(selection)
                else:
                    current_section = None

        # Join description lines
        if description_lines:
            data["description"] = " ".join(description_lines)

        return data


def list_profiles(product: str | None = None) -> DiscoveryResult[ProfileSummary]:
    """List profiles for a product or all products.

    Args:
        product: Optional product filter

    Returns:
        DiscoveryResult with ProfileSummary items and any parse errors
    """
    discovery = ProfileDiscovery()
    return discovery.list_profiles(product)


def get_profile_details(profile_id: str, product: str) -> ProfileDetails | None:
    """Get detailed information about a profile.

    Args:
        profile_id: Profile identifier
        product: Product identifier

    Returns:
        ProfileDetails or None if not found
    """
    discovery = ProfileDiscovery()
    return discovery.get_profile_details(profile_id, product)
