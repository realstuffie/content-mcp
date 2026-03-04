#!/usr/bin/env python3
"""Before and After: Unified Rule Discovery

This example shows the difference between the old way (multiple calls)
and the new way (single unified call) for getting rule information.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def example_old_way():
    """The OLD way: Multiple separate calls."""
    print("=" * 70)
    print("OLD WAY: Multiple Separate Calls")
    print("=" * 70)

    from content_agent.config import initialize_settings
    from content_agent.core.integration import initialize_content_repository
    from content_agent.core import discovery

    # Initialize
    initialize_settings()
    initialize_content_repository(Path.home() / "workspace" / "content")

    rule_id = "accounts_password_pam_dcredit"

    print(f"\nStep 1: Get source rule details...")
    rule = discovery.get_rule_details(rule_id, include_rendered=False)
    print(f"  ✓ Rule: {rule.title}")
    print(f"  ✓ Severity: {rule.severity}")
    print(f"  ✓ Products: {rule.products}")

    print(f"\nStep 2: Manually check which products are built...")
    built_products = discovery.list_built_products()
    print(f"  ✓ Built products: {built_products}")

    print(f"\nStep 3: Get rendered content for each product...")
    for product in built_products:
        rendered = discovery.get_rendered_rule(product, rule_id)
        if rendered:
            print(f"  ✓ {product}:")
            print(f"    - YAML: {len(rendered.rendered_yaml)} chars")
            print(
                f"    - Remediations: {list(rendered.rendered_remediations.keys())}"
            )

    print(f"\nTotal: 3+ API calls (1 + 1 + N for N products)")


def example_new_way():
    """The NEW way: Single unified call."""
    print("\n" + "=" * 70)
    print("NEW WAY: Single Unified Call")
    print("=" * 70)

    from content_agent.config import initialize_settings
    from content_agent.core.integration import initialize_content_repository
    from content_agent.core import discovery

    # Initialize
    initialize_settings()
    initialize_content_repository(Path.home() / "workspace" / "content")

    rule_id = "accounts_password_pam_dcredit"

    print(f"\nSingle call: get_rule_details('{rule_id}')...")
    rule = discovery.get_rule_details(rule_id)  # That's it!

    # Source information
    print(f"\n✓ Source Information:")
    print(f"  - Rule: {rule.title}")
    print(f"  - Severity: {rule.severity}")
    print(f"  - Products: {rule.products}")

    # Rendered content (automatically included!)
    if rule.rendered:
        print(f"\n✓ Rendered Content (automatic!):")
        print(f"  - Available for {len(rule.rendered)} products")

        for product, rendered in rule.rendered.items():
            print(f"\n  {product}:")
            print(f"    - YAML: {len(rendered.rendered_yaml)} chars")
            print(
                f"    - Remediations: {list(rendered.rendered_remediations.keys())}"
            )
            print(f"    - Built: {rendered.build_time}")

    print(f"\nTotal: 1 API call (got everything!)")


def example_with_product_filter():
    """NEW way with product filter."""
    print("\n" + "=" * 70)
    print("NEW WAY: With Product Filter")
    print("=" * 70)

    from content_agent.config import initialize_settings
    from content_agent.core.integration import initialize_content_repository
    from content_agent.core import discovery

    # Initialize
    initialize_settings()
    initialize_content_repository(Path.home() / "workspace" / "content")

    rule_id = "accounts_password_pam_dcredit"

    print(f"\nSingle call with filter: get_rule_details('{rule_id}', product='rhel10')...")
    rule = discovery.get_rule_details(rule_id, product="rhel10")

    print(f"\n✓ Source Information:")
    print(f"  - Rule: {rule.title}")

    if rule.rendered:
        print(f"\n✓ Rendered Content:")
        print(f"  - Only for: {list(rule.rendered.keys())}")

        if "rhel10" in rule.rendered:
            rendered = rule.rendered["rhel10"]
            print(f"\n  RHEL 10:")
            print(f"    - YAML: {len(rendered.rendered_yaml)} chars")
            print(f"    - OVAL: {len(rendered.rendered_oval) if rendered.rendered_oval else 0} chars")
            print(f"    - Bash: {len(rendered.rendered_remediations.get('bash', '')) } chars")
            print(f"    - Ansible: {len(rendered.rendered_remediations.get('ansible', ''))} chars")

    print(f"\nTotal: 1 API call (filtered to one product)")


def example_comparison():
    """Compare source vs rendered content."""
    print("\n" + "=" * 70)
    print("BONUS: Source vs Rendered Comparison")
    print("=" * 70)

    from content_agent.config import initialize_settings
    from content_agent.core.integration import initialize_content_repository
    from content_agent.core import discovery
    import yaml

    # Initialize
    initialize_settings()
    initialize_content_repository(Path.home() / "workspace" / "content")

    rule_id = "accounts_password_pam_dcredit"
    rule = discovery.get_rule_details(rule_id)

    print(f"\nRule: {rule.title}\n")

    # Source
    print("Source (from repository):")
    print(f"  Description: {rule.description[:200]}...")

    # Rendered
    if rule.rendered:
        first_product = list(rule.rendered.keys())[0]
        rendered = rule.rendered[first_product]

        rendered_data = yaml.safe_load(rendered.rendered_yaml)
        print(f"\nRendered for {first_product} (from build):")
        print(f"  Description: {rendered_data['description'][:200]}...")

        # Check for variable expansion
        if "{{{" in rule.description:
            if "{{{" not in rendered_data["description"]:
                print("\n✅ Jinja variables were expanded in the build!")
            else:
                print("\n⚠️  Some variables remain unexpanded")


if __name__ == "__main__":
    try:
        # Show old way
        example_old_way()

        # Show new way
        example_new_way()

        # Show with filter
        example_with_product_filter()

        # Show comparison
        example_comparison()

        print("\n" + "=" * 70)
        print("Summary:")
        print("  OLD: 3+ API calls, manual coordination")
        print("  NEW: 1 API call, automatic everything!")
        print("=" * 70)

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
