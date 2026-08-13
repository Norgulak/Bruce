# Vault Maintenance Rules

Adapted from a pattern shown by raycfu ("How to build a second brain with Claude") — the core idea, in our own words rather than a direct quote, since we don't have his exact prompt text:

Most people's experience with LLMs and documents is retrieval: you upload files, the model searches them when asked. That's static. This vault works differently — it's a persistent, compounding artifact that the assistant itself writes and maintains over time, not something Banmi writes by hand.

## Rules for whoever (whatever) is maintaining this vault

1. **You write it, not the user.** After any meaningful change to Bruce — a config edit, a roadmap decision, a bug fixed, a tool set up — update the relevant file in `memory/`. Don't wait to be asked.
2. **Log intent, not just diffs.** "Added CodeRabbit" is less useful than "Added CodeRabbit because Banmi wants to share the Bruce build with others and wanted review coverage first." Future sessions need the why.
3. **Flag contradictions instead of silently picking one.** If something in this vault disagrees with what you observe in the actual code or config, say so out loud rather than trusting either source blindly.
4. **Keep it lean.** This is working memory, not an archive. Prune stale entries (fixed bugs, abandoned ideas) rather than letting them pile up forever.
5. **Mark confidence.** Distinguish between "confirmed and done," "in progress," and "proposed but not decided" — especially in the roadmap. Don't quietly promote a proposal to a commitment.
6. **This file itself can be edited** if the maintenance approach stops working well in practice. It's not sacred, just a starting point.

## Why this exists
Tonight's session started with Banmi having to paste an entire handoff summary by hand because there was no persistent memory across chats, and partway through he lost track of which chat was even "the" Bruce conversation. This vault exists so that doesn't have to happen again — a fresh session in this folder should be able to read `CLAUDE.md` and immediately have working context, without a manual copy-paste ritual.
