# sprite-frames

A Claude Code skill for making a game character's sprite frames and effect sheets with an AI image tool. Codex (or
ChatGPT) draws, Claude directs and fits, you decide:

reference pictures + design talk → frame plan → prompts file → pilot round → drawing rounds → checks, fitting, review
sheets → ✅ / 🔁 Fix / ➕ new → until every frame is ✅.

`SKILL.md` is what Claude reads; `reference/` holds the design questions, the prompt recipe (with Lessons) and the
review checklist; `templates/` the project settings, prompts file, Codex's `AGENTS.md` and the art style;
`scripts/` the Python tools (numpy, Pillow, scipy) for fitting, checks and review sheets.

## Install
Claude Code finds personal skills in `~/.claude/skills/`, so clone it there:
```
git clone https://github.com/shivansh-77/sprite-frames.git ~/.claude/skills/sprite-frames
```
It loads when you work on character art in any project, or with `/sprite-frames`.
