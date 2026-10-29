"""Review pictures of fitted sprite frames, the way the game will show them.

The sheet: each frame next to the idle, both at game size (x the character's `game_scale`) on the game's background
(`review_background`), their origins (the bottom centre of the canvas, where the game anchors a frame) on one floor
line with a small red mark, the frame name above and a verdict under it. Verdicts come from a JSON file
`{"frame": "text"}`; the first word picks the dot's colour: OK / GOOD / PASS / KEEP = green, REDO / BAD / FAIL / NO /
REJECT = red, anything else (?, CHECK, DOUBT, ASK...) = amber. Dots are drawn, not emoji (Pillow's fonts often can't).

The animation (`--anim a,b,c`): an animated GIF of a sequence at the settings' `fps`, every frame anchored on its
origin on the background at game size, so problems that only show in motion can be seen (a walk cycle, a combo).

    python review_sheet.py --settings sprite_frames.json --char xlr8 --frames walk_01,walk_02 --out sheet.png
    python review_sheet.py --settings S --char xlr8 --verdicts verdicts.json --out sheet.png      (every frame)
    python review_sheet.py --settings S --char xlr8 --anim walk_01,walk_02,walk_03,walk_02 --gif walk.gif

Frames are read from `--dir` (default `sprites_dir`) by `sprite_name`; the idle is that folder's `idle` frame.
The sheet is made when `--frames` is given or `--anim` isn't; `--anim` alone makes only the GIF. Its width is chosen
to make it about 4:3 (or `--width`); about 6-12 frames per sheet stay readable when the picture is shown scaled down.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True                       # no __pycache__ next to the skill's scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf_settings import load  # noqa: E402

PAD = 14            # inside each cell
GAP = 18            # between the idle and the frame
TEXT = (225, 228, 238)
DIM = (150, 156, 175)
RED_MARK = (235, 60, 60)
DOTS = {'green': (70, 200, 90), 'amber': (240, 175, 40), 'red': (230, 60, 60)}
GREEN_WORDS = {'OK', 'GOOD', 'PASS', 'FINE', 'KEEP', 'APPROVED', 'YES'}
RED_WORDS = {'REDO', 'BAD', 'FAIL', 'NO', 'REJECT', 'WRONG', 'RETRY'}


def font(size):
    for name in ('arial.ttf', 'segoeui.ttf', 'DejaVuSans.ttf', 'Arial.ttf', 'Helvetica.ttc', 'LiberationSans-Regular.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size)
    except TypeError:          # Pillow older than 10.1: a fixed bitmap font
        return ImageFont.load_default()


def shade(colour, amount):
    """The background a little lighter (amount > 0) for lines and frames on it."""
    return tuple(int(min(255, max(0, c + amount))) for c in colour)


def verdict_colour(text):
    word = re.match(r'\s*([A-Za-z]+)', text or '')
    word = word.group(1).upper() if word else ''
    return 'green' if word in GREEN_WORDS else 'red' if word in RED_WORDS else 'amber'


class Sprite:
    """A fitted frame at game size, cropped to its drawing, with its origin's place in the crop."""

    def __init__(self, path, scale, alpha_floor):
        im = Image.open(path).convert('RGBA')
        w, h = im.size
        if scale != 1:
            im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        sw, sh = im.size
        alpha = np.asarray(im)[..., 3] > alpha_floor
        rows, cols = np.flatnonzero(alpha.any(axis=1)), np.flatnonzero(alpha.any(axis=0))
        if len(rows) == 0:
            rows, cols = np.array([sh - 1]), np.array([sw // 2])
        x0, x1, y0, y1 = int(cols[0]), int(cols[-1]) + 1, int(rows[0]), int(rows[-1]) + 1
        self.image = im.crop((x0, y0, x1, y1))
        self.ox, self.oy = sw / 2 - x0, sh - y0               # the origin, in the crop's pixels
        # how far the drawing (and the origin mark) reaches left, right and up from the origin
        self.left = max(self.ox, 8)
        self.right = max(self.image.width - self.ox, 8)
        self.up = max(self.oy, 8)
        self.down = max(0, self.image.height - self.oy)        # nothing for a frame anchored at its canvas bottom

    def paste(self, canvas, x, floor_y):
        """Draw with the origin at (x, floor_y)."""
        canvas.alpha_composite(self.image, (round(x - self.ox), round(floor_y - self.oy)))


def origin_mark(draw, x, y):
    x, y = round(x), round(y)
    draw.line([(x - 6, y), (x + 6, y)], fill=RED_MARK, width=2)
    draw.line([(x, y - 5), (x, y + 7)], fill=RED_MARK, width=2)


def wrap(draw, text, fnt, width):
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}'.strip()
        if line and draw.textlength(trial, font=fnt) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + ([line] if line else [])


def make_sheet(names, sprites, idle, verdicts, bg, out, title, max_width):
    name_font, small, verdict_font, head_font = font(17), font(12), font(14), font(15)
    measure = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    line_h = 18

    cells = []
    for name in names:
        sp = sprites[name]
        pair = ([idle] if idle else []) + [sp]
        width = sum(p.left + p.right for p in pair) + GAP * (len(pair) - 1) + 2 * PAD
        width = max(width, measure.textlength(name, font=name_font) + 2 * PAD, 170)
        text = verdicts.get(name, '')
        lines = wrap(measure, text, verdict_font, width - 2 * PAD - 16) if text else []
        cells.append({'name': name, 'pair': pair, 'width': int(np.ceil(width)), 'text': text, 'lines': lines})

    def flow(width):
        """The cells in rows no wider than `width`, each row with its top, the height above its floor and its height."""
        rows, row, used = [], [], 0
        for c in cells:
            if row and used + c['width'] > width:
                rows.append(row)
                row, used = [], 0
            row.append(c)
            used += c['width']
        rows.append(row)
        layout, y = [], 58                      # below the title and the legend
        for row in rows:
            up = max(p.up for c in row for p in c['pair'])
            down = max(p.down for c in row for p in c['pair'])
            n_lines = max([len(c['lines']) for c in row] + [1])
            h = int(PAD + 22 + up + max(down, 10) + 8 + n_lines * line_h + PAD)
            layout.append((row, y, up, h))
            y += h
        return layout, max(max(sum(c['width'] for c in row) for row in rows), 640), y

    if max_width:
        layout, sheet_w, y = flow(max_width)
    else:
        # no width given: the one that makes the sheet closest to 4:3, so it stays readable when shown scaled down
        tries = [flow(w) for w in range(1000, 3401, 100)]
        layout, sheet_w, y = min(tries, key=lambda t: abs(t[1] / t[2] - 4 / 3))
    canvas = Image.new('RGBA', (sheet_w, y), tuple(bg) + (255,))
    draw = ImageDraw.Draw(canvas)

    draw.text((PAD, 10), title, font=head_font, fill=TEXT)
    legend_x = PAD
    for colour, label in (('green', 'OK'), ('amber', 'doubtful'), ('red', 'redo')):
        draw.ellipse([legend_x, 38, legend_x + 10, 48], fill=DOTS[colour])
        draw.text((legend_x + 15, 35), label, font=small, fill=DIM)
        legend_x += 30 + measure.textlength(label, font=small)
    note = 'red cross = origin (bottom centre of the canvas)' + ('; left of each pair: the idle' if idle else '')
    draw.text((legend_x + 10, 35), note, font=small, fill=DIM)

    line_colour, frame_colour = shade(bg, 40), shade(bg, 22)
    for row, top, up, h in layout:
        x = 0
        for c in row:
            draw.rectangle([x, top, x + c['width'] - 1, top + h - 1], outline=frame_colour)
            draw.text((x + PAD, top + PAD - 4), c['name'], font=name_font, fill=TEXT)
            floor_y = top + PAD + 22 + up
            draw.line([(x + 6, floor_y), (x + c['width'] - 7, floor_y)], fill=line_colour, width=1)
            px = x + PAD
            for i, sp in enumerate(c['pair']):
                ox = px + sp.left
                sp.paste(canvas, ox, floor_y)
                origin_mark(draw, ox, floor_y)              # after the drawing, so it shows on top
                if idle and i == 0:
                    draw.text((ox + 10, floor_y + 4), 'idle', font=small, fill=DIM)
                px = ox + sp.right + GAP
            ty = floor_y + max(p.down for p in c['pair']) + 18
            if c['text']:
                draw.ellipse([x + PAD, ty + 4, x + PAD + 10, ty + 14], fill=DOTS[verdict_colour(c['text'])])
                for k, line in enumerate(c['lines']):
                    draw.text((x + PAD + 16, ty + k * line_h), line, font=verdict_font, fill=TEXT)
            x += c['width']
    canvas.convert('RGB').save(out)
    return canvas.size


def make_gif(names, sprites, bg, fps, out):
    small = font(13)
    left = max(sprites[n].left for n in names)
    right = max(sprites[n].right for n in names)
    up = max(sprites[n].up for n in names)
    down = max(sprites[n].down for n in names)
    margin = 24
    w, h = int(left + right + 2 * margin), int(up + down + 2 * margin + 20)
    ox, floor_y = margin + left, margin + 14 + up
    frames = []
    for i, name in enumerate(names):
        im = Image.new('RGBA', (w, h), tuple(bg) + (255,))
        draw = ImageDraw.Draw(im)
        draw.line([(0, floor_y), (w, floor_y)], fill=shade(bg, 40))
        sprites[name].paste(im, ox, floor_y)
        origin_mark(draw, ox, floor_y)
        draw.text((8, 6), f'{i + 1}/{len(names)}  {name}', font=small, fill=DIM)
        # flat cartoon colours: an exact palette per frame without dithering noise
        frames.append(im.convert('RGB').quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=round(1000 / fps), loop=0, disposal=2)
    return w, h


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--settings', help='sprite_frames.json (default: looked for in this folder and its parents)')
    ap.add_argument('--char', required=True)
    ap.add_argument('--frames', help='a,b,c for the sheet (default: every frame of the character in the settings)')
    ap.add_argument('--dir', help='the fitted frames folder (default: sprites_dir)')
    ap.add_argument('--verdicts', help='JSON {"frame": "OK" / "REDO: third arm" / "? the tail"...}')
    ap.add_argument('--out', help='the sheet PNG (default: <char>_review.png here)')
    ap.add_argument('--width', type=int, help='the widest a row of the sheet may be, px (default: what makes the '
                                              'sheet about 4:3)')
    ap.add_argument('--anim', help='a,b,c: frames of an animation in order (repeats allowed)')
    ap.add_argument('--gif', help='the animation GIF (default: <char>_anim.gif here)')
    args = ap.parse_args()

    s = load(args.settings)
    char = s.char(args.char)
    scale, bg, floor = char['game_scale'], s['review_background'], s['alpha_floor']

    def path(name):
        if args.dir:
            return Path(args.dir) / s['sprite_name'].format(char=args.char, frame=name)
        return s.sprite_path(args.char, name)

    names = args.frames.split(',') if args.frames else list(s.frames(args.char))
    anim = args.anim.split(',') if args.anim else []
    make_sheet_now = bool(args.frames) or not anim

    sprites, missing = {}, []
    for name in dict.fromkeys((names if make_sheet_now else []) + anim + ['idle']):
        p = path(name)
        if p.exists():
            sprites[name] = Sprite(p, scale, floor)
        elif name != 'idle':
            missing.append(name)
    if missing:
        print('missing (left out): ' + ', '.join(f'{n} ({path(n)})' for n in missing))
    idle = sprites.get('idle')
    if not idle:
        print(f'no fitted idle at {path("idle")}: the sheet shows the frames alone')

    if make_sheet_now:
        verdicts = json.loads(Path(args.verdicts).read_text(encoding='utf-8')) if args.verdicts else {}
        shown = [n for n in names if n in sprites]
        if shown:
            out = args.out or f'{args.char}_review.png'
            title = f'{args.char}: {len(shown)} frames at game size (x{scale})'
            size = make_sheet(shown, sprites, idle, verdicts, bg, out, title, args.width)
            print(f'sheet: {out} ({size[0]}x{size[1]})')
    if anim:
        shown = [n for n in anim if n in sprites]
        if shown:
            out = args.gif or f'{args.char}_anim.gif'
            size = make_gif(shown, sprites, bg, s['fps'], out)
            print(f'gif: {out} ({size[0]}x{size[1]}, {len(shown)} frames at {s["fps"]} fps)')


if __name__ == '__main__':
    main()
