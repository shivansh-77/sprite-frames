# <Game>: art style

Written once at the start of the game, before the first character's prompts. Every character's prompts follow it, so
the whole cast looks like one game. The first character is the style test: change this file until its pilot frames
look right, then keep it.

## The look
- **Lines:** <thin black outlines | coloured lines | none>; how thick compared to the head (e.g. "about 1/40 of the
  head's width").
- **Shading:** <flat cel shading, one shadow tone | soft painted | pixel art>; where the light comes from.
- **Colours:** <saturated cartoon | muted | limited palette>; anything never used (e.g. a colour the UI or an effect
  owns).
- **Proportions:** <how stylised: big heads or realistic, chunky or slim>.
- **View:** <three-quarter view facing right | side view | front>; every frame faces the same way (the game mirrors).
- **Detail:** <how much: readable at game size, which is about <N> px tall on screen>.

## The pictures
- **Background:** transparent PNG; else plain <white | magenta #FF00FF> (never black, never a colour a character
  uses). Light effects (glows, flashes) as light on black, drawn additive in the game.
- **What the game draws, not the frames:** <floor shadows, motion blur, speed lines, dust, hit sparks, ...>.
- **Canvas shape:** like the pose (wide for runs and kicks, tall for jumps and uppercuts).

## The style block
Every body prompt includes this sentence (inside its shared block, before the view sentence; the view itself stays
out of it, since special frames change only the view sentence):
```
<e.g. "Black outlines as thin as in the attached images. Flat cartoon cel shading like the 2005 show.">
```

## Style references
Approved frames that show the style (attach one to a new character's first prompts, so the cast matches):
- <first character's idle, once ✅>
