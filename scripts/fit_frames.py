"""Fit a character's raw frames (from Codex / ChatGPT) into game sprites that line up with each other.

AI image tools fill whatever canvas they get, so every frame comes out at its own size and place. This sizes them
all to the character's idle and stands them on one feet row, so the game can swap frames without the character
jumping around. Every number comes from the project's settings file (sf_settings.py, `sprite_frames.json`).

  python fit_frames.py --settings S --char xlr8 --dry-run --preview p.png      measure and preview only
  python fit_frames.py --settings S --char xlr8 --out review/ --preview p.png  fit into a review folder
  python fit_frames.py --settings S --char xlr8 --frames walk_01,jump          only these (and the idle as reference)
  python fit_frames.py --settings S --char xlr8                                write into the game's sprites

What it does (ported from the Alien Fight project's fit_xlr8.py / fit_bigchill.py):
- Every picture is read with its background cut out if it has none (white or magenta, cutout.py) and its alpha
  rounded: >= alpha_round_up -> 255 (AI cut-outs are 253-254 inside), <= alpha_floor -> 0. Then trimmed to what's
  drawn (alpha > alpha_floor).
- The idle (the character's "idle" picture) is scaled so its drawn height is idle_height px and stood in the middle
  of a canvas_min square (its bounding box centred), its lowest drawn row on row H - feet_margin.
- Every frame is scaled so the area it covers (the square root of its drawn pixels, alpha > 128) matches the fitted
  idle's, times its "factor" (set by eye: < 1 when a pose spreads out and looks too big, > 1 when it hides the body).
  Its lowest drawn row goes on the feet row (H - feet_margin) and it is centred like the idle by its "centring":
  'legs' = the middle of the lowest leg_share of the drawing goes where the idle's legs are (grounded poses: the feet
  don't slide between frames), 'mass' = the middle of everything drawn goes where the idle's is (airborne poses,
  lying down). The canvas is at least canvas_min square and grows in canvas_step steps (keeping 10 px free around
  the pose) when a pose doesn't fit; it always grows evenly on both sides, so the canvas's bottom centre (the
  sprite's origin in the game) stays under the character.
- Scaling weights the colour by alpha (Pillow's premultiplied 'RGBa'), so edges get no dark or light fringe.
- Writes <sprite_path(char, frame)> (or the same names in --out DIR), the idle included unless --frames leaves it
  out, and prints a table: the scale (area-matched x factor), the canvas, the drawn size, and the drawn height and
  area against the idle's (area 1.00 = the same size as the idle; a factor shows up here).
- --preview PNG: every fitted frame at game size (game_scale) side by side on review_background, feet on one line,
  each sprite's origin marked (yellow tick), the idle first; the effect sheets below.

Settings it reads: canvas_min, canvas_step, feet_margin, leg_share, alpha_floor, alpha_round_up, review_background,
sprites_dir / sprite_name, and per character: idle, idle_height, game_scale, codex_dir, frames, sheets. Optional per
character: "white_threshold" (cutout.py, default 200; 240+ for pale characters on white). Per frame:
    "walk_01": {"file": "walk_01.png", "factor": 1.0, "centring": "legs", "mirror": false}
"file" is relative to the character's codex_dir (or absolute); "mirror": true flips a frame drawn facing the wrong way.

Effect sheets ("sheets", per character): one picture with several pieces drawn in a grid (the prompt's order, row
by row; e.g. a tornado's bands, dust puffs). Each piece is cut out, all are scaled by one factor (so their sizes stay
true to each other) and packed into rows of one picture, written as <sprite_path(char, sheet name)>; where each piece
lies goes into <sprites_dir>/<anchors_name> (default "{char}_anchors.json") under the sprite's name (its file name
without .png), as {piece: [x, y, w, h]} in px of the packed picture. Other keys in that file are kept.
    "sheets": {
      "tornado": {
        "file": "tornado_sheet.png",                 relative to codex_dir
        "pieces": [["band_wide", "band_medium", "band_narrow"],
                   ["lip", "base_ring", "gust"]],     names, row by row as drawn
        "rows": [460],                               source px: the lines between rows (one fewer than rows)
        "columns": [[690, 1180], [590, 1130]],       per row, source px: the lines between its pieces
        "scale": 0.6,                                one scale for every piece (source px -> sprite px)
        "max_width": 2048,                           a packed row wraps before it gets wider (optional, 2048)
        "gap": 6,                                    px between packed pieces (optional, 6)
        "background": "cutout",                      "cutout" (transparent, white or magenta; default) or "black":
                                                     light drawn on black, kept black (the game draws it additively)
        "reach": 0,                                  source px around a piece's blobs that still belong to it (its
                                                     soft edge, loose bits; optional, 0; ~24 for smoke on black)
        "floor": 10                                  "black" sheets: brightness below which black counts as empty
      }
    }
  Every blob goes to the piece whose grid cell its middle sits in (so a loose droplet joins its piece); with "reach"
  every pixel within that many px of a blob joins the nearest blob's piece. Find the row and column lines by opening
  the sheet in any image viewer that shows pixel coordinates; a piece with nothing found stops the script.

Needs Pillow, numpy and scipy.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.dont_write_bytecode = True                       # no __pycache__ next to the skill's scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf_settings import load as load_settings       # noqa: E402
from cutout import cut_out, WHITE_THRESHOLD          # noqa: E402

EDGE_PAD = 10        # px kept free around a pose that makes the canvas grow (each side, and above it)
RESIZE_FLOOR = 8     # after scaling, alpha at or below this is dropped: only specks, the soft edge stays
AREA_ALPHA = 128     # a pixel counts toward the drawn area when its alpha is over this (more than half covered)


class Fit:
    """The numbers every step needs, from the settings file and the character."""

    def __init__(self, settings, char):
        s, c = settings, settings.char(char)
        self.settings, self.char, self.c = s, char, c
        self.canvas_min = int(s['canvas_min'])
        self.step = int(s['canvas_step'])
        self.feet_margin = int(s['feet_margin'])
        self.leg_share = float(s['leg_share'])
        self.floor = int(s['alpha_floor'])
        self.round_up = int(s['alpha_round_up'])
        self.white_threshold = c.get('white_threshold') or WHITE_THRESHOLD

    def art_path(self, file):
        file = Path(file)
        return file if file.is_absolute() else self.settings.codex_dir(self.char) / file


# ----------------------------------------------------------------------------------------------------------------
# Reading and measuring
# ----------------------------------------------------------------------------------------------------------------
def read_art(path, fit, mirror=False):
    """RGBA float array, background cut out if it had none, alpha rounded."""
    if not path.exists():
        raise SystemExit(f'{path}: not found')
    a = np.array(Image.open(path).convert('RGBA')).astype(np.float64)
    try:
        a, _ = cut_out(a, 'auto', fit.white_threshold)
    except ValueError as e:
        raise SystemExit(f'{path}: {e}')
    if mirror:
        a = a[:, ::-1].copy()
    al = a[..., 3]
    al[al >= fit.round_up] = 255
    al[al <= fit.floor] = 0
    return a


def drawn(a, floor):
    """Rows and columns that hold a drawn pixel (alpha > floor)."""
    al = a[..., 3]
    return np.where(al.max(axis=1) > floor)[0], np.where(al.max(axis=0) > floor)[0]


def trim(a, floor):
    """Crops to the drawn pixels; returns the crop and its top-left corner in the source."""
    rows, cols = drawn(a, floor)
    if not len(rows):
        raise SystemExit('a picture is empty (nothing drawn)')
    return a[rows.min():rows.max() + 1, cols.min():cols.max() + 1], (int(cols.min()), int(rows.min()))


def drawn_area(a):
    return float((a[..., 3] > AREA_ALPHA).sum())


def resize(a, s, round_up):
    """Scaled by s with the colour weighted by alpha (premultiplied 'RGBa': no dark or light fringe), alpha rounded."""
    im = Image.fromarray(np.round(a).clip(0, 255).astype(np.uint8), 'RGBA').convert('RGBa')
    w, h = im.size
    out = np.array(im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS).convert('RGBA'))
    al = out[..., 3]
    al[al >= round_up] = 255
    al[al <= RESIZE_FLOOR] = 0
    return out


def resize_rgb(a, s):
    """An opaque picture on black (light drawn additively: no alpha to premultiply), scaled."""
    im = Image.fromarray(np.round(a[..., :3]).clip(0, 255).astype(np.uint8), 'RGB')
    w, h = im.size
    out = np.array(im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS).convert('RGBA'))
    out[..., 3] = 255
    return out


def centre_of(a, centring, fit):
    """Where a frame is centred, x px in `a`: 'legs' = the alpha-weighted middle of the lowest leg_share of what's
    drawn, 'mass' = the middle of everything drawn."""
    if centring not in ('legs', 'mass'):
        raise SystemExit(f'centring must be "legs" or "mass", not {centring!r}')
    al = a[..., 3].astype(float)
    if centring == 'legs':
        rows, _ = drawn(a, fit.floor)
        cut = rows.max() - (rows.max() - rows.min()) * fit.leg_share
        al = np.where(np.arange(al.shape[0])[:, None] >= cut, al, 0)
    return float((al.sum(axis=0) * np.arange(al.shape[1])).sum() / al.sum())


def place(small, centre_x, idle_dx, fit):
    """`small` on a canvas: its lowest drawn row on row H - feet_margin, its centre_x (px in `small`) idle_dx px right
    of the canvas's middle column. The canvas is at least canvas_min square, grown in canvas_step steps (evenly on
    both sides) when the pose doesn't fit. Returns the canvas and where `small`'s corner went."""
    rows, cols = drawn(small, fit.floor)
    top, feet = rows.min(), rows.max()
    anchor = centre_x - idle_dx
    reach = max(anchor - cols.min(), cols.max() + 1 - anchor)
    grow = lambda px: int(np.ceil(px / fit.step)) * fit.step
    W = max(fit.canvas_min, grow(2 * reach + 2 * EDGE_PAD))
    H = max(fit.canvas_min, grow(feet - top + 1 + fit.feet_margin + EDGE_PAD))
    off_x = round(W / 2 + idle_dx - centre_x)
    off_y = (H - fit.feet_margin) - feet
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(Image.fromarray(small, 'RGBA'), (int(off_x), int(off_y)))
    return np.array(canvas), (int(off_x), int(off_y))


def measure(out, fit):
    rows, cols = drawn(out, fit.floor)
    return {'canvas': (out.shape[1], out.shape[0]), 'drawn': (int(cols.max() - cols.min() + 1),
                                                              int(rows.max() - rows.min() + 1)),
            'area': drawn_area(out)}


# ----------------------------------------------------------------------------------------------------------------
# Body frames
# ----------------------------------------------------------------------------------------------------------------
def fit_idle(fit):
    path = fit.settings.idle_path(fit.char)
    if path is None:
        raise SystemExit(f'characters.{fit.char}.idle is not set in {fit.settings.path}')
    crop, _ = trim(read_art(path, fit), fit.floor)
    s = fit.c['idle_height'] / crop.shape[0]
    small = resize(crop, s, fit.round_up)
    out, _ = place(small, small.shape[1] / 2, 0, fit)       # its bounding box centred
    W = out.shape[1]
    idle = {'legs': centre_of(out, 'legs', fit) - W / 2, 'mass': centre_of(out, 'mass', fit) - W / 2,
            **measure(out, fit)}
    row = {'name': 'idle', 'file': path.name, 'centring': '-', 'measured': s, 'factor': 1.0, 'scale': s}
    print(f'idle: {path.name}, {crop.shape[1]}x{crop.shape[0]} drawn -> scale {s:.3f}; legs {idle["legs"]:+.1f}, '
          f'mass {idle["mass"]:+.1f} px from the canvas middle')
    return out, idle, row


def fit_frame(name, spec, idle, fit):
    path = fit.art_path(spec['file'])
    crop, _ = trim(read_art(path, fit, spec.get('mirror', False)), fit.floor)
    measured = (idle['area'] / drawn_area(crop)) ** 0.5     # idle['area'] is already at canvas scale
    factor = float(spec['factor'])
    small = resize(crop, measured * factor, fit.round_up)
    centring = spec['centring']
    out, _ = place(small, centre_of(small, centring, fit), idle[centring], fit)
    row = {'name': name, 'file': path.name + (' (mirrored)' if spec.get('mirror') else ''), 'centring': centring,
           'measured': measured, 'factor': factor, 'scale': measured * factor}
    return out, row


def table(rows, results, idle):
    head = ['frame', 'file', 'centring', 'area x', 'factor', 'scale', 'canvas', 'drawn', 'height', 'area']
    lines = [head]
    for row in rows:
        m = results[row['name']]
        lines.append([row['name'], row['file'], row['centring'], f'{row["measured"]:.3f}', f'{row["factor"]:.2f}',
                      f'{row["scale"]:.3f}', '{}x{}'.format(*m['canvas']), '{}x{}'.format(*m['drawn']),
                      f'{m["drawn"][1] / idle["drawn"][1]:.2f}', f'{m["area"] / idle["area"]:.2f}'])
    widths = [max(len(line[i]) for line in lines) for i in range(len(head))]
    print()
    for i, line in enumerate(lines):
        print('  '.join(cell.ljust(w) for cell, w in zip(line, widths)).rstrip())
        if i == 0:
            print('  '.join('-' * w for w in widths))
    print('(scale = source px -> sprite px; height and area against the idle\'s)')


# ----------------------------------------------------------------------------------------------------------------
# Effect sheets
# ----------------------------------------------------------------------------------------------------------------
def check_grid(name, spec):
    pieces, rows, columns = spec['pieces'], spec.get('rows', []), spec['columns']
    if len(rows) != len(pieces) - 1 or len(columns) != len(pieces):
        raise SystemExit(f'sheet {name}: {len(pieces)} rows of pieces need {len(pieces) - 1} "rows" lines and '
                         f'{len(pieces)} "columns" lists')
    for r, (names, cols) in enumerate(zip(pieces, columns)):
        if len(cols) != len(names) - 1:
            raise SystemExit(f'sheet {name}: row {r} has {len(names)} pieces, so it needs {len(names) - 1} column '
                             f'lines, not {len(cols)}')


def assign_pieces(mask, spec):
    """Every pixel of `mask` given to a piece by the grid: the blobs by where their middle sits, then (with
    spec['reach']) each pixel to the nearest blob's piece within that many px. Returns a map of piece index + 1."""
    lab, n = ndimage.label(mask)
    centres = ndimage.center_of_mass(mask, lab, range(1, n + 1))
    owner = np.zeros(n + 1, int)
    for label, (cy, cx) in enumerate(centres, 1):
        row = int(np.searchsorted(spec.get('rows', []), cy))
        col = int(np.searchsorted(spec['columns'][row], cx))
        owner[label] = sum(len(r) for r in spec['pieces'][:row]) + col + 1
    pieces = owner[lab]
    reach = spec.get('reach', 0)
    if reach:
        dist, (iy, ix) = ndimage.distance_transform_edt(pieces == 0, return_indices=True)
        pieces = np.where(dist <= reach, pieces[iy, ix], 0)
    return pieces


def pack(a, pieces, spec, fit, keep_black=False):
    """Trims every piece, scales them all by spec['scale'] and packs them in rows (max_width wide at most) into one
    picture. Returns it and {piece name: [x, y, w, h]}."""
    names = [n for row in spec['pieces'] for n in row]
    cut = []
    for i, name in enumerate(names, 1):
        mine = pieces == i
        if not mine.any():
            raise SystemExit(f'{spec["file"]}: nothing found for {name} (check the rows and columns lines)')
        ys, xs = np.where(mine)
        crop = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
        crop[~mine[ys.min():ys.max() + 1, xs.min():xs.max() + 1]] = 0     # only this piece's pixels
        if keep_black:
            crop[..., 3] = 255
            cut.append((name, resize_rgb(crop, spec['scale'])))
        else:
            cut.append((name, resize(crop, spec['scale'], fit.round_up)))
    gap, max_width = spec.get('gap', 6), spec.get('max_width', 2048)
    rects, x, y, row_h = {}, gap, gap, 0
    for name, p in cut:
        h, w = p.shape[:2]
        if x + w + gap > max_width and x > gap:
            x, y, row_h = gap, y + row_h + gap, 0
        rects[name] = [x, y, w, h]
        row_h = max(row_h, h)
        x += w + gap
    width = max(r[0] + r[2] for r in rects.values()) + gap
    height = max(r[1] + r[3] for r in rects.values()) + gap
    out = np.zeros((height, width, 4), np.uint8)
    if keep_black:
        out[..., 3] = 255
    for name, p in cut:
        x, y, w, h = rects[name]
        out[y:y + h, x:x + w] = p
    return out, rects


def fit_sheet(name, spec, fit):
    check_grid(name, spec)
    path = fit.art_path(spec['file'])
    black = spec.get('background', 'cutout') == 'black'
    if black:
        if not path.exists():
            raise SystemExit(f'{path}: not found')
        a = np.array(Image.open(path).convert('RGBA')).astype(np.float64)
        mask = a[..., :3].max(-1) > spec.get('floor', 10)
    else:
        a = read_art(path, fit)
        mask = a[..., 3] > fit.floor
    out, rects = pack(a, assign_pieces(mask, spec), spec, fit, keep_black=black)
    print(f'sheet {name}: {path.name} -> {out.shape[1]}x{out.shape[0]}, '
          + ', '.join(f'{n} {r[2]}x{r[3]}' for n, r in rects.items()))
    return out, rects


# ----------------------------------------------------------------------------------------------------------------
# Preview
# ----------------------------------------------------------------------------------------------------------------
def preview(frames, sheets, out_path, fit):
    """Every frame at game size on the review background, feet on one line, the idle first, with each sprite's
    origin (yellow tick); the sheets below at half size."""
    game_scale = float(fit.c['game_scale'])
    background = tuple(fit.settings['review_background'])[:3] + (255,)
    tiles = []
    for name, arr in frames:
        im = Image.fromarray(arr, 'RGBA')
        tiles.append((name, im.resize((max(1, round(im.width * game_scale)), max(1, round(im.height * game_scale))),
                                      Image.LANCZOS)))
    per_row, gap = 7, 12
    rows = [tiles[i:i + per_row] for i in range(0, len(tiles), per_row)]
    row_h = max(t.height for _, t in tiles) + 24
    width = max(sum(t.width for _, t in r) + gap * (len(r) + 1) for r in rows)
    fx = []
    for name, arr in sheets:
        im = Image.fromarray(arr, 'RGBA')
        k = min(1.0, 1200 / im.width) * 0.5
        fx.append((name, im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)))
    fx_h = max(im.height for _, im in fx) + 24 if fx else 0
    width = max(width, sum(im.width for _, im in fx) + gap * (len(fx) + 1))
    bg = Image.new('RGBA', (width, row_h * len(rows) + fx_h), background)
    d = ImageDraw.Draw(bg)
    line = tuple(min(255, c + 60) for c in background[:3]) + (255,)
    for ri, row in enumerate(rows):
        ground = (ri + 1) * row_h - 16
        x = gap
        d.line([(0, ground), (width, ground)], fill=line)
        for name, im in row:
            bg.alpha_composite(im, (x, ground + round(fit.feet_margin * game_scale) - im.height))
            cx = x + im.width / 2
            d.line([(cx, ground - 6), (cx, ground + 6)], fill=(255, 220, 80, 255))
            d.text((x, ground + 3), name, fill=(220, 220, 220, 255))
            x += im.width + gap
    x, top = gap, row_h * len(rows)
    for name, im in fx:
        bg.alpha_composite(im, (x, top + 4))
        d.text((x, top + 6 + im.height), name, fill=(220, 220, 220, 255))
        x += im.width + gap
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bg.save(out_path)
    print('preview:', out_path)


# ----------------------------------------------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--settings', type=Path, help='the sprite_frames.json (default: found in this folder or above)')
    p.add_argument('--char', required=True)
    p.add_argument('--frames', help='comma-separated frame and sheet names to fit (default: all; the idle is always '
                                    'fitted as the reference, but only written when listed or with no --frames)')
    p.add_argument('--out', type=Path, help='write the fitted frames here (same file names) instead of the sprites '
                                            'folder: a review round')
    p.add_argument('--dry-run', action='store_true', help='measure only, write nothing (but --preview)')
    p.add_argument('--preview', type=Path, help='write a picture of every fitted frame at game size here')
    args = p.parse_args()

    settings = load_settings(args.settings)
    if args.char not in settings.characters():
        raise SystemExit(f'no character {args.char!r} in {settings.path} (has: {", ".join(settings.characters())})')
    fit = Fit(settings, args.char)
    frame_specs = settings.frames(args.char)
    sheet_specs = fit.c.get('sheets') or {}
    wanted = [n.strip() for n in args.frames.split(',') if n.strip()] if args.frames else None
    if wanted:
        unknown = [n for n in wanted if n != 'idle' and n not in frame_specs and n not in sheet_specs]
        if unknown:
            raise SystemExit(f'unknown frames: {", ".join(unknown)} (known: idle, '
                             f'{", ".join([*frame_specs, *sheet_specs])})')
    want = lambda n: wanted is None or n in wanted

    idle_out, idle, idle_row = fit_idle(fit)
    frames, rows, results = [('idle', idle_out)], [idle_row], {'idle': idle}
    for name, spec in frame_specs.items():
        if want(name):
            out, row = fit_frame(name, spec, idle, fit)
            frames.append((name, out))
            rows.append(row)
            results[name] = measure(out, fit)
    table(rows, results, idle)

    sheets, rects = [], {}
    for name, spec in sheet_specs.items():
        if want(name):
            out, rects[name] = fit_sheet(name, spec, fit)
            sheets.append((name, out))

    if not args.dry_run:
        def target(name):
            path = settings.sprite_path(args.char, name)
            return args.out / path.name if args.out else path
        written = [(n, a) for n, a in frames + sheets if n != 'idle' or want('idle')]
        for name, arr in written:
            path = target(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(arr, 'RGBA').save(path, optimize=True)
        print(f'\nwrote {len(written)} sprites to {target("idle").parent}')
        if rects:
            anchors_name = settings.data.get('anchors_name', '{char}_anchors.json').format(char=args.char)
            game_file = settings.sprites_dir() / anchors_name
            anchors_file = (args.out / anchors_name) if args.out else game_file
            source = anchors_file if anchors_file.exists() else game_file
            anchors = json.loads(source.read_text(encoding='utf-8')) if source.exists() else {}
            for name, r in rects.items():
                anchors[target(name).stem] = r
            with open(anchors_file, 'w', newline='\n', encoding='utf-8') as f:
                f.write(json.dumps(dict(sorted(anchors.items())), indent=2) + '\n')
            print(f'wrote the sheets\' pieces into {anchors_file}')
    if args.preview:
        preview(frames, sheets, args.preview, fit)


if __name__ == '__main__':
    main()
