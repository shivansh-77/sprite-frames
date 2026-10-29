# Review checklist: when a round of frames comes back

Look at every try of every frame, at full size and at game size, next to the idle. Measure what can be measured
(scale, overlap, colours, alpha); judge the rest by eye. Examples are from the Omni Clash project's "Made so far"
notes (`docs/characters/*.md`).

## Per frame
1. **Likeness and build vs the idle.** Scale the frame to the idle by an anchor (head width, the emblem, eye span or
   the drawn area, square-rooted), then compare side by side: head size, limb length, bulk, neck, tail.
   - Anchors can lie: a model drew the emblem ~17% bigger relative to the body than the official art, and drew eyes
     as big glowing rings where the idle has slits. When two anchors disagree, use the one that matches by eye, or
     average them.
   - A frame drawn with a small head on a tall body (Goop's hurt) sized by the face comes out +25% too big: size
     upright poses by height instead, bent or shaped poses by the anchor.
2. **Count limbs, fingers, claws, eyes, emblems.** Count up close, every try. Seen so far: a jump with three arms (one
   growing from behind the head), a block with five arms, a seventh leg under a thigh, two Omnitrix dials (one per
   shoulder), eyes added to an eyeless face. A limb hidden behind the body is fine; one that's missing or extra is not.
3. **Colours.** Sample the main tones against the idle. A whole batch brighter or more saturated than official art
   (Spidermonkey's blue, Wildmutt's orange) is matched tone by tone at fitting, once, not retried. Check the forbidden
   colours (Omni Clash: no green emblem on XLR8) and form markers (visor up = eyes showing; visor down = no eyes).
4. **Outline thickness:** outline width ÷ head width, against the idle's. Thicker = retry with the thin-outline line.
5. **Background, transparency, edges.**
   - Real alpha, or a painted checkerboard? (One "transparent" PNG was RGB with grey and white squares: flood it out
     from the edges, then ask for plain white in every later prompt.)
   - Alpha 250-254 inside the body is normal for these models: round >= 250 up to 255.
   - Cut from white: defringe the light rim, then check enclosed gaps (between claws, between limbs) and pale parts
     (teeth, highlights, a white dial) by eye; the script can't tell them apart.
   - Cut from magenta: un-mix the pink from the edge pixels; check nothing pink is left.
   - Look at it on a dark background and on the game's real backgrounds.
6. **Cut off at the picture edge?** Find the drawn area's bounds. A soft outline rim touching the edge is fine; a
   claw tip, tail or foot sliced flat is a retry.
7. **Pose matches the prompt,** limb by limb: weight and contact with the floor, facing, view, head direction.
   Roster conventions: down lies head-left; wall frames stand on the picture's left edge, head turned right; grab
   frames leave the victim's space empty.
8. **Nothing the game draws:** no effects, floor shadow, drool, webs, extra parts the engine adds.
9. **Reads at game size.** Shrink it to its real on-screen size on the game's background: does the silhouette say
   what the move is?
10. **Size vs the idle after fitting:** within ~10% looks the same in play; more shows as the character growing or
    shrinking between frames.
11. **Drawn reach.** If the engine takes hit reach from the drawn extents, a long arm or tail in the art is long reach
    in play. Flag it to the user (Goop's stretch jab came out 1.8x the reference fighter's reach; kept and balanced
    with recovery and damage).
12. **Near-duplicates.** Align two frames on the anchor and measure how much their silhouettes overlap. Spidermonkey:
    attack_02 overlapped attack_01 74% (the same swipe: retried as an overhead slash); wall_climb_02 60% (retried,
    45% kept).
13. **Frames that add nothing:** a pose another frame already covers, or motion the code makes (a walk from a bob and
    sway, a landing from a dip). Don't install it; note it as unused (kept for a win pose or intro, maybe).
14. **Names:** a sheet or piece must not take a pose's name (XLR8's boom sheet first overwrote the `boom` punch pose:
    renamed `boom_fx`).

## Per move
- **Play the move's frames in order** at game size (a contact strip or a scratch GIF): wind-up, hit, recovery. Does
  it read as one action, and does each hit of a combo use a different limb or silhouette?
- **Pairs and cycles alternate visibly** (walk strides, climb steps, wing beats). If they don't, retry the second one
  with the first attached ("draw the NEXT step, every limb in the OTHER position").
- **A missing frame** (a move that jumps from wind-up straight to recovery, a hit with no contact pose) gets a new
  prompt (➕) in the right section of the prompts file.
- **Shared frames work for every move that uses them** (a jump frame shown rising and falling; a punch reused in a
  flurry and a dash strike). Check the frame plan's "used by" list.
- **Effects:** every piece present, apart, in the order asked; the right background (solid on magenta, light on black);
  pieces meant to stack really match.

## Verdicts
Write them into the master prompts file (then run `sync_prompts.py`): the **Status** table row first (it is what
Codex reads), then under the frame's heading:
- **✅ approved:** Status ✅ with the try (`walk_01_try2`) and a short note; under the heading anything to remember at
  fitting ("the tail is held straight out, so the frame is wide"). Its `file` goes into `sprite_frames.json`.
- **🔁 redraw:** Status 🔁 with what's wrong in a few words; under the prompt one line,
  `**Fix (try 2), add at the end:** "..."`. If the pose itself has to change, rewrite the prompt and say so in the
  Note.
- **➕ new frame:** a Status row marked ➕ and a new section with its prompt, where a move needs it.

How to decide:
- **Approve clear ones yourself.** Ask the user only about doubtful ones, with the evidence (side-by-side at game
  size, the numbers). The user can veto any pick, which sends it back to rework.
- **Fix by hand instead of retrying** when the flaw is small and stands apart: a stray limb erased and the outline
  redrawn, a second emblem painted over with the fur tones. Keep the original; save the fix as `<name>_fixed`.
- **The same flaw on two or more frames** means the shared block is missing a line: fix the block and the fallback
  lines, not each frame.
- Keep every raw try until the character is finished (never overwrite; tries are `<frame>_try<N>.png` in
  `<char>_codex/`); then only the rejected tries are deleted, with the user's OK.

## The good-enough rule
Frames on screen for only a few milliseconds (jabs, kicks, skids, slams, climb steps, a finisher, a hit reaction):
keep the best try instead of chasing retries. Retry only when the flaw is plain to see in play (an arm growing out of
the head), not for a hidden limb or a pose that's merely close to its partner. When two tries exist, keep the one that
serves the frame's job better (the one that differs more from its partner in a cycle).

Examples:
- XLR8's walk_01 and walk_03 came out almost the same pose: fine for a fast jog seen from the side, no retry.
- Spidermonkey's wall_climb_02 retry still overlapped 45%: kept ("a frame seen for a few ms, no one is going to
  notice", the user).
- A stun pose standing steadier than asked: the face and the game's stars sell it; kept.
