# Prompt recipe: the prompts file and each prompt

Distilled from six characters drawn by ChatGPT images / Codex for a 2D fighting game. It works for any game or
engine: it's about getting consistent, single-pose sprite frames out of an image model. Examples are from the Omni
Clash project (`docs/characters/xlr8_prompts.md` is the best model; Ben 10 names appear only in examples).

## 1. The prompts file

One file per character (e.g. `docs/characters/<name>_prompts.md`). **Its sections are the ones in
`templates/prompts.md`, in that order** (that template is the one place the layout is defined): How to use, Status
(frame, form, canvas, used by, status, try, note), Frame plan, This character's must-haves (what a model gets wrong
for *him*: "the visor exactly as each prompt says", "no eyes, ever", "no spider legs: the game draws them"), Official
pictures used as frames (no prompt: "idle (picture 1, as it is)", "bite (picture 11, mirrored)"), The shared blocks
(one per form) with the fallback lines (section 6), then one section per frame, grouped as the frame plan groups
them (core, combo, air, specials, wall), and the effects.

The file is the living record: verdicts, results and retry lines are written into it as rounds come back
(see `review_checklist.md`).

### The how-to-use header
- **What to attach to every body prompt, in order**, with paths. Form variants add theirs after
  ("visor-down prompts (marked D) also attach `02_..._visor_down.png` third"). A frame that names a still attaches
  it last (when a still may be attached: section 3, part 1).
- **A new image chat for this character.** An old chat keeps reusing the characters it drew before. Body frames can
  share one chat; effect sheets get a chat of their own.
- **One frame per message:** attach, then paste the prompt.
- **Ask for 2-3 tries** and keep the best. For frames shown only a moment (jabs, kicks, skids, slams), a good-enough
  try beats chasing retries.
- **Pilot frames first:** name 2-3 frames to bring back before the rest, one per form variant (XLR8: `defend`,
  `walk_01`, `blur`). If the build, colours or a marking drift, fixing the shared block once is cheaper than redoing
  every frame.
- **Where results go:** `<raw_art>/<char>/<char>_codex/`, one file per try, `<frame>_try<N>.png` (`_try1` first);
  nothing is ever overwritten.
- **With Codex (batch):** its rules are in `<raw_art>/AGENTS.md` (`templates/AGENTS.md`): "draw the frames for
  <char>" draws every frame the Status table marks ⬜, 🔁 or ➕, each prompt exactly as written plus its Fix line,
  with its attachments. It changes no prompt and no table.

## 2. A frame's section

```
### walk_01: jogging, the reach (walk 1 of 3)
His walk is a fast jog, looped walk_01 -> walk_02 -> walk_03 -> walk_02.     <- for us: use, cycle, what the game adds

Attach `01_official_crouch_visor_up.png` and `10_model_sheet.png`.
<fenced prompt>
```
The line above the prompt is for Claude and the user, never pasted: which moves use the frame and what the game
draws on top ("The game adds the teal smear behind it"); for a hit frame, the reach the move needs ("the kick's ball
ends about one body length in front of him": a limb drawn longer than that makes the hit reach further, since many
games measure reach from the drawing). It makes review faster.

## 3. The prompt, part by part

1. **Name what each attached image shows.** "The attached images are my game character, X from Y: the first image
   shows him crouched, ready to run (three-quarter view facing right), the second is his model sheet from every side."
   An approved frame attached as a helper: "The second image is a pose of him you drew for my game; it shows his four
   arms clearly."
   **Stills of a pose (one rule):** attach a still only if its view matches the game's and it shows nothing the game
   draws itself (spray, smears, a victim, a build that differs); then "like the third attached image, which shows the
   pose; keep the colours of the first image". Otherwise describe the still's pose in words and don't attach it.
2. **One pose, on a canvas shaped like the pose:** "Draw him ONCE, as ONE NEW pose, in a WIDE image (3:2, 1536x1024)."
   - WIDE 3:2: runs, lunges, kicks, dives, lying down, spread wings, long tails held out.
   - TALL PORTRAIT 2:3: tall upright figures, uppercuts, wall climbs, being held up.
   - SQUARE 1:1: compact poses (block, hurt, stun, jump).
   A tall thin figure on a square or wide canvas comes back squashed.
3. **"Draw a new pose, don't copy the poses of the attached images."**
4. **The POSE paragraph, limb by limb.** Which limb, where, how bent, where the weight is, which feet touch the
   floor, the head and gaze, then tail / cape / hair. Name limbs **near / far** (to the viewer) or **by their
   markings** ("the leg with the black speaker panel"), never left / right: the game mirrors and the model confuses
   them. A bare verb ("walking", "blocking") gives a pose close to the idle. For the second frame of a pair, put the
   swapped limbs in CAPS ("his FAR leg reaching forward ... his NEAR leg pushed back"). For a hit, say how far the
   striking limb stretches (the reach in the frame's use line). For anything the game draws
   (a victim, a wall): "don't draw them: leave the space around his neck empty".
5. **The shared build-and-colours block, written out in full in every prompt**, so each prompt can be pasted alone
   (never "same as above"):
   - "Keep him EXACTLY the same size, build and proportions as in the attached images: <the build in words>."
   - "Do not make him <the drifts>." Name the drift *away from* this character's build: a slim one comes back
     bulkier, a bulky one leaner, a tall thin one shorter. Models pull toward an average body.
   - Counts and absences: "He has exactly FOUR legs, never more", "NO EYES: never draw eyes".
   - Every colour by name and where it goes, anchored to a picture: "muted TEAL (blue-green, as in the first attached
     image, not bright cyan) on his forearms and hands".
   - Every marking: the emblem and its colours, claws per hand, the feet, tail bands.
   - "Black outlines as thin as in the attached images. Flat cartoon cel shading like <the style>."
6. **Form variants as alternative sentences.** If the character has forms (visor up / down, cloak / wings), keep two
   versions of the block that differ only in the form sentence, and mark every prompt with its form (U / D).
7. **The view sentence:** "Three-quarter view facing right, like the first attached image." (Pick the game's facing
   once; the game mirrors.) Special frames change only this sentence: "Seen from the side, lying on the floor."
8. **"Full body, tail included, nothing cut off."**
9. **No effects, no floor shadow:** "No effects (no speed lines, motion blur, afterimages, smears, dust, wind or
   stars), no shadow on the floor, no ground or scenery." Add what the game draws for this character, with the
   reason: "No drool or saliva (my game draws it)." The reason makes the model comply more often.
10. **Background:** "Transparent background (PNG); if you can't make it truly transparent, a plain white background
    instead, never a checkerboard pattern." (One model painted a grey-and-white checkerboard as "transparency".)
    - Transparent is best. Fallback: **white** for dark characters, **magenta #FF00FF** for white or pale ones.
    - A dark character with white parts (a white chest panel): white is safe when every white part is closed in by
      outlines; if white reaches the silhouette's edge or shows in a gap between limbs, use magenta.
    - **Never black** (outlines and dark parts can't be cut from it), **never a colour the character uses**
      (Omni Clash: never green, because every alien wears the green Omnitrix).

### Example: a complete body prompt (XLR8, `walk_01`)
```
The attached images are my game character, XLR8 from the original Ben 10 cartoon (2005): the first image shows him
crouched, ready to run (three-quarter view facing right), the second is his model sheet from every side (top row
with his visor up, bottom row with his visor down). Draw him ONCE, as ONE NEW pose, in a WIDE image (3:2,
1536x1024). Draw a new pose, don't copy the poses of the attached images.

POSE: jogging fast, the reach: leaning well forward; his near leg reaching forward, the ball under its foot just
touching the floor ahead of him; his far leg pushed back behind him, its ball lifted off the floor; his far arm
swung forward and his near arm swung back, the claws pointing back; his head and helmet crest forward; his tail held
straight out behind him, level, for balance.

Keep him EXACTLY the same size, build and proportions as in the attached images: a slim, raptor-like alien with a
long neck, a narrow chest, long thin arms, long thin bird-like legs and a long, thick tail as long as his body. Do
not make him bulkier, shorter, more human or bigger-headed. Same colours and style: a mostly BLACK body with
lavender-grey highlight bands along its edges; muted TEAL (blue-green, as in the first attached image, not bright
cyan) on his forearms and hands, [... every marking ...]. VISOR UP: his face shows, a teal mask with lime-green
eyes, as in the first attached image. Black outlines as thin as in the attached images. Flat cartoon cel shading
like the 2005 show. Three-quarter view facing right, like the first attached image. Full body, tail included,
nothing cut off. No effects (no speed lines, motion blur, afterimages, smears, dust, wind or stars), no shadow on
the floor, no ground or scenery. Transparent background (PNG); if you can't make it truly transparent, a plain white
background instead, never a checkerboard pattern.
```
(The real file writes the bracketed part out in full in every prompt.)

## 4. Conventions that keep a roster consistent
- **Down:** on his back, head on the LEFT, feet on the right, like every other fighter's down frame.
- **Held / choked:** "held up off the floor by the neck by someone much bigger (don't draw them: leave the space
  around his neck empty)".
- **Grabs and carries:** drawn without the victim; the game places the victim's own hurt frame.
- **Walls:** "a vertical wall that runs along the LEFT edge of the image ... The wall is NOT drawn: the balls of his
  feet touch the left edge of the image", head turned right toward the arena; the game mirrors for the other wall.
- **Jump:** one frame for rising and falling, so it must read both ways.
- **Walk cycles:** seen from the side two stride frames look alike. Either three frames, reach / passing (legs
  together, one knee up) / other reach, looped 01 -> 02 -> 03 -> 02; or two new frames with the idle as the
  in-between, 01 -> idle -> 02 -> idle.
- **Pose stills in other colours:** "like the fourth attached image, which shows the pose; keep the colours of the
  first image, not the fourth's brighter cyan".

## 5. Variants made as an edit of an approved frame
A frame that is an approved frame with one change (the block's crossed arms, the same with the mouth open for a
roar) is asked for as an edit, attaching the approved frame: "Edit the attached image: keep the pose, size, colours,
outline and background exactly the same; change only this: his mouth wide open in a roar, showing his teeth." This
is the one time an edit is wanted; for a new pose, editing the reference is the failure (section 7).

## 6. The fallback line ("If a try comes back with X")
Under the shared block, one line per known failure, so the user can retry without asking Claude:
> **If a try comes back with X,** ask again with this line added at the end: "Look again: ..."

Examples:
- XLR8: "Look again: the Omnitrix is grey and black with no green, each foot is teal claws gripping a grey ball, and
  the teal is the muted blue-green of the first attached image."
- Wildmutt: "Look again: he has NO eyes at all, and exactly four legs."
- Spidermonkey: "Count again: he must have four arms with four clawed hands and two legs with two clawed feet, six
  limbs in all."
- Big Chill (two forms): "Look again: his cloak is closed around him, no wings and no antennae."

When the same fix is needed on two frames, move it into the shared block for every later prompt.

## 7. What image models get wrong, and the wording that fixed it
| They tend to... | What fixed it |
|---|---|
| Draw the character bulkier, shorter, more human, bigger-headed (or a bulky one leaner) | Build in words + "Do not make him ..." in every prompt; the idle attached first; a canvas shaped like the pose. Numbers ("18 heads tall") are ignored. |
| Squash a tall figure | One pose per image on a TALL PORTRAIT canvas. Goop: two poses per wide image came back ~13 emblem-widths tall against 18; one pose on 2:3 matched on the first try. |
| Thicken the outline (~20%) | "Black outlines as thin as in the attached images." |
| Copy a reference pose | "Draw a new pose, don't copy the poses of the attached images." Describe a still in words instead of attaching it when its build differs (an upright two-legged leap still would have made an all-fours character stand up). |
| Edit a reference instead of drawing anew | "Draw him ONCE, as ONE NEW pose"; a new chat. (Gemini once moved a panel on the attached frame and returned it.) |
| Draw two frames of a pair the same (strides, climb steps, two punches) | CAPS on the swapped limbs. Retry: attach the first frame, "Draw the NEXT step of the same climb, with every limb in the OTHER position", or "You already drew him swiping one arm straight forward; this pose must look clearly DIFFERENT". Or change the move so the outlines differ (an overhead slash after a straight swipe). |
| Add or drop limbs (three arms, a seventh leg, five arms in a block) | A count line ("Count the arms: exactly TWO raised, exactly TWO on the floor. Four in all, never five."); attach an approved frame that shows every limb clearly as a second image. |
| Add features he lacks (eyes on an eyeless face, a second emblem) | Say it in the block ("NO EYES: never draw eyes"); a fallback line. |
| Draw what the game draws (spider legs, drool, a floating disc, webs, speed smears) | "Draw no X (my game draws it)". Never attach a reference showing X: erase it from the reference first (Ultimate Spidermonkey's idle had its spider legs erased before it was attached). |
| Get colours wrong (a brighter render, a forbidden colour) | Colours by name, place and picture ("as in the first attached image, not bright cyan"). A small, consistent drift is matched at fitting rather than retried. |
| Paint a checkerboard for "transparent" | "... a plain white background instead, never a checkerboard pattern." |
| Reuse a character drawn earlier in the chat | A new chat per character. |
| Add speed lines, dust, glow, floor shadows | The no-effects sentence, listing them. |

The older "two poses side by side in one image" rule was dropped: the poses squashed each other and drifted together.

## 8. Effect sheets (pieces, not a character)
- **First decide how the game will animate the sheet** (pieces stacked into a column, scrolled, flipped, scaled,
  spun, played in order): that decides the pieces and how they must match (a stacked tornado needs bands whose edges
  meet; a played-in-order puff needs growing stages). Write it in the sheet's use line.
- **One sheet per family** (tornado, dust, sonic boom, ice, drool), pieces in a grid **in the prompt's order**,
  numbered: "Top row, left to right: 1. ...; 2. ... Bottom row, left to right: ...". "Each piece with plenty of
  empty magenta space around it (no two pieces touch)": a script cuts them by grid position and names them.
- Give each piece's shape and proportions ("a flat band of wind about five times as wide as it is tall").
- Pieces the game combines must be told to match ("Pieces 1 to 3 must look like slices of the same tornado, so my
  game can stack them into one spinning column").
- **Solid effects** (dust, dirt, ice, goo, webs, a painted tornado): **magenta #FF00FF**. "Draw the dust SOLID and
  opaque, never see-through, so no magenta shows through any piece (my game makes it see-through itself)."
- **Light effects** (glows, flashes, shock rings, soft smoke, mist, breath): **pure black #000000**, drawn by the
  game additively, where black disappears. "Soft bright white and pale cyan light, brightest in the middle of each
  piece and fading softly to nothing at its edges, no hard outlines." Soft smoke on magenta turns pink at its edges;
  on black it needs no cutting at all.
- End with "Nothing else in the image: no character, no ground", the background sentence ("and magenta in every
  gap"), the canvas, "nothing cut off".
- Effects drawn by code (smears, streaks, speed lines, see-through phasing) get no picture: list them in the plan.

Example (XLR8 `boom_sheet`, light on black, opening):
```
Draw a game effect sheet for my Ben 10 fighting game (the original 2005 cartoon's style), not a character: THREE
separate pieces of a sonic boom, in one row, each piece with plenty of empty black space around it (no two pieces
touch). Left to right: 1. a sonic boom ring: a bright ring of shock-compressed air seen at an angle, a thin oval ring
about twice as tall as it is wide, thicker and brighter on its near side; 2. a cone of air: ...
```

## 9. Lessons
Add one line here after every character: a wording that fixed a mistake, a check that caught something, a step that
saved a round. Date it and name the character, so the reason stays clear.
- 2026-10-29 (from six Omni Clash characters): everything above.
