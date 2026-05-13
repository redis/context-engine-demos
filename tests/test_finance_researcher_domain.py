from pathlib import Path
from hashlib import sha256
import json

from backend.app.core.domain_loader import load_domain


def snapshot_tree(root: Path) -> list[tuple[str, int, int, str]]:
    if not root.exists():
        return []
    entries: list[tuple[str, int, int, str]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        data = path.read_bytes()
        stat = path.stat()
        entries.append(
            (
                str(path.relative_to(root)),
                stat.st_size,
                stat.st_mtime_ns,
                sha256(data).hexdigest(),
            )
        )
    return entries


def test_finance_researcher_domain_loads_and_generates_data(tmp_path: Path) -> None:
    domain = load_domain("finance-researcher")
    assert domain.manifest.id == "finance-researcher"
    assert domain.manifest.branding.starter_prompts
    assert domain.manifest.branding.ui.show_platform_surface is True
    assert domain.manifest.branding.ui.show_live_updates is True
    assert len(domain.get_entity_specs()) == 7
    tool_names = {tool.name for tool in domain.get_internal_tool_definitions(runtime_config={})}
    assert "recent_watchlist_events" in tool_names

    shared_raw_dir = Path(__file__).resolve().parents[1] / "output" / "finance-researcher" / "raw"
    shared_raw_snapshot = snapshot_tree(shared_raw_dir)

    result = domain.generate_demo_data(output_dir=tmp_path, update_env_file=False)
    assert result.summary["companies"] == 14
    assert result.summary["research_documents"] >= 4
    assert result.summary["coverage_events"] >= 7

    for spec in domain.get_entity_specs():
        assert (tmp_path / spec.file_name).exists()

    for file_name in ("research_documents.jsonl", "research_chunks.jsonl", "coverage_events.jsonl"):
        for line in (tmp_path / file_name).read_text().splitlines():
            row = json.loads(line)
            document_id = row.get("document_id")
            if document_id:
                assert "-" not in document_id

    raw_dir = tmp_path / "raw"
    assert raw_dir.exists()
    assert snapshot_tree(shared_raw_dir) == shared_raw_snapshot
