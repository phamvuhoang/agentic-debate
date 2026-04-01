"""A2UI message builders and stream observer for the debate demo."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from agentic_debate.context import DebateContext
from agentic_debate.types import (
    DebateArbitration,
    DebateChallenge,
    DebateParticipant,
)

SURFACE_ID = "debate-surface"
ROOT_ID = "debate_root"


# ---------------------------------------------------------------------------
# Low-level component helpers (private)
# ---------------------------------------------------------------------------


def _text(uid: str, text: str, hint: str = "body") -> dict[str, Any]:
    return {"id": uid, "component": {"Text": {"text": {"literalString": text}, "usageHint": hint}}}


def _column(uid: str, children: list[str]) -> dict[str, Any]:
    return {"id": uid, "component": {"Column": {"children": {"explicitList": children}}}}


def _card(uid: str, child_id: str) -> dict[str, Any]:
    return {"id": uid, "component": {"Card": {"child": child_id}}}


def _button(uid: str, action_name: str, child_id: str) -> dict[str, Any]:
    return {
        "id": uid,
        "component": {
            "Button": {
                "child": child_id,
                "action": {"name": action_name, "context": []},
            }
        },
    }


def _surface_update(components: list[dict[str, Any]]) -> str:
    return json.dumps({"surfaceUpdate": {"surfaceId": SURFACE_ID, "components": components}})


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def color_emoji(hex_color: str) -> str:
    mapping = {
        "#4F86C6": "🔵",
        "#E05A5A": "🔴",
        "#4CAF50": "🟢",
        "#F5A623": "🟡",
        "#9B59B6": "🟣",
    }
    return mapping.get(hex_color, "⚪")


# ---------------------------------------------------------------------------
# Public message builder functions
# ---------------------------------------------------------------------------


def begin_rendering_msg(surface_id: str, root_id: str) -> str:
    return json.dumps({"beginRendering": {"surfaceId": surface_id, "root": root_id}})


def status_card_msg(text: str, existing_children: list[str]) -> str:
    """Shows/replaces the status card. Status card is always appended (removing prior instance)."""
    children = [c for c in existing_children if c != "status_card"] + ["status_card"]
    return _surface_update([
        _column(ROOT_ID, children),
        _card("status_card", "status_text"),
        _text("status_text", text, "h3"),
    ])


def topic_card_msg(
    reframed_topic: str,
    domain: str,
    controversy_level: str,
    existing_children: list[str],
    locale: str = "en",
) -> str:
    """Remove status_card and topic_card if present, append topic_card."""
    children = [c for c in existing_children if c not in ("status_card", "topic_card")] + ["topic_card"]
    controversy_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(controversy_level, "⚪")
    meta = f"{controversy_emoji} {controversy_level.capitalize()} controversy · {domain.capitalize()}"
    return _surface_update([
        _column(ROOT_ID, children),
        _card("topic_card", "topic_col"),
        _column("topic_col", ["topic_title", "topic_meta"]),
        _text("topic_title", reframed_topic, "h2"),
        _text("topic_meta", meta, "body"),
    ])


def participant_intro_card_msg(
    participant: DebateParticipant,
    existing_children: list[str],
) -> str:
    uid = f"p_intro_{participant.participant_id}"
    children = [c for c in existing_children if c != "status_card"] + [uid]
    color = participant.metadata.get("accent_color", "#888")
    label = f"{color_emoji(color)} {participant.label}"
    stance_text = participant.stance or "—"
    return _surface_update([
        _column(ROOT_ID, children),
        _card(uid, f"{uid}_col"),
        _column(f"{uid}_col", [f"{uid}_name", f"{uid}_role", f"{uid}_stance"]),
        _text(f"{uid}_name", label, "h3"),
        _text(f"{uid}_role", participant.role.capitalize(), "body"),
        _text(f"{uid}_stance", f'"{stance_text}"', "body"),
    ])


def round_header_msg(round_index: int, existing_children: list[str], locale: str = "en") -> str:
    uid = f"round_{round_index}_hdr"
    children = existing_children + [uid]
    label = f"Round {round_index}"
    # Minimal static translation for demo
    if locale == "vi": label = f"Vòng {round_index}"
    elif locale == "ja": label = f"第 {round_index} ラウンド"
    
    return _surface_update([
        _column(ROOT_ID, children),
        _text(uid, f"── {label} ──", "h2"),
    ])


def argument_card_msg(
    challenge: DebateChallenge,
    participants: list[DebateParticipant],
    existing_children: list[str],
    locale: str = "en",
) -> str:
    uid = f"arg_r{challenge.round_index}_{challenge.challenger_id}_vs_{challenge.target_id}"
    children = existing_children + [uid]
    pid_map = {p.participant_id: p for p in participants}
    challenger = pid_map.get(challenge.challenger_id)
    target = pid_map.get(challenge.target_id)
    color = challenger.metadata.get("accent_color", "#888") if challenger else "#888"
    name = challenger.label if challenger else challenge.challenger_id
    target_name = target.label if target else challenge.target_id
    conf_pct = int(challenge.confidence * 100)
    
    challenges_label = "challenges"
    confidence_label = "confidence"
    if locale == "vi":
        challenges_label = "phản biện"
        confidence_label = "độ tin cậy"
    elif locale == "ja":
        challenges_label = "への反論"
        confidence_label = "信頼度"

    footer = f"→ {challenges_label} {target_name}  ·  {conf_pct}% {confidence_label}"
    return _surface_update([
        _column(ROOT_ID, children),
        _card(uid, f"{uid}_col"),
        _column(f"{uid}_col", [f"{uid}_name", f"{uid}_body", f"{uid}_footer"]),
        _text(f"{uid}_name", f"{color_emoji(color)} {name}", "h3"),
        _text(f"{uid}_body", challenge.challenge_text, "body"),
        _text(f"{uid}_footer", footer, "body"),
    ])


def arbitrating_msg(existing_children: list[str], locale: str = "en") -> str:
    children = existing_children + ["arbitrating_card"]
    label = "⚖️ Judge is deliberating…"
    if locale == "vi": label = "⚖️ Thẩm phán đang cân nhắc…"
    elif locale == "ja": label = "⚖️ 審判が検討中です…"
    return _surface_update([
        _column(ROOT_ID, children),
        _card("arbitrating_card", "arbitrating_text"),
        _text("arbitrating_text", label, "h3"),
    ])


def verdict_card_msg(
    arbitration: DebateArbitration,
    participants: list[DebateParticipant],
    existing_children: list[str],
    transcript: dict[str, Any] | None = None,
    locale: str = "en",
) -> str:
    pid_map = {p.participant_id: p for p in participants}
    # Remove arbitrating_card from children if present, append verdict_card
    children = [c for c in existing_children if c != "arbitrating_card"] + ["verdict_card"]

    # Use localized strings from transcript if provided, otherwise fall back to arbitration object
    summary = transcript.get("summary") if transcript else arbitration.summary
    verdicts_data = transcript.get("verdicts") if transcript else [v.model_dump() for v in arbitration.verdicts]
    contested = transcript.get("contested_topics") if transcript else list(arbitration.contested_topics)

    verdict_child_ids: list[str] = ["verdict_summary"]
    components: list[dict[str, Any]] = [
        _text("verdict_summary", f"📋 {summary}", "h3"),
    ]
    for i, v in enumerate(verdicts_data):
        vid = f"verdict_item_{i}"
        winner_id = v.get("winning_participant_id") if isinstance(v, dict) else v.winning_participant_id
        winner = pid_map.get(winner_id)
        winner_name = winner.label if winner else winner_id
        
        conf = v.get("confidence") if isinstance(v, dict) else v.confidence
        conf_pct = int(conf * 100)
        
        rationale = v.get("rationale") if isinstance(v, dict) else v.rationale
        verdict_text = f"🏆 {winner_name} ({conf_pct}%) — {rationale}"
        
        verdict_child_ids.append(vid)
        components.append(_text(vid, verdict_text, "body"))
        
        open_questions = v.get("open_questions") if isinstance(v, dict) else v.open_questions
        for j, q in enumerate(open_questions):
            qid = f"verdict_item_{i}_q{j}"
            verdict_child_ids.append(qid)
            components.append(_text(qid, f"❓ {q}", "body"))

    if contested:
        cid = "verdict_contested"
        verdict_child_ids.append(cid)
        label = "Contested"
        if locale == "vi": label = "Tranh cãi"
        elif locale == "ja": label = "論争中"
        components.append(_text(cid, f"⚡ {label}: " + ", ".join(contested), "body"))

    btn_uid = "restart_btn"
    btn_label_uid = "restart_btn_label"
    verdict_child_ids.append(btn_uid)
    btn_label = "Ask another question"
    if locale == "vi": btn_label = "Đặt câu hỏi khác"
    elif locale == "ja": btn_label = "別の質問をする"
    components.append(_button(btn_uid, "restart_debate", btn_label_uid))
    components.append(_text(btn_label_uid, btn_label, "body"))

    return _surface_update([
        _column(ROOT_ID, children),
        _card("verdict_card", "verdict_col"),
        _column("verdict_col", verdict_child_ids),
        *components,
    ])


def error_card_msg(message: str, existing_children: list[str]) -> str:
    children = existing_children + ["error_card"]
    return _surface_update([
        _column(ROOT_ID, children),
        _card("error_card", "error_text"),
        _text("error_text", f"❌ {message}", "h3"),
    ])


# ---------------------------------------------------------------------------
# A2UIStreamObserver
# ---------------------------------------------------------------------------


class A2UIStreamObserver:
    """Translates engine lifecycle events into A2UI messages on an asyncio queue."""

    def __init__(
        self,
        queue: asyncio.Queue[str | None],
        participants: list[DebateParticipant],
    ) -> None:
        self._queue = queue
        self._participants = participants
        self._children: list[str] = []

    def _enqueue(self, msg: str) -> None:
        self._queue.put_nowait(msg)

    async def on_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        context: DebateContext,
    ) -> None:
        _ = (payload, context)
        if event_type == "arbitration_started":
            msg = arbitrating_msg(self._children, locale=getattr(self, "_locale", "en"))
            # Update _children to reflect the new arbitrating_card
            new_children = json.loads(msg)["surfaceUpdate"]["components"][0]["component"]["Column"]["children"]["explicitList"]
            self._children.clear()
            self._children.extend(new_children)
            self._enqueue(msg)
        # Other events are handled by main.py directly (round headers, argument cards, etc.)
