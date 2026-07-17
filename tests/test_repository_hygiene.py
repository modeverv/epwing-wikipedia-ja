from pathlib import Path


def test_generated_root_gaiji_outputs_are_gitignored() -> None:
    repository = Path(__file__).resolve().parents[1]
    patterns = set((repository / ".gitignore").read_text(encoding="utf-8").splitlines())

    assert {"/gaiji/", "/gaiji.sqlite3", "/unicode-report.json"} <= patterns
