# Design questions: the talk before any prompt

No prompt is written until the character's look, every move and the frame plan are agreed. The design is a doc in
the project (one per character); the frames file is written from it.

**A model to copy:** the Omni Clash project's `docs/characters/xlr8.md`: Identity, a powers-to-moves table, a stats
table against the roster, Signature mechanics, a basic-attack table, a specials table (keys, engine, cost, what it
does, how to beat it), then **Art plan** (the reference pictures table, "His look", Rules, Made so far, Frame list),
Decisions and Open questions. Mark what the user settled "(user, date)" and Claude's suggestions "(proposal)".

## 1. References first
Ask the user for reference pictures before the questions; they change the answers.
- **Most useful:** official art of the rest pose (often good enough to be the idle as it is), a **model sheet from
  every side** (build and markings), one picture per form (visor up / down, cloak / wings), stills of the signature
  moves and effects.
- Save them in a references folder, numbered, and keep a table: **file / what it shows / use** (which frame or
  effect it informs).
- From them write **"His look"**: build, colours by name with sampled values, every marking (emblem, claws per hand,
  feet, tail bands). This becomes the shared block of every prompt.
- Decide which official pictures become frames as they are (mirrored to face the game's way), and which need
  cleaning before they're attached: anything the game will draw itself (Ultimate Spidermonkey's spider legs, Goop's
  floating disc) is erased from the reference first, or the model draws it in every frame.
- Note where references disagree (a brighter render, a different colour) and which one rules.

## 2. Rounds of questions
Three or four rounds, a few questions each. Every question comes with options and Claude's pick, and the user's
answers are written into the design doc as they come.
1. **Role and fighting style:** what is he for, what is the roster missing, his matchups, his weakness. Size and
   weight against the others (XLR8: "as tall as Rath", the lightest body).
2. **Powers to moves:** list the source's powers (the user can paste a wiki list) and map each to a move, a mechanic
   or a look, or "not used".
3. **Movement:** the walk (a jog, a scuttle, a lope, a hover glide; how many frames and the loop order), run or dash,
   jump (one frame?), landing, special movement (walls, flight, phasing, a second form), and how each looks.
4. **Basic attacks:** how many hits, which limb each uses (different limbs read as different hits), the last hit's
   reaction; air attacks; the dash attack.
5. **Specials:** each with its input, what it does, how to beat it, and whether it needs frames of its own or reuses
   others.
6. **The super:** the big one; how it starts, what the victim sees, how it ends.
7. **Defence and getting hit:** block, hurt, stun, knocked down, grabbed, and any status looks (frozen, webbed).
8. **Signature mechanics and looks:** what makes him play differently, and which looks the code draws (smears,
   afterimages, see-through phasing, drool) versus pictures.

**Every move is confirmed by the user, the walk included.** A walk is the frame on screen most; agree its style and
cycle before drawing it.

## 3. The frame plan
Only once every move is agreed. In the design doc, under Art plan -> Frame list:
- **Each move mapped to its frames, 1 to 5 per move**: key poses, not animation sheets. The engine adds motion
  (lunges, afterimages, shake, squash and stretch), so a combo step is usually one frame.
- **Start from the reference table's Use column:** every picture assigned to a frame, an effect or "not used"
  before the plan is drawn up (an official still often is a frame's pose).
- **Group them:** official (used as they are), core (walk, jump, defend, hurt, stun, down, held; a land frame only if
  the landing pause is long enough to see, about 100 ms or more), combo, air, specials, wall, effects. Give each frame
  its pose in a phrase ready to go into the prompt, and its uses.
- **Share frames between moves** wherever the pose fits, and list them: "Reused, no new picture: Blur Barrage =
  attack_01 / attack_02 / attack_04 smeared; the running strike = attack_04".
- **A shared frame in the wrong form** (a visor-up kick reused in a visor-down speed move): fine if it's on screen
  only briefly; otherwise a form variant made as an edit of the approved frame. Ask the user which.
- **Variants of an approved frame** are made as an edit of it, not a new drawing: arms crossed in an X for the
  block; the same with the mouth open for a roar.
- **Form per frame:** with forms, mark each frame (XLR8: U = visor up at rest, D = visor down at speed; 15 U, 11 D).
- **Canvas shape per frame** (wide, tall, square), and the **pilot frames** to bring back first.
- **Effects in the same plan:** each sheet's pieces, its background (solid on magenta, light on black), and the list
  of looks drawn by code with no picture.
- **What the code does instead of a frame** (a walk from a bob, a short landing from a dip): note it, and add
  frames only if it looks stiff in play.
- **Effects:** decide how the code animates each sheet (stacked, scrolled, scaled, played in order) before its
  pieces are chosen.
- A total at the top: "1 official + 25 from ChatGPT + 3 effect sheets".

Example (XLR8, abbreviated):
```
- Official, used as it is (1): idle (picture 1), U.
- Core (10), U: walk_01 / walk_02 / walk_03 (reach, passing, the other reach; 01 -> 02 -> 03 -> 02), jump, land,
  defend, hurt (picture 8), stun, down (on his back, head on the left), choked (held up by the neck).
- Speed (3), D: blur (the blur step, the run, Blur Strike), skid, air_blur.
- Combo (4), U: attack_01 (jab), attack_02 (cross), attack_03 (tail whip), attack_04 (spinning heel kick).
- Effects (3 sheets): tornado and dust on magenta, the sonic boom on black (drawn as light).
- Reused, no new picture: Cyclone = blur circling; Time Blur's hits = attack_01-04 and the blur.
```

Then write the prompts file (`prompt_recipe.md`), one prompt per new frame, in the plan's order and groups.
