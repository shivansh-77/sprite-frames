# Drawing character frames (instructions for Codex)

This folder holds each character's art: `<char>/<char>_reference/` (pictures to work from), `<char>/<char>_codex/`
(the frames you draw) and `<char>/<char>_prompts.md` (what to draw). **Your only job here is drawing pictures.**
Never change code, settings, the prompts files or any file other than the pictures you save.

When asked to draw a character's frames (e.g. "draw the frames for big_chill"):
1. Open `<char>/<char>_prompts.md`. Its **Status** table lists every frame.
2. Draw every frame marked ⬜, 🔁 or ➕. Skip ✅ (approved) and ⏸ (waiting for another frame). If asked for the pilot,
   draw only the frames marked **pilot**.
3. For each frame: use the pictures its section says to attach (from `<char>/<char>_reference/`, or approved frames
   from `<char>/<char>_codex/`) and its prompt exactly as written. If a **Fix** line sits under the prompt, add that
   line at the end of the prompt.
4. One picture per frame, one pose per picture, in the shape the prompt asks for (wide, tall or square).
5. Save it in `<char>/<char>_codex/` as `<frame>_try<N>.png`, N one higher than the highest try of that frame already
   there (the first is `_try1`). **Never overwrite, rename or delete a file.**
6. A transparent PNG background when you can; otherwise the plain background colour the prompt names. Never a
   checkerboard drawn into the picture.
7. When you're done, list the files you saved and any frame you couldn't draw, and why.

Claude reviews every round, keeps the Status table and writes the Fix lines; the user decides.
