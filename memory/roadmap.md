# Roadmap

Status markers: **[confirmed]** = decided and either done or actively planned. **[proposed]** = surfaced from a reel or discussion, not yet locked in by Banmi.

## AI & Intelligence — Feature Priority (set 2026-08-13, Banmi wants "important features" prioritized over process/fixes)

**Phase 1 — build out Bruce's full component set:**
1. Persistent memory for Bruce himself (not just this project vault — Bruce-the-assistant having his own long-term memory of Banmi: facts, preferences, history) — inspired by reel 4 (alex2learn) and reel 7 (raycfu), same pattern already proven in this vault. **[DONE 2026-08-14 — merged to `main`. Both explicit ("remember that X") and passive (automatic extraction on session end) paths hardware-verified across a full Bruce restart. See decisions-log for the full build/review/fix history.]**
2. Smarter locally hosted model — bigger Qwen model or Mistral. Low effort relative to payoff. **[confirmed]** Note 2026-08-14: the reel that surfaced Pocket TTS also showed Qwen3.8-Max benchmarks, initially assumed irrelevant. Corrected after Banmi pushed back — it's a real, newly open-weighted model (Alibaba published weights ~Aug 10, 2026), but reportedly 2.4 trillion parameters, ~300x the size of Bruce's current qwen2.5:7b and not remotely runnable on consumer hardware like the RTX 5070 Ti. Also controversial as "open source" — Alibaba used a restrictive custom license, not the Apache 2.0 they'd used before. Not a fit for this roadmap item; "bigger Qwen" here still means something in the 14B-32B range that actually fits local hardware.
3. Streaming TTS to fix the ~5s response delay. Also listed under Pending Fixes — same underlying problem. **[DONE 2026-08-14 — pending merge]** `kyutai-labs/pocket-tts` integrated into `bruce.py` on branch `bruce-pocket-tts` (real streaming via `generate_audio_stream()`, not the blocking `generate_audio()` — first version had a 5-10s delay, fixed). Banmi hardware-tested and preferred it over every other voice tried, and it's now set as the **default voice** (falls back to Kokoro gracefully if `pocket-tts` isn't installed on a given machine). PR open, awaiting CodeRabbit + final hardware confirmation of the default-voice change before merge.
   - Future idea, not started: try a different Pocket TTS preset voice (or a cloned one) instead of the current default "alba" — Banmi wants to explore other voice options. **[proposed, 2026-08-14]**
4. iPhone bridge, Discord, Steam notifications, daily schedule — genuinely valuable but the most complex; sequence after the above, not before. **[confirmed, lower sequence]**

**Phase 2 — ambitious, deliberately deferred, not simultaneous with Phase 1:**
- Periodic local fine-tuning (LoRA-style) on Bruce's model, run offline on a schedule (e.g. weekly), trained on curated logs pulled from Bruce's own memory vault once that exists. This is real "active learning and development" rather than just memory lookup — but it depends on Phase 1's memory system existing first to supply good training data, and it's a project of its own (not something to build in parallel with everything else). Explicitly NOT live/real-time weight updates during conversation — that's a genuinely unsolved problem (catastrophic forgetting, heavier compute needs) and isn't being pursued. **[confirmed as phase 2, not started]**

**Local-first direction (ongoing philosophy, not a blocking requirement):**
- Banmi wants Bruce to run as close to fully local as possible, but wants to finish building out Bruce's full feature set first, then deliberately move existing cloud-dependent pieces toward local alternatives afterward — not mid-build.
- Current local/cloud status: Ollama/Qwen (brain) — local. Whisper (speech-to-text) — local. Kokoro (one of three voice options) — local. ElevenLabs and Edge-TTS (the other two voice options) — both cloud, despite "Edge" sounding local. Tavily (web search) — cloud.
- Later migration is genuinely easy for voice — Kokoro already exists and is already integrated, so dropping ElevenLabs/Edge-TTS later is low-cost.
- Web search is a real exception: "search the web" inherently requires reaching the actual internet somewhere, so it can never be fully offline. "Local" there would mean not depending on Tavily specifically (e.g. self-hosting something like SearXNG) rather than zero network access.
- Sharpen Bruce's `SYSTEM_PROMPT` so his tendency to push back / not blindly agree is more explicit, matching how Claude is now expected to operate in this project **[proposed, to-do — Banmi asked for this to be tracked, not yet implemented]**

## Search quality (new 2026-08-14, from testing the conversational search fix)
- Prefer credible sources over random ones when Bruce searches — currently `web_search()` in `bruce.py` just takes Tavily's top results as-is with no source-quality weighting. **[proposed]**
- Cite the source when a search result is news or anything where the source matters (not needed for e.g. "what's the weather" but matters for "what's happening with X company") — Bruce should say where the information came from, not just state it. **[proposed]**
- Longer-term, ambitious idea: a system where Bruce recognizes patterns in the news and surfaces similar historical trends/precedents to help contextualize/decode media narratives — explicitly framed by Banmi as a "later in development" idea, not a near-term build. **[proposed, low priority, needs real design thought before starting]**

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
- ~~Try LiveKit~~ **[deprioritized 2026-08-14]** — see AI & Intelligence item 3 above; `kyutai-labs/pocket-tts` looks like a more surgical fix for the TTS delay than adopting LiveKit's full WebRTC stack. Not fully ruled out, just no longer the default plan.

## HUD Pending
- Connect Apple Calendar to calendar panel **[confirmed, not started]**
- Connect todo items to real task system **[confirmed, not started]**
- Progress bar timing fine-tuning **[confirmed, not started]**

## Pending Fixes
- TTS delay (~5 seconds with Kokoro)
- Monitor audio switch command not working
- Whisper/Vosk sometimes mishears what Banmi actually says (transcription accuracy) — flagged 2026-08-14 during the memory hardware test. **Root cause found 2026-08-14** (not yet fixed — see next item for the specific mechanism and fix plan): mostly explained by dropped audio on interrupt, below.
- **Interrupt handling needs a real architectural fix — `interrupt_flag` is a single shared global with no session/generation scoping, causing at least two distinct bugs** (reported/found 2026-08-14):
  1. *Post-interrupt audio dropped, causing frequent mishearing (~40% per Banmi)* — traced through `bruce.py`'s `voice_interrupt_listener()`, `convo_thread()`, and `record_until_silence()`. When Banmi interrupts Bruce mid-response, the interrupt is detected by a separate mic stream that only measures volume and throws away the actual audio. The real recording (`record_until_silence()`) only opens a brand-new mic stream *after* the interrupt is fully processed — a gap of roughly 100-300ms (stream teardown/setup + thread polling delay) during which anything Banmi is already saying is never captured. Confirmed by his example: interrupting to ask "why did you bring up a YouTube video" was transcribed as just "me a YouTube video."
  2. *CodeRabbit finding on PR #4, confirmed real by re-reading the code* — the INSERT-key `interrupt_listener()` sets `interrupt_flag = True` then holds it for a flat `time.sleep(0.5)` before resetting, regardless of what else happens in that window. `play_pcm_stream()` (new in this PR, used for Pocket TTS streaming) checks that same flag on its very first iteration, before opening a stream — so if Bruce's next reply starts playing within that 500ms, it silently skips the whole reply with no error. This was always technically possible but effectively never triggered with the old slow voices (TTS generation alone usually took longer than 500ms); Pocket TTS's ~200ms time-to-first-chunk is exactly what makes this newly likely to fire in normal use.
  
  Both bugs come from the same design flaw: `interrupt_flag` is reused across unrelated moments (should Bruce stop talking / should the mic start recording / should the next reply be allowed to play) with no concept of which conversation turn it belongs to. Real fix is architectural — scope interrupt/cancellation state to a playback or recording generation instead of one bare timed global flag — and should fix both symptoms at once. Bigger, riskier change than tonight's other fixes (core audio/interrupt pipeline), needs its own branch and real hardware testing. Not merge-blocking for PR #4 (pre-existing behavior, not introduced by this PR), but now higher priority given it's more likely to actually surface. **[proposed, not started, high priority]**
- HUD has no text input — voice-only right now, no way to type to Bruce instead of talking — flagged 2026-08-14
- Bruce says "Ready." out loud before the wake word system is actually ready — HUD's wake-readiness bar was only ~30% when the audio cue played, so it's telling Banmi he can talk before he reliably can. Likely the same root cause as the wake-word race condition fixed earlier (bruce.py's "Ready." fires once its own init finishes, not once the separate bruce_wake_1.py process has actually finished loading Vosk + its boot wait) — flagged 2026-08-14, not fixed yet
- ~~Bruce claimed it couldn't search the browser when asked~~ **[DONE 2026-08-14]** — root cause was two-fold: `SYSTEM_PROMPT`'s capability list never mentioned web search at all, and `is_search_query()` only matched sentences starting with an exact trigger phrase. Fixed: added search to the capability list, added conversational lead-in stripping to the fast path, and added `classify_search_intent()` as an LLM-based fallback for fully natural phrasing (only runs when a loose keyword hints at search, so ordinary chat never pays the extra latency — CodeRabbit caught that "know"/"information" were too broad and triggered on ordinary questions, narrowed after that). Hardware-verified working by Banmi, merged to `main` via PR #3.
- Memory is accumulating near-duplicate facts/preferences worded slightly differently across sessions (e.g. "Banmi prefers cold weather over hot weather" saved separately from "Banmi's preference for cold weather over hot weather") — exact-string dedup doesn't catch this. Not urgent, but will get noisier over time; worth a periodic consolidation/cleanup pass eventually — noted 2026-08-14
- Bruce's personality feels non-existent in practice despite a fairly detailed `SYSTEM_PROMPT` (dry humor, non-human perspective, proactive, corrects without judgment) — flagged 2026-08-14 by Banmi, worth revisiting once the current search fix is done. Possibly related to the small local model (qwen2.5:7b) not reliably expressing a written personality in short responses, or the prompt needing to be more directive/example-driven rather than descriptive.
- Voice interrupt is too trigger-happy and slow to recover — `voice_interrupt_listener()` in `bruce.py` breaks Bruce out of speaking based on raw mic amplitude (`VOICE_THRESHOLD = 150` over ~3 consecutive chunks, ~100ms), not actual speech detection. Any loud noise (accidental bump, background sound) triggers it, not just Banmi talking, and recovering afterward takes long enough to disrupt the conversation. Flagged 2026-08-14. Needs real speech confirmation (e.g. requiring the "interrupting" audio to actually transcribe to something) instead of a bare volume threshold.
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
