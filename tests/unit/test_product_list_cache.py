"""Tests for reusing the product list between tool calls."""

import os

from content_agent.core.discovery.controls import controls_dir_setting
from content_agent.core.discovery.products import ProductDiscovery


def _ids(result):
    return [p.product_id for p in result.items]


class TestProductListCache:
    def test_new_product_refreshes_the_list(self, initialized_content_repo):
        repo = initialized_content_repo.path
        first = ProductDiscovery().list_products()
        (repo / "products" / "ubuntu2204").mkdir()
        (repo / "products" / "ubuntu2204" / "product.yml").write_text(
            "product: ubuntu2204\nfull_name: Ubuntu 22.04\n"
        )

        second = ProductDiscovery().list_products()

        assert _ids(first) == ["rhel9"]
        assert _ids(second) == ["rhel9", "ubuntu2204"]

    def test_changed_product_refreshes_the_list(self, initialized_content_repo):
        product_yml = initialized_content_repo.path / "products" / "rhel9" / "product.yml"
        ProductDiscovery().list_products()
        product_yml.write_text("product: rhel9\nfull_name: Renamed\n")
        stat = product_yml.stat()
        os.utime(product_yml, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))

        result = ProductDiscovery().list_products()

        assert result.items[0].name == "Renamed"

    def test_callers_get_their_own_copy(self, initialized_content_repo):
        first = ProductDiscovery().list_products()
        first.items.clear()

        second = ProductDiscovery().list_products()

        assert _ids(second) == ["rhel9"]


class TestControlsDirSetting:
    def test_reads_plain_and_quoted_values(self, tmp_path):
        plain = tmp_path / "plain.yml"
        plain.write_text("id: plain\ncontrols_dir: plain\n")
        quoted = tmp_path / "quoted.yml"
        quoted.write_text("id: quoted\ncontrols_dir: 'quoted_dir'  # requirements\n")

        assert controls_dir_setting(plain) == {"controls_dir": "plain"}
        assert controls_dir_setting(quoted) == {"controls_dir": "quoted_dir"}

    def test_absent_setting(self, tmp_path):
        control_file = tmp_path / "inline.yml"
        control_file.write_text("id: inline\ncontrols:\n    - id: R1\n      controls_dir: no\n")

        assert controls_dir_setting(control_file) == {}
        assert controls_dir_setting(tmp_path / "missing.yml") == {}


class TestProductNameAndVersion:
    def test_split_like_ssg_parse_name(self):
        from content_agent.core.discovery.products import product_name_and_version

        assert product_name_and_version("rhel9") == ("rhel", "9")
        assert product_name_and_version("ubuntu2404") == ("ubuntu", "2404")
        assert product_name_and_version("al2023") == ("al", "2023")
        assert product_name_and_version("fedora") == ("fedora", None)

    def test_product_details(self, initialized_content_repo):
        product_yml = initialized_content_repo.path / "products" / "rhel9" / "product.yml"
        product_yml.write_text(
            "product: rhel9\nfull_name: Red Hat Enterprise Linux 9\ntype: platform\n"
            "cpes:\n  - rhel9:\n      name: 'cpe:/o:redhat:enterprise_linux:9'\n"
        )

        details = ProductDiscovery().get_product_details("rhel9")
        summary = ProductDiscovery().list_products().items[0]

        assert details is not None
        assert (details.product_type, details.version) == ("rhel", "9")
        assert details.cpe == "cpe:/o:redhat:enterprise_linux:9"
        assert (summary.product_type, summary.version) == ("rhel", "9")
