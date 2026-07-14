from __future__ import annotations

from pathlib import Path

DOCKERFILE = Path("docker/toolchain.Dockerfile")


def test_runtime_installs_the_pinned_noto_cjk_font_package() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert "fonts-noto-cjk=1:20220127+repack1-1" in dockerfile
