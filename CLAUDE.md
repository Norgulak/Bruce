# Bruce AI Wingman — Project Memory

This file is the entry point for any AI assistant (Claude Code, Cowork, or otherwise) working in this folder. Read this first. Deeper context lives in `memory/`.

This vault follows the "second brain" pattern: it is written and maintained by the AI, not manually by the user. See `memory/IDEA.md` for the maintenance rules before editing anything in here.

## What Bruce Is
A local AI voice assistant running on Banmi's Windows PC (RTX 5070 Ti, Ryzen 5900X, 64GB RAM). Non-human wingman personality: dry, deadpan, corrects mistakes without judgment, no evolutionary biases in its worldview. All files live in `D:\BRUCE\`.

## Where to look
- `memory/project-state.md` — current files, config, pending fixes, what's known to be broken
- `memory/roadmap.md` — full feature roadmap, split into confirmed vs. proposed-but-not-locked-in
- `memory/decisions-log.md` — chronological record of changes made to this project, with *why*, not just *what*
- `memory/IDEA.md` — the rules for how this vault itself should be maintained

## Quick facts an assistant should know before doing anything
- This repo is on GitHub at `github.com/Norgulak/Bruce` (private), with CodeRabbit wired up to auto-review pull requests.
- Live API keys live in `bruce_secrets.py`, which is gitignored. Never hardcode keys back into `bruce.py`.
- `kokoro-v1.0.onnx` and `voices-v1.0.bin` are large binaries excluded from git via `.gitignore` — don't try to commit them.
- Banmi is not a developer by background — explanations should default to plain language unless he's asked for the technical version. He also does not want blind agreement — push back with reasoning when warranted, for both Claude and Bruce.
