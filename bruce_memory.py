"""
Bruce Memory — persistent long-term memory for Bruce himself.

Stores facts and preferences about Banmi that persist across restarts,
separate from BruceBrain.history (which is just the current session's
conversation and gets wiped every time Bruce restarts).

Design note: this is retrieval-based memory, not weight updates. Facts get
extracted from conversations and saved here, then re-injected into Bruce's
system prompt on future runs so he has continuity without his actual model
weights ever changing. Real fine-tuning (periodic, offline, LoRA-style) is
a deliberately separate, deferred Phase 2 project — see
D:\\BRUCE\\memory\\roadmap.md for why they're kept apart.
"""
import json
import os

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bruce_memory.json")

DEFAULT_MEMORY = {
    "facts": [],
    "preferences": [],
    "history_summaries": []
}


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return dict(DEFAULT_MEMORY)
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in DEFAULT_MEMORY:
            data.setdefault(key, [])
        return data
    except (json.JSONDecodeError, OSError) as e:
        # Corrupted or unreadable - don't crash Bruce, just start fresh in memory.
        # Doesn't touch the file, so a human can inspect/recover it later if needed.
        print(f"[Bruce Memory] Couldn't read {MEMORY_FILE} ({e}), starting with empty memory this session.")
        return dict(DEFAULT_MEMORY)


def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"[Bruce Memory] Failed to save: {e}")


def format_memory_for_prompt(memory, max_facts=40, max_prefs=20, max_summaries=10):
    """Build a text block to append to Bruce's system prompt."""
    parts = []
    if memory.get("facts"):
        facts = memory["facts"][-max_facts:]
        parts.append("Known facts about your operator:\n" + "\n".join(f"- {f}" for f in facts))
    if memory.get("preferences"):
        prefs = memory["preferences"][-max_prefs:]
        parts.append("Known preferences:\n" + "\n".join(f"- {p}" for p in prefs))
    if memory.get("history_summaries"):
        summaries = memory["history_summaries"][-max_summaries:]
        parts.append(
            "Recent conversation history:\n"
            + "\n".join(f"- [{s.get('date', '?')}] {s.get('summary', '')}" for s in summaries)
        )
    if not parts:
        return ""
    return "\n\nLong-term memory (persists across restarts — this is what you actually remember about your operator):\n" + "\n\n".join(parts)


def add_fact(memory, fact):
    fact = (fact or "").strip()
    if fact and fact not in memory["facts"]:
        memory["facts"].append(fact)
        return True
    return False


def add_preference(memory, pref):
    pref = (pref or "").strip()
    if pref and pref not in memory["preferences"]:
        memory["preferences"].append(pref)
        return True
    return False


def add_history_summary(memory, date, summary):
    summary = (summary or "").strip()
    if summary:
        memory["history_summaries"].append({"date": date, "summary": summary})
        return True
    return False


def extract_from_conversation(conversation_history, query_fn):
    """
    Ask the LLM to pull out anything memory-worthy from the recent conversation.

    conversation_history: list of {"role": "user"/"assistant", "content": str}
    query_fn: a callable like BruceBrain._query(prompt, system=...) -> str

    Returns {"facts": [...], "preferences": [...], "summary": "..."}
    """
    if not conversation_history:
        return {"facts": [], "preferences": [], "summary": ""}

    convo_text = "\n".join(
        f"{'Banmi' if m['role'] == 'user' else 'Bruce'}: {m['content']}"
        for m in conversation_history[-20:]
    )

    extraction_prompt = f"""Below is a recent conversation between Banmi and Bruce (his AI wingman).

{convo_text}

Extract anything genuinely worth remembering long-term. Respond in EXACTLY this format, nothing else:

FACTS:
- (one durable fact about Banmi worth remembering, or write "none")

PREFERENCES:
- (one preference Banmi expressed, or write "none")

SUMMARY:
(one sentence summarizing what this conversation was about)

Don't invent anything that wasn't actually said. If nothing is worth remembering, write "none" under FACTS and PREFERENCES."""

    try:
        raw = query_fn(
            extraction_prompt,
            system="You extract structured memory from conversations. Be terse and accurate. Never invent information that wasn't said."
        )
    except Exception as e:
        print(f"[Bruce Memory] Extraction failed: {e}")
        return {"facts": [], "preferences": [], "summary": ""}

    return _parse_extraction(raw)


def _parse_extraction(raw):
    facts, prefs, summary = [], [], ""
    section = None
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("FACTS:"):
            section = "facts"
            continue
        if upper.startswith("PREFERENCES:"):
            section = "preferences"
            continue
        if upper.startswith("SUMMARY:"):
            section = "summary"
            continue
        if section == "facts" and line.startswith("-"):
            item = line.lstrip("- ").strip()
            if item and item.lower() != "none":
                facts.append(item)
        elif section == "preferences" and line.startswith("-"):
            item = line.lstrip("- ").strip()
            if item and item.lower() != "none":
                prefs.append(item)
        elif section == "summary":
            summary = (summary + " " + line).strip()
    return {"facts": facts, "preferences": prefs, "summary": summary}
