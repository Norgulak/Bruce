# HUD Design Notes

Source: `anthropics/skills` → `frontend-design` skill (via the open agent Skills ecosystem, surfaced in reel 5). The automated `npx skills add` mechanism doesn't plug into Cowork (see roadmap.md for why), so this is the actual guidance pulled out by hand and translated for Bruce's HUD specifically, rather than the generic version.

## The core mistake to avoid
Most AI-generated UI clusters around a handful of visual defaults — a warm cream background with a serif display font, or a near-black background with one bright accent color, or a newspaper-style hairline-rule layout. These aren't wrong, but they're defaults, not choices. Bruce's HUD already has a real identity (dark, sci-fi, wingman-not-assistant) — any redesign work should make deliberate choices that fit *that*, not whatever a generic prompt would produce.

## Applying this to Bruce specifically
- **The HUD's "hero" is the status ring / Mission Briefing panel** — that's the first thing the eye should land on, so it deserves the most deliberate design attention, not the panels around it.
- **Spend boldness in one place.** Right now the HUD has a lot going on (progress bar, stats, CMD log, status ring, calendar, weather, todo, oscilloscope, pipeline, animation canvas). Per this guidance, one element should be the memorable signature — everything else should stay quiet and disciplined around it. Worth deciding which panel that is before adding more.
- **The animation system (radar, gears, targeting, core, warp, council, thinking, idle) is already the kind of "deliberate motion" this guidance recommends** — keyword-triggered, purposeful, not decorative. Good instinct already in place; don't dilute it by adding animation elsewhere just because it's possible.
- **Numbered/structural markers should mean something.** If any future panel uses numbering (e.g., a step sequence), it should represent a real order, not just decoration.
- **Copy matters.** Any text Bruce's HUD displays (status labels, error states) should describe what's happening in plain, active terms — matching Bruce's own established voice (dry, direct, no padding) rather than generic UI copy like "Submit" or "Error occurred."

## On the Skills ecosystem itself
The broader lesson from reel 5 isn't really "install this specific package" — it's the underlying idea: when a design or engineering question comes up, check whether there's an established, battle-tested pattern before improvising. I can do that manually by pulling the relevant skill content directly, as done here, even without the CLI mechanism working in this environment.
