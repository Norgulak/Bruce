# Project State

Last updated: 2026-08-13 (this session)

## Files
| File | Purpose |
|------|---------|
| `bruce.py` | Main AI brain v1.9 |
| `bruce_secrets.py` | ElevenLabs + Tavily API keys — gitignored, never commit |
| `bruce_wake_1.py` | Vosk wake word listener |
| `bruce_overlay_1_1.py` | HUD overlay launcher |
| `bruce_mini_overlay.py` | Mini corner overlay |
| `BRUCE __ SYSTEM HUD.html` | Main HUD |
| `BRUCE MINI.html` | Mini HUD |
| `START_BRUCE.bat` | One-click launcher — **reconstructed this session, not the verified original** (see decisions-log). Launches the overlay and wake listener; has not been confirmed to match old behavior exactly (e.g. whether `bruce.py` itself used to be launched directly too). |
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

## Known issues / pending fixes (carried over, not yet re-verified)
- TTS delay (~5 seconds with Kokoro)
- Monitor audio switch command not working
- `START_BRUCE.bat` is a reconstruction (see above) — worth testing thoroughly against expected old behavior, not just confirming it launches without error

## Resolved this session
- Debug print spam — `bruce.py`'s `BruceBrain.ask()` now gates its four `[DEBUG]` prints behind a `DEBUG_MODE` flag (default `False`) instead of always printing.
