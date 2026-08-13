# Decision Log

Chronological, most recent first. Each entry: what changed, why.

## 2026-08-13 — Workflow: selective PRs + mandatory run-and-check for core changes
Considered a local git hook to force every change through a branch + PR (so CodeRabbit reviews everything). Decided against it: Banmi's intent is single-machine development, not multi-collaborator, and forcing full PR ceremony on every small edit adds friction disproportionate to the benefit. Landed on a lighter rule instead: routine small changes go straight to `main`; branch + PR + CodeRabbit review is reserved for risky/substantial changes. Separately, added a hard rule that any change to a core Bruce function (audio, TTS, wake word, brain logic, HUD data flow) must actually be run and checked before being called done — motivated by Banmi's experience during Bruce's original build of repeatedly having to go back and fix things that looked right but didn't work in practice. CodeRabbit reviews code quality on PRs but never executes Bruce, so it can't catch that category of bug; the run-and-check step is what actually addresses it.

## 2026-08-13 — Debug print spam cleaned up
Added a `DEBUG_MODE = False` flag to `bruce.py`'s config block and wrapped the four `[DEBUG]` prints in `BruceBrain.ask()` behind it, instead of deleting them outright. Why: they were cluttering the console on every response, but they're genuinely useful if the Ollama connection breaks again — gating instead of deleting keeps that option available.

## 2026-08-13 — Reel 5 (Skills ecosystem) investigated, resolved without adopting a new tool
Ran `npx skills add` for real to check whether it installs somewhere Cowork reads. Confirmed it doesn't — it targets 76 named coding agents (Claude Code CLI among them), not Cowork specifically, and writes to a project-local `.claude/skills/` folder that this session doesn't read from. Considered installing Claude Code CLI to make it work, but that's a workflow change (terminal-based dev instead of chat-based), not a small fix, so decided against it for now. Instead manually pulled the `frontend-design` skill's actual guidance and wrote it up for Bruce's HUD specifically in `memory/frontend-design-notes.md` — captured the useful content without the broken automation.

## 2026-08-13 — Memory vault created
Implemented the "second brain" pattern from reel 7 (raycfu): `CLAUDE.md` + `memory/` folder, written and maintained by the AI. Why: this exact session started with Banmi having to manually paste a full handoff summary, and later lost track of which chat was "the" Bruce conversation entirely. Goal is for a fresh session to get working context automatically instead of repeating that.

## 2026-08-13 — CodeRabbit installed and verified
Set up git on the local machine, created a GitHub repo (`Norgulak/Bruce`, private), pushed the initial commit, then installed CodeRabbit via GitHub App and confirmed it works with a real test pull request (it left an automated review comment). Why: Banmi wants to eventually share the Bruce build with others and wanted review coverage in place first, plus wanted Claude to have "faster tools" for building Bruce going forward.

## 2026-08-13 — API keys extracted from bruce.py
`ELEVENLABS_KEY` and `TAVILY_KEY` were hardcoded directly in `bruce.py`. Moved both into a new `bruce_secrets.py`, gitignored it, and changed `bruce.py` to import from it instead. Why: about to push this code to a public-ish GitHub repo (even private repos aren't a great place for live credentials, and CodeRabbit itself would've been able to read them) — decided to fix this before the first commit rather than after.

## 2026-08-13 — START_BRUCE.bat accidentally overwritten, reconstructed
While creating `.gitignore` via Notepad, a Save As dialog wrote gitignore content into `START_BRUCE.bat` instead, overwriting the real 414-byte launcher. No Windows "previous versions" backup existed. Rebuilt it as a best-effort reconstruction (launches `bruce_overlay_1_1.py` and `bruce_wake_1.py`) based on what the other files do — **not verified to exactly match the original's behavior.** Banmi confirmed the reconstruction "works," but this should be treated as provisionally correct, not confirmed-identical to the original.

## 2026-08-13 — D:\BRUCE connected as a working folder
Previously Claude only had Bash access to the folder via a mounted sandbox path, requiring Banmi to manually run every command in his own Command Prompt (source of most of this session's friction — wrong drives, merged pastes, Notepad mistakes). Connecting the folder directly lets Claude read/write/edit files in `D:\BRUCE` without relaying through the user's terminal.
