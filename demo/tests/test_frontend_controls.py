from __future__ import annotations

from pathlib import Path


def test_frontend_exposes_max_participants_and_max_round_controls():
    html = (Path(__file__).resolve().parents[1] / "frontend" / "index.html").read_text(
        encoding="utf-8"
    )

    assert 'id="max-participants-select"' in html
    assert 'id="max-rounds-select"' in html
    assert '<option value="10">10 members</option>' in html
    assert '<option value="5">5 rounds</option>' in html


def test_frontend_posts_selected_counts_to_backend():
    js = (Path(__file__).resolve().parents[1] / "frontend" / "main.js").read_text(
        encoding="utf-8"
    )

    assert "participant_count: selectedNumberOrNull(maxParticipantsSelect)" in js
    assert "round_count: selectedNumberOrNull(maxRoundsSelect)" in js
