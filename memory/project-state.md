# Project State

Last updated: 2026-08-15

## Files
| File | Purpose |
|------|---------|
| `bruce.py` | Main AI brain v1.9 |
| `bruce_memory.py` | Bruce's persistent long-term memory module (facts/preferences/session summaries) — see decisions-log for design |
| `bruce_memory.json` | The actual memory data — gitignored, personal info about Banmi, never commit |
| `bruce_secrets.py` | ElevenLabs + Tavily API keys — gitignored, never commit |
| `bruce_wake_1.py` | Vosk wake word listener |
| `bruce_overlay_1_1.py` | HUD overlay launcher |
| `bruce_mini_overlay.py` | Mini corner overlay |
| `BRUCE __ SYSTEM HUD.html` | Main HUD |
| `BRUCE MINI.html` | Mini HUD |
| `START_BRUCE.bat` | One-click launcher — reconstructed after a Notepad accident, then fixed 2026-08-14 to actually launch `bruce.py` (was missing that line, which broke the wake word entirely — see decisions-log). Still not guaranteed to match the original byte-for-byte, but now confirmed functionally correct via a real hardware test. |
| `kokoro-v1.0.onnx`, `voices-v1.0.bin` | Kokoro TTS model + voice data — large binaries, gitignored |

## Config (non-secret)
```
OLLAMA_MODEL     = "qwen2.5:7b"
KOKORO_VOICE     = "am_onyx"
ELEVENLABS_VOICE = "nPczCjzI2devNBz1zQrb" (Brian — was nearly out of credits as of last check)
STATS_PORT       = 9001
WS_PORT          = 8765
ACTIVATE_KEY     = "insert"
Brave path: C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
Shure MV7 mic, headphones keyword: "shure", speakers keyword: "aw3423"
```
Live keys (ElevenLabs, Tavily) live in `bruce_secrets.py`, imported into `bruce.py` via `from bruce_secrets import ELEVENLABS_KEY, TAVILY_KEY`.

## Infrastructure (new this session)
- Git repo initialized at `D:\BRUCE`, pushed to `github.com/Norgulak/Bruce` (private).
- CodeRabbit installed and confirmed working — auto-reviews pull requests on this repo.
- Git identity: `user.name = Norgulak`, `user.email = campsmarioromero@gmail.com` (global config on this machine).

## Known issues / pending fixes
- Monitor audio switch command not working
- Whisper/Vosk transcription accuracy — Bruce sometimes mishears what Banmi says. Several real contributors found and fixed 2026-08-14 (interrupt crash, dead voice-interrupt paths, silence-bundling on repeated quick speech — see roadmap.md Pending Fixes); some residual mishearing may remain, not fully explained yet.
- HUD has no text input, voice-only
- Bruce says "Ready." before the wake word system is actually warmed up (HUD readiness bar was still ~30% when heard)
- Memory accumulates near-duplicate facts/preferences across sessions (exact-string dedup only) — not urgent, worth a periodic consolidation pass eventually
- Sharpen Bruce's `SYSTEM_PROMPT` against reflexive/blind agreement — still open, tracked in roadmap.md
- Voice interrupt triggers on raw mic amplitude, not real speech — any loud noise interrupts Bruce. The mechanism actually works reliably now (see Resolved below), this is just about it being too easily triggered by non-speech noise, not about it failing.
- Search doesn't weigh source credibility or cite sources for news-type results — see roadmap.md "Search quality"
- Post-interrupt audio may still be dropped at the very start of a new recording (the `record_until_silence()` mic-handoff gap) — needs retest now that the interrupt system itself is reliable; see roadmap.md Pending Fixes.

## Resolved this session
- Debug print spam — `bruce.py`'s `BruceBrain.ask()` now gates its four `[DEBUG]` prints behind a `DEBUG_MODE` flag (default `False`) instead of always printing.

## Resolved 2026-08-14
- `START_BRUCE.bat` was missing `start "" python bruce.py` entirely (gap from the earlier Notepad-overwrite reconstruction) — the wake word had no server to signal. Fixed.
- Wake word race condition on cold boot — `bruce_wake_1.py`'s fixed 12s wait was sometimes shorter than `bruce.py`'s import time, causing the first "Bruce online" to silently fail. `signal_bruce()` now retries for ~9s instead of giving up after one attempt.
- Automatic (passive) memory extraction was capped at one fact/one preference per session and only looked at the last 20 messages, both fixed — see decisions-log.
- **Persistent memory system (`bruce_memory.py`) shipped**: `bruce-persistent-memory` branch merged to `main` (PR #2). Both the explicit "remember that X" path and the passive end-of-session extraction path verified end-to-end on real hardware, surviving full Bruce restarts.
- **Conversational web search shipped**: `bruce-conversational-search` branch merged to `main` (PR #3). Fixed `SYSTEM_PROMPT` never mentioning Bruce has web search, and `is_search_query()` only matching exact trigger phrases. Added lead-in stripping to the fast path plus `classify_search_intent()` as an LLM-based fallback for natural phrasing. Hardware-verified working by Banmi.
- Found `kyutai-labs/pocket-tts` (verified real, 7.9k stars) as a strong candidate to replace Kokoro for the TTS-delay fix — see roadmap.md item 3. Not yet integrated.

## Resolved 2026-08-15
- **Pocket TTS shipped as Bruce's default voice**: `bruce-pocket-tts` branch merged to `main` (PR #4). Real streaming via `generate_audio_stream()` fixed the original 5-10s delay; falls back to Kokoro gracefully if `pocket-tts` isn't installed. TTS delay issue is now considered resolved.
- **Interrupt system crash + two dead voice-interrupt code paths, fixed and hardware-verified**: bundled into the same PR #4. `bruce.py` had two threads both calling `keyboard.wait(ACTIVATE_KEY)` concurrently (a redundant `interrupt_listener()` thread plus the main INSERT loop) — colliding hotkey cleanup in the `keyboard` library threw an unhandled `KeyError('insert')` that crashed the entire process on interrupt, which looked like Bruce "freezing." Fixed by deleting the redundant thread. Separately, `voice_interrupt_listener()` had a dead second mic-monitoring block that reused an already-terminated `PyAudio` object (silent failure, no error printed) and was also gated behind `conversation_mode`, making voice interrupt silently impossible during INSERT-triggered replies. Both fixed. Confirmed via repeated hardware interrupt testing, both voice and keyboard.
- Widened `bruce_wake_1.py`'s wake-word activation retry window from ~9s to ~18s — Pocket TTS's added load time was intermittently pushing boot past the old window.
- **Conversational search hint-gate fix shipped**: `bruce-search-hint-fix` branch merged to `main` (PR #5). "going on with" broadened to "going on" / "happening" after Banmi's real-world test showed "going on in the stock market" didn't match.
