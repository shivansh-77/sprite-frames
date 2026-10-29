# <Character>: prompts for every frame

The design, the moves and the reference pictures' table are in `<design doc>`; the game's look is in
`<art_style.md>`. This file is the master (in `<prompts_dir>`); a copy sits next to the art in `<raw_art>/<char>/`
for Codex. Claude edits only this one and copies it over after every change.

## How to use
- Codex: "draw the frames for <char>" draws every frame marked ⬜, 🔁 or ➕ in the Status table (its rules are in
  `<raw_art>/AGENTS.md`). By hand in ChatGPT: a new image chat for this character (effect sheets in a chat of their
  own), one frame per message, attach what the frame names, paste its prompt, save the result in
  `<raw_art>/<char>/<char>_codex/` as `<frame>_try<N>.png`.
- Attach to every body prompt, in this order: <1. the idle / main reference>, <2. the model sheet>. Form <B> prompts
  also attach <3. ...> third. A frame that names a still attaches it last.
- The pilot round first (marked **pilot**): if the build or colours drift, the shared block is fixed once.
- Ask for 2-3 tries where a frame is hard; frames shown only a moment keep a good-enough try.

## Status
⬜ to draw · 🔁 redraw (see its Fix line) · ➕ new, to draw · ✅ approved (which try) · ⏸ waits for another frame

| Frame | Form | Canvas | Used by | Status | Try | Note |
|---|---|---|---|---|---|---|
| idle | A | - | standing | ✅ official | picture 1 | used as it is |
| walk_01 | A | wide | walk | ⬜ pilot | | |
| defend | A | square | block | ⬜ pilot | | |
| <frame> | B | wide | <move> | ⬜ pilot | | one frame of each other form |
| <frame> | A | tall | <moves> | ⬜ | | |
| <variant> | A | square | <move> | ⏸ | | an edit of <frame> once it's ✅ |

## Frame plan
| Move | Frames, in order | Notes |
|---|---|---|
| Walk | walk_01, walk_02, walk_03 | loop 01 → 02 → 03 → 02 |
| <Special> | <frame_a>, <frame_b> | <frame_a> also used by <other move> |
| <Effect> | <sheet> | pieces: <a, b, c>; the game <stacks / scrolls / scales> them |
| <Look drawn by code> | none | <smears, afterimages, ...> |

## This character's must-haves
<The few things a model gets wrong for him, said once here and written into the shared block: e.g. "the visor
exactly as each prompt says", "exactly four legs", "no spider legs: the game draws them".>

## Official pictures used as frames (no prompt)
- idle: picture 1, as it is (mirrored if it faces the wrong way).

## The shared blocks
Every body prompt ends with its form's block, written out in full in each prompt so each one can be pasted alone.
The blocks differ only in the form sentence.

**Form A block:**
```
Keep him EXACTLY the same size, build and proportions as in the attached images: <build, spelled out>. Do not make
him <the drift away from his build: bulkier, shorter, more human, bigger-headed>. Same colours and style: <every colour
by name, where it goes, anchored to a picture>; <every marking: emblem, claws per hand, feet, tail>. <FORM A
sentence>. <The style block from art_style.md.> <View sentence>. Full body, nothing cut off. No effects (no speed
lines, motion blur, afterimages, dust, wind or stars), no shadow on the floor, no ground or scenery. <What the game
draws for him, with the reason: "No X (my game draws it)".> Transparent background (PNG); if you can't make it truly
transparent, a plain <white | magenta #FF00FF> background instead, never a checkerboard pattern.
```
**Form B block:** the same with `<FORM B sentence>`.

**If a try comes back with <the usual mistake>,** ask again with this line added at the end: "Look again: <...>".

---

## Body frames

### walk_01: <what it shows> (<move>, 1 of 3)
<For us, never pasted: which moves use it, the loop, what the game adds on top; for a hit frame the reach it needs.>

Attach <pictures>.
```
The attached images are my game character, <name> from <source>: the first image shows <...>, the second <...>.
Draw him ONCE, as ONE NEW pose, in a <WIDE (3:2, 1536x1024) | TALL (2:3, 1024x1536) | SQUARE (1024x1024)> image.
Draw a new pose, don't copy the poses of the attached images.

POSE: <limb by limb: which limb (near / far, or named by its markings), where, how bent, how far it stretches; where
the weight is and which feet touch the floor; the head and gaze; the tail or cape's line>.

<the form's shared block, written out>
```
<!-- A redraw gets one line here, never a rewrite:
**Fix (try 2), add at the end:** "<what to change>" -->

---

## Effects

### <sheet_name>: <what it is>
<For us: how the game animates the pieces (stacked, scrolled, flipped, scaled, spun), which decides the pieces.>

Attach <pictures>.
```
<pieces in a grid, in reading order, numbered and named, each with its shape and proportions; light effects as light
on a BLACK background (the game draws them additive), solid effects SOLID on magenta #FF00FF; "Nothing else in the
image: no character, no ground"; the canvas; nothing cut off>
```
