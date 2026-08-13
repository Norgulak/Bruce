# Roadmap

Status markers: **[confirmed]** = decided and either done or actively planned. **[proposed]** = surfaced from a reel or discussion, not yet locked in by Banmi.

## AI & Intelligence
- Smarter locally hosted AI — bigger Qwen model or Mistral **[confirmed, not started]**
- Build Bruce's neural network using `github.com/codecrafters-io/build-your-own-x` as reference **[confirmed, not started]**
- Try LiveKit for AI voice / streaming TTS to fix delay **[confirmed, not started]**
- Persistent memory vault for Bruce himself (not just this Claude/Bruce project vault, but Bruce-the-assistant having his own long-term memory of Banmi) — inspired by reel 4 (alex2learn, "infinite memory") and reel 7 (raycfu, "second brain") **[proposed]**
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
- ~~Debug lines still in CMD output~~ **[DONE]** — gated behind a `DEBUG_MODE` flag in `bruce.py` (default `False`); flip it to `True` to see raw Ollama request/response info again if troubleshooting is needed.

## Reel 5 investigation outcome
Tested `npx skills add` directly (2026-08-13). It works and installs real skill packages into a project-local `.claude/skills/` folder, but it targets 76 named coding agents by slug (claude-code, codex, cursor, windsurf, etc.) — Cowork is not among them. Coword's own skills live in a separate, read-only, Cowork-managed directory, so a project-local install here would never actually be read by this session. It *would* work if Bruce were ever developed via Claude Code CLI directly instead of Cowork — a real option, but a workflow change (terminal-based instead of chat-based), not just a "fix." Decided against installing Claude Code for this alone. Instead, pulled the actual content of the `frontend-design` skill by hand and translated it for Bruce's HUD — see `memory/frontend-design-notes.md`. Net effect: got the useful part of the reel without adopting a second tool.

## Instagram Reels Decoded So Far
1. softwarewithnick — `build-your-own-x` GitHub repo (neural network from scratch) — folded into AI & Intelligence above
2. designlab.anirudh — portfolio build, reactbits.dev — folded into HUD & UI above
3. carterperez.dev — cybersecurity dashboard/HSM emulator/canary tokens — **not relevant to Bruce, intentionally left off the roadmap**
4. alex2learn — "infinite memory" Obsidian vault concept — folded into AI & Intelligence above
5. liamjohnston.ai — open agent Skills ecosystem — folded into Claude/Agent Tooling above
6. jimmy.tensor — reaction video, not a tutorial; confirmed reel 7's pattern is a large, validated trend rather than a single creator's niche idea — no direct roadmap item, informs prioritization
7. raycfu — "second brain" vault pattern — **this vault (`CLAUDE.md` + `memory/`) is the direct implementation of what this reel showed**
