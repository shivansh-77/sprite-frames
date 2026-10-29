---
name: sprite-frames
description: Make or redo a game character's sprite frames and effect sheets with an AI image tool (Codex or ChatGPT draws, Claude directs) - the design talk from reference pictures, a frame plan, a paste-ready prompts file, drawing rounds, then checking, fitting and approving every frame until all are done. Use when the user wants new character art, animation or sprite frames, effect sprite sheets, an art style for a new game, or says a Codex/ChatGPT frames folder is ready to check, in any game project or engine.
---

# Sprite frames with an AI image tool

The user's proven loop (six characters in a 2.5D fighter): **Claude is the art director and fitter, Codex (or
ChatGPT) only draws, the user decides.** Teach as you go: the user is learning game development, so say briefly what
each step and file is for.

```
references + design talk → frame plan → prompts file → pilot round → rounds: Codex draws → Claude checks, fits,
reviews → ✅ / 🔁 Fix / ➕ new → … until every frame is ✅ → install, tidy up, lessons
```

Paths below: `<skill>` = this skill's folder; everything else comes from the project's `sprite_frames.json`.

## Rules that always hold
- **Approve the clear frames yourself; ask the user only about doubtful ones** (show the review sheet). The user can
  veto any approved frame: it goes back to 🔁.
- **The master prompts file is `<prompts_dir>/<char>_prompts.md`.** Edit only it; after every change run
  `sync_prompts.py` so the copy next to the art (`<raw_art>/<char>/<char>_prompts.md`, the one Codex reads) matches.
- **A redraw gets one Fix line under its prompt, not a rewrite**, so it stays clear what fixed what.
- **Never overwrite or delete the user's pictures** except rejected tries when a character is finished (step 7).
- Ask before anything big: the frame plan, adding frames, changing the shared block, installing into the game.
- The raw-art folder is only for Claude, Codex and the user: never imported or shipped by the engine.

## 0. Once per project: setup
1. **Settings:** copy `<skill>/templates/sprite_frames.json` to the project root as `sprite_frames.json` and fill it
   in from the engine (where sprites go and how they're named, the canvas, the idle's drawn height, the scale the game
   draws them at, the background colour of the game for review sheets). Ask the user what you can't read from the
   project. Every script reads it (`--settings`; found in the current folder or its parents).
2. **Raw-art folder** (default `character_raw_art/` inside the project, snake_case names, no spaces):
   `<char>/<char>_reference/`, `<char>/<char>_codex/`, `<char>/<char>_prompts.md` (the copy). Keep the engine away
   from it: Godot → an empty `.gdignore` file in it; web builds (Vite, Phaser) → outside `public/`. If the user moves
   it outside the project (an exception), set `raw_art` to the absolute path, ask them to add that folder to the
   session, and suggest a cloud-synced folder as its backup (it's out of git then).
3. **Codex's instructions:** copy `<skill>/templates/AGENTS.md` to `<raw_art>/AGENTS.md` (Codex reads it by itself,
   like Claude reads CLAUDE.md).
4. **The art style, once per game:** before the first character, fill in `<skill>/templates/art_style.md` with the
   user as `docs/art_style.md` (`art_style` in the settings): lines, shading, colours, proportions, view, what the game
   draws itself, the style block every prompt includes. **The first character is the style test**: change the file
   until its pilot frames look right; its approved idle becomes the style reference later characters attach.
5. **A project that already has characters:** map its existing folders in the settings instead of moving them (per
   character `reference_dir` / `codex_dir`), and write `art_style.md` from its approved frames and prompts files.

## 1. Design talk
Follow `<skill>/reference/design_questions.md`. **Reference pictures first** (ask the user for them; they go in
`<char>_reference/`, numbered, in a table in the design notes: file / what it shows / use). Then a few rounds of
questions: role and fighting
style, movement, attacks, specials, the super, defence and getting hit. **Every move confirmed, the walk included.**
Write the design into the project's character notes.

## 2. Frame plan
First give every reference picture a use (a frame's pose, an effect, or "not used"). Then every move mapped to its
frames (1 to 5 per move), frames shared between moves, variants made as edits of an approved frame (arms crossed in
an X for the block → the same with the mouth open for a roar), effects (sheets or single frames, and how the code
animates each) in the same plan, each frame with its form and canvas shape. Show it to the user and confirm before
writing prompts.

## 3. Prompts file
Write `<prompts_dir>/<char>_prompts.md` from `<skill>/templates/prompts.md`, following
`<skill>/reference/prompt_recipe.md` (the template's sections are the layout): the Status table (⬜ to draw ·
🔁 redraw · ➕ new · ✅ approved · ⏸ waits), the frame plan, the character's must-haves, the shared block per form
written out in every prompt, one prompt per frame, the effect sheets. Mark 3 frames **pilot** (a walk, the block,
one frame of each other form or a colour that's easy to get wrong). Run
`sync_prompts.py`. Tell the user: open Codex on the project and say "draw the pilot frames for <char>".

## 4. A review round (each time the user says the folder is ready)
1. **Checks:** `python <skill>/scripts/check_frames.py --settings sprite_frames.json --char <char> --source raw`
   (transparency, a background left in, light fringe, cut off, forbidden colours). A white or magenta background left
   in → `cutout.py`, then `defringe.py` on that raw try (both keep a backup), before fitting. A frame drawn facing the
   wrong way gets `"mirror": true` in the settings.
   The flags are hints, not verdicts: a forbidden-colour range can catch a colour the character really has (lime
   eyes inside a "green" range: narrow the range in the settings), and the near-duplicate threshold (a constant at
   the top of `check_frames.py`) was calibrated on one character.
2. **Look at every new try yourself** (read the image) with `<skill>/reference/review_checklist.md`: likeness and
   build vs the idle, extra or missing limbs, the pose the prompt asked for, readable at game size.
3. **Fit the candidates for review:** set each frame's `file` (the try), `factor` and `centring` in the settings, then
   `fit_frames.py --settings … --char <char> --frames … --out <char_dir>/review/`; then
   `check_frames.py --source fitted --dir <char_dir>/review/` (size vs the idle, near-duplicates).
4. **Review sheet:** `review_sheet.py --settings … --char <char> --frames … --dir <char_dir>/review/ --verdicts
   v.json --out <char_dir>/review/sheet.png`, and `--anim … --gif …` for each move whose frames are all in (some
   problems only show in motion). Look at both yourself before showing the user.
5. **Verdicts:** ✅ clear ones (Status: ✅ + the try); 🔁 with one Fix line; ➕ prompts for frames a move still needs.
   Show the user the sheet and **ask only about the doubtful ones**, each with your pick. Frames shown only for a few
   milliseconds keep a good-enough try.
6. After the **pilot**: if the build or colours drifted, fix the shared block once (ask first), then the full round.
7. `sync_prompts.py`, then tell the user what to ask Codex next ("draw the frames for <char>": it draws every ⬜ 🔁 ➕).

## 5. Finish (every frame ✅)
1. **Install** the approved frames the way the project's own rules say (CLAUDE.md, the engine's sprite lists or
   animation resources): `fit_frames.py` without `--out` writes into the game's sprites. Ask before writing into the
   game.
2. **Tidy up:** delete only the rejected tries from `<char>_codex/` (ask first); the approved raws stay, full size,
   as the source if the frames are ever re-fitted.
3. **Lessons:** add what this character taught (a wording that fixed a mistake, a check that caught something) to
   `<skill>/reference/prompt_recipe.md` → Lessons, and tell the user what you added. The skill gets better with every
   character.

## Scripts (`<skill>/scripts/`, Python with numpy and Pillow; all take `--settings`)
| Script | What it does |
|---|---|
| `sf_settings.py` | Reads `sprite_frames.json` (used by every script) |
| `check_frames.py` | Automatic checks on raw or fitted frames; a report, never changes files |
| `fit_frames.py` | Idle to its height, every frame to the idle's size (area × factor), feet on one line, canvas; effect sheets cut into pieces and packed, with an anchors JSON (format in its docstring); `--out` for a review folder |
| `cutout.py` | Removes a white or magenta background (`white_threshold` for pale characters) |
| `defringe.py` | Removes the light ring a white or magenta background leaves round outlines (`--hole` for gaps between limbs) |
| `review_sheet.py` | Frames next to the idle at game size with verdicts; an animated GIF of a move |
| `sync_prompts.py` | Copies the master prompts file next to the art |

## Files
- `reference/design_questions.md`: the design talk and the frame plan.
- `reference/prompt_recipe.md`: how to write prompts that work, what the tools get wrong, Lessons.
- `reference/review_checklist.md`: what to check in a round, verdicts.
- `templates/`: `sprite_frames.json`, `prompts.md`, `AGENTS.md` (for Codex), `art_style.md`.
