# Roadmap

Status markers: **[confirmed]** = decided and either done or actively planned. **[proposed]** = surfaced from a reel or discussion, not yet locked in by Banmi.

## AI & Intelligence — Feature Priority (set 2026-08-13, Banmi wants "important features" prioritized over process/fixes)

**Phase 1 — build out Bruce's full component set:**
1. Persistent memory for Bruce himself (not just this project vault — Bruce-the-assistant having his own long-term memory of Banmi: facts, preferences, history) — inspired by reel 4 (alex2learn) and reel 7 (raycfu), same pattern already proven in this vault. **[DONE 2026-08-14 — merged to `main`. Both explicit ("remember that X") and passive (automatic extraction on session end) paths hardware-verified across a full Bruce restart. See decisions-log for the full build/review/fix history.]**
2. Smarter locally hosted model — bigger Qwen model or Mistral. Low effort relative to payoff. **[confirmed]**
3. LiveKit / streaming TTS to fix the ~5s response delay. Also listed under Pending Fixes — same underlying problem. **[confirmed]**
4. iPhone bridge, Discord, Steam notifications, daily schedule — genuinely valuable but the most complex; sequence after the above, not before. **[confirmed, lower sequence]**

**Phase 2 — ambitious, deliberately deferred, not simultaneous with Phase 1:**
- Periodic local fine-tuning (LoRA-style) on Bruce's model, run offline on a schedule (e.g. weekly), trained on curated logs pulled from Bruce's own memory vault once that exists. This is real "active learning and development" rather than just memory lookup — but it depends on Phase 1's memory system existing first to supply good training data, and it's a project of its own (not something to build in parallel with everything else). Explicitly NOT live/real-time weight updates during conversation — that's a genuinely unsolved problem (catastrophic forgetting, heavier compute needs) and isn't being pursued. **[confirmed as phase 2, not started]**

**Local-first direction (ongoing philosophy, not a blocking requirement):**
- Banmi wants Bruce to run as close to fully local as possible, but wants to finish building out Bruce's full feature set first, then deliberately move existing cloud-dependent pieces toward local alternatives afterward — not mid-build.
- Current local/cloud status: Ollama/Qwen (brain) — local. Whisper (speech-to-text) — local. Kokoro (one of three voice options) — local. ElevenLabs and Edge-TTS (the other two voice options) — both cloud, despite "Edge" sounding local. Tavily (web search) — cloud.
- Later migration is genuinely easy for voice — Kokoro already exists and is already integrated, so dropping ElevenLabs/Edge-TTS later is low-cost.
- Web search is a real exception: "search the web" inherently requires reaching the actual internet somewhere, so it can never be fully offline. "Local" there would mean not depending on Tavily specifically (e.g. self-hosting something like SearXNG) rather than zero network access.
- Sharpen Bruce's `SYSTEM_PROMPT` so his tendency to push back / not blindly agree is more explicit, matching how Claude is now expected to operate in this project **[proposed, to-do — Banmi asked for this to be tracked, not yet implemented]**

## HUD & UI
- Better, more interactive HUD **[confirmed, not started]**
- Add UI UX Pro Max from GitHub **[confirmed, not started]**
- Add 21st.dev components **[confirmed, not started]**
- News feed panel (AP/Reuters/BBC) **[confirmed, not started]**
- reactbits.dev — animated React component library (Text Pressure, Lanyard, etc.) as a resource for HUD upgrades, from reel 2 (designlab.anirudh) **[proposed]**
- Node-graph "capability map" visual style, loosely inspired by reel 6's glimpses of other people's multi-agent dashboards — aesthetic reference only, no concrete build steps **[proposed, low priority]**

## Integrations
- iPhone bridge (same WiFi) using Apple Shortcuts + HTTP: iMessage read/send, Apple Music control, Apple Calendar → HUD panel, daily schedule to dad via iMessage **[confirmed, not started]**
- Steam wishlist notifications **[confirmed, not started]**
- Discord integration **[confirmed, not started]**
- Daily schedule Bruce can edit and read each morning **[confirmed, not started]**
- "?" program (Apple Music playlist + tasks + Discord + iMessage notifs) **[confirmed, not started]**

## Claude / Agent Tooling
- Add CodeRabbit for code review **[confirmed, DONE]** — installed and verified working this session via a test PR.
- Open agent Skills ecosystem (`npx skills add <repo>`, e.g. `frontend-design`, `find-skills`) from reel 5 (liamjohnston.ai) **[investigated and resolved — see below]**
- Add UI UX Pro Max from GitHub **[confirmed, not started]**
- Add 21st.dev **[confirmed, not started]**
- Try LiveKit **[confirmed, not started]**

## HUD Pending
- Connect Apple Calendar to calendar panel **[confirmed, not started]**
- Connect todo items to real task system **[confirmed, not started]**
- Progress bar timing fine-tuning **[confirmed, not started]**

## Pending Fixes
- TTS delay (~5 seconds with Kokoro)
- Monitor audio switch command not working
- Whisper/Vosk sometimes mishears what Banmi actually says (transcription accuracy) — flagged 2026-08-14 during the memory hardware test, not investigated yet
- HUD has no text input — voice-only right now, no way to type to Bruce instead of talking — flagged 2026-08-14
- Bruce says "Ready." out loud before the wake word system is actually ready — HUD's wake-readiness bar was only ~30% when the audio cue played, so it's telling Banmi he can talk before he reliably can. Likely the same root cause as the wake-word race condition fixed earlier (bruce.py's "Ready." fires once its own init finishes, not once the separate bruce_wake_1.py process has actually finished loading Vosk + its boot wait) — flagged 2026-08-14, not fixed yet
- Bruce claimed it couldn't search the browser when asked, despite Tavily web search ("search for X" → opens Brave) being a documented existing feature — flagged 2026-08-14, not investigated (could be the phrasing not matching the search command trigger, or an actual regression)
- Memory is accumulating near-duplicate facts/preferences worded slightly differently across sessions (e.g. "Banmi prefers cold weather over hot weather" saved separately from "Banmi's preference for cold weather over hot weather") — exact-string dedup doesn't catch this. Not urgent, but will get noisier over time; worth a periodic consolidation/cleanup pass eventually — noted 2026-08-14
- Bruce's personality feels non-existent in practice despite a fairly detailed `SYSTEM_PROMPT` (dry humor, non-human perspective, proactive, corrects without judgment) — flagged 2026-08-14 by Banmi, worth revisiting once the current search fix is done. Possibly related to the small local model (qwen2.5:7b) not reliably expressing a written personality in short responses, or the prompt needing to be more directive/example-driven rather than descriptive.
- ~~Debug lines still in CMD output~~ **[DONE]** — gated behind a `DEBUG_MODE` flag in `bruce.py` (default `False`); flip it to `True` to see raw Ollama request/response info again if troubleshooting is needed.
- ~~START_BRUCE.bat never launched bruce.py itself~~ **[DONE 2026-08-14]** — the post-Notepad-incident reconstruction only started the overlay and wake listener, so the wake word had nothing to actually signal. Added the missing `start "" python bruce.py` line.
- ~~Wake word race condition on boot~~ **[DONE 2026-08-14]** — `bruce_wake_1.py` had a fixed 12s wait before listening, but `bruce.py`'s slow imports (torch/Whisper/Kokoro) can take longer than that on a cold start, so the first "Bruce online" after launch would silently fail with "Could not reach Bruce." Made `signal_bruce()` retry for ~9 seconds instead of failing after one attempt.

## Reel 5 investigation outcome
Tested `npx skills add` directly (2026-08-13). It works and installs real skill packages into a project-local `.claude/skills/` folder, but it targets 76 named coding agents by slug (claude-code, codex, cursor, windsurf, etc.) — Cowork is not among them. Coword's own skills live in a separate, read-only, Cowork-managed directory, so a project-local install here would never actually be read by this session. It *would* work if Bruce were ever developed via Claude Code CLI directly instead of Cowork — a real option, but a workflow change (terminal-based instead of chat-based), not just a "fix." Decided against installing Claude Code for this alone. Instead, pulled the actual content of the `frontend-design` skill by hand and translated it for Bruce's HUD — see `memory/frontend-design-notes.md`. Net effect: got the useful part of the reel without adopting a second tool.

## Instagram Reels Decoded So Far
1. softwarewithnick — `build-your-own-x` GitHub repo (neural network from scratch) — originally listed as its own item ("build Bruce's neural network as a learning exercise"); superseded by the Phase 2 fine-tuning plan above, which is the real version of "Bruce has a neural network that learns," rather than a from-scratch numpy tutorial project
2. designlab.anirudh — portfolio build, reactbits.dev — folded into HUD & UI above
3. carterperez.dev — cybersecurity dashboard/HSM emulator/canary tokens — **not relevant to Bruce, intentionally left off the roadmap**
4. alex2learn — "infinite memory" Obsidian vault concept — folded into AI & Intelligence above
5. liamjohnston.ai — open agent Skills ecosystem — folded into Claude/Agent Tooling above
6. jimmy.tensor — reaction video, not a tutorial; confirmed reel 7's pattern is a large, validated trend rather than a single creator's niche idea — no direct roadmap item, informs prioritization
7. raycfu — "second brain" vault pattern — **this vault (`CLAUDE.md` + `memory/`) is the direct implementation of what this reel showed**
