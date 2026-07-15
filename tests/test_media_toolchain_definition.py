from __future__ import annotations

from pathlib import Path

DOCKERFILE = Path("docker/toolchain.Dockerfile")
POLICY_FILE = Path("docker/toolchain/imagemagick-policy.xml")


def test_runtime_installs_the_pinned_imagemagick_package() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert "imagemagick=8:6.9.11.60+dfsg-1.6+deb12u9" in dockerfile


def test_runtime_installs_the_pinned_librsvg_package() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert "librsvg2-bin=2.54.7+dfsg-1~deb12u1" in dockerfile


def test_runtime_overwrites_imagemagick_policy_after_install() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    install_index = dockerfile.index("imagemagick=8:6.9.11.60+dfsg-1.6+deb12u9")
    policy_copy_index = dockerfile.index(
        "COPY docker/toolchain/imagemagick-policy.xml /etc/ImageMagick-6/policy.xml"
    )

    assert policy_copy_index > install_index


def test_policy_file_disables_dangerous_coders() -> None:
    policy = POLICY_FILE.read_text(encoding="utf-8")

    for dangerous in ("MSL", "URL", "HTTPS", "HTTP", "FTP", "EPHEMERAL", "PDF", "PS"):
        assert f'pattern="{dangerous}"' in policy

    assert 'rights="none"' in policy


def test_policy_file_is_well_formed_xml() -> None:
    import xml.etree.ElementTree as ElementTree

    ElementTree.fromstring(POLICY_FILE.read_bytes())
