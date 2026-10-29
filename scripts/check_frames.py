"""Automatic checks on a character's sprite frames, before anyone looks at them by eye.

Two kinds of frames:
  raw     the AI tool's output (default folder: the character's `codex_dir`, file names from the frames' `file`):
          transparency (an alpha channel at all, the share of empty pixels, empty corners), a solid background left
          in (white, magenta, black, grey, or a grey/white checkerboard drawn into the picture), a light fringe
          round the outline (needs defringing), cut off (drawn pixels touching the picture's border), forbidden
          colours.
  fitted  the frames fitted for the game (default folder: `sprites_dir`, names from `sprite_name`):
          size against the fitted idle (drawn height and the square root of the drawn area), near-duplicate poses
          (every pair's silhouettes compared, aligned on their feet and centre), the fringe, cut off and
          forbidden colours again.

It prints a table per frame with short flags and the most similar pairs; `--json` writes the same for Claude to read.
It only reports: the exit code is always 0.

    python check_frames.py --settings sprite_frames.json --char xlr8
    python check_frames.py --settings sprite_frames.json --char xlr8 --source fitted --json checks.json
    python check_frames.py --settings S --char C --source fitted --dir path/to/sprites --frames walk_01,walk_02

Every number for the project comes from the settings file (see sf_settings.py): `alpha_floor`, the character's
`forbidden_colours`, `sprite_name`, the folders.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.dont_write_bytecode = True                       # no __pycache__ next to the skill's scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf_settings import load  # noqa: E402

SIZE_TOLERANCE = 0.12      # flag a frame whose height or area differs from the idle's by more than this
FRINGE_LIGHTER = 60        # an edge pixel this much lighter (0-255) than the outline just inside it is fringe...
FRINGE_SHARE = 0.10        # ...and the frame needs defringing when this share of its edge is fringe
CUT_DEPTH = 2              # drawn pixels within this many px of the border count as touching it...
CUT_MIN_PX = 3             # ...when there are at least this many on one side (a stray pixel is not a cut)
SIMILAR_CELLS = 64         # silhouettes are compared on a grid where the idle is this many cells tall...
SIMILAR_BLUR = 2.0         # ...softened by this many cells, so a limb a few px off still counts as the same
SIMILAR_FLAG = 0.58        # pairs at or above this similarity are flagged as near-duplicates (calibrated on XLR8:
                           # his near-same walk, punch and wall-run pairs scored 0.60-0.71, other poses <= 0.57)
SIMILAR_LIST = 8           # how many of the most similar pairs to list


# ---------------------------------------------------------------- loading

def read_rgba(path):
    """The picture as an RGBA uint8 array, and whether the file has transparency at all."""
    im = Image.open(path)
    has_alpha = im.mode in ('RGBA', 'LA', 'PA', 'RGBa', 'La') or 'transparency' in im.info
    return np.asarray(im.convert('RGBA')), has_alpha


def luminance(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


# ---------------------------------------------------------------- the checks

def background(arr, mask):
    """The kind of solid background left in the picture, judged by the border ring, or None when it is empty."""
    h, w = mask.shape
    ring_w = max(4, round(min(h, w) * 0.01))
    ring = np.zeros_like(mask)
    ring[:ring_w], ring[-ring_w:], ring[:, :ring_w], ring[:, -ring_w:] = True, True, True, True
    if mask[ring].mean() < 0.5:
        return None
    rgb = arr[..., :3][ring & mask].astype(np.float32)
    sat = rgb.max(axis=1) - rgb.min(axis=1)
    lum = luminance(rgb)
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    if ((r > 180) & (g < 90) & (b > 180)).mean() >= 0.8:
        return 'magenta'
    if (sat < 25).mean() >= 0.9:
        if is_checkerboard(arr, ring_w):
            return 'checkerboard'
        med = float(np.median(lum))
        return 'white' if med > 200 else 'black' if med < 50 else 'grey'
    med = np.median(rgb, axis=0).astype(int)
    return f'colour {tuple(med.tolist())}'


def is_checkerboard(arr, ring_w):
    """A grey/white checkerboard drawn in: the top and left lines alternate between two light levels in steady runs."""
    lines = [arr[ring_w // 2, :, :3], arr[:, ring_w // 2, :3]]
    for line in lines:
        lum = luminance(line.astype(np.float32))
        lo, hi = np.percentile(lum, 10), np.percentile(lum, 90)
        if hi - lo < 12:
            return False
        bits = lum > (lo + hi) / 2
        if min(bits.mean(), 1 - bits.mean()) < 0.2:
            return False
        changes = np.flatnonzero(bits[1:] != bits[:-1])
        if len(changes) < 6:
            return False
        runs = np.diff(changes)
        if not 4 <= np.median(runs) <= 128:
            return False
    return True


def fringe_share(arr, mask):
    """The share of the outline's edge pixels that are much lighter than the outline just inside them."""
    if mask.sum() < 50:
        return 0.0
    edge = mask & ~ndimage.binary_erosion(mask)
    inner = ndimage.binary_erosion(mask, iterations=2) & ~ndimage.binary_erosion(mask, iterations=5)
    lum = luminance(arr[..., :3].astype(np.float32))
    # the mean luminance of the inner ring around each pixel (a 9 x 9 window)
    inner_sum = ndimage.uniform_filter(lum * inner, 9)
    inner_cnt = ndimage.uniform_filter(inner.astype(np.float32), 9)
    has_inner = inner_cnt > 0.01
    local = np.where(has_inner, inner_sum / np.maximum(inner_cnt, 1e-6), 0)
    judged = edge & has_inner
    light = judged & (lum - local > FRINGE_LIGHTER) & (lum > 110)
    return float(light.sum() / max(1, judged.sum()))


def cut_sides(mask):
    """The sides of the picture that drawn pixels touch."""
    sides = {'top': mask[:CUT_DEPTH], 'bottom': mask[-CUT_DEPTH:],
             'left': mask[:, :CUT_DEPTH], 'right': mask[:, -CUT_DEPTH:]}
    return [side for side, part in sides.items() if part.sum() >= CUT_MIN_PX]


def hsv(rgb):
    """Hue in degrees (0-360), saturation and value (0-1) of an N x 3 uint8 array."""
    rgb = rgb.astype(np.float32) / 255
    mx, mn = rgb.max(axis=1), rgb.min(axis=1)
    d = mx - mn
    safe = np.where(d > 0, d, 1)
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    hue = np.where(mx == r, ((g - b) / safe) % 6, np.where(mx == g, (b - r) / safe + 2, (r - g) / safe + 4)) * 60
    hue = np.where(d > 0, hue, 0)
    sat = np.where(mx > 0, d / np.where(mx > 0, mx, 1), 0)
    return hue, sat, mx


def where_in(mask, part):
    """Where `part` lies in the drawing, roughly: 'top left', 'middle', 'bottom right'..."""
    top, bottom, left, right = drawn_box(mask)
    ys, xs = np.nonzero(part)
    fy = (ys.mean() - top) / max(1, bottom - top)
    fx = (xs.mean() - left) / max(1, right - left)
    row = 'top' if fy < 1 / 3 else 'bottom' if fy > 2 / 3 else 'middle'
    col = 'left' if fx < 1 / 3 else 'right' if fx > 2 / 3 else ''
    return f'{row} {col}'.strip() if row != 'middle' or not col else col


def forbidden(arr, mask, rules):
    """Each forbidden colour's share of the drawn pixels: [(name, share, over the limit, where)]."""
    solid = mask & (arr[..., 3] >= 128)          # half-transparent edge pixels don't show their colour reliably
    if not rules or solid.sum() == 0:
        return []
    hue, sat, val = hsv(arr[..., :3][solid])
    out = []
    for rule in rules:
        lo, hi = rule['hue']
        in_hue = (hue >= lo) & (hue <= hi) if lo <= hi else (hue >= lo) | (hue <= hi)   # e.g. red: [340, 20]
        hit = in_hue & (sat >= rule.get('min_saturation', 0)) & (val >= rule.get('min_value', 0))
        share = float(hit.mean())
        where = None
        if hit.any():
            part = np.zeros_like(solid)
            part[solid] = hit
            where = where_in(mask, part)
        out.append((rule.get('name', f'hue {lo}-{hi}'), share, share > rule.get('max_share', 0), where))
    return out


def drawn_box(mask):
    """(top, bottom, left, right) of the drawn pixels, inclusive, or None."""
    rows, cols = np.flatnonzero(mask.any(axis=1)), np.flatnonzero(mask.any(axis=0))
    if len(rows) == 0:
        return None
    return int(rows[0]), int(rows[-1]), int(cols[0]), int(cols[-1])


# ---------------------------------------------------------------- near-duplicates

def silhouette(mask, cell):
    """The mask shrunk to cells of `cell` px (soft: each cell holds its drawn share), with its feet row and centre."""
    h, w = mask.shape
    small = Image.fromarray(mask.astype(np.uint8) * 255).resize(
        (max(1, round(w / cell)), max(1, round(h / cell))), Image.BOX)
    small = np.asarray(small, dtype=np.float32) / 255
    ys, xs = np.nonzero(small > 0.05)
    return small, int(ys.max()), float(xs.mean())


def similar_pairs(masks, idle_height):
    """Every pair's similarity (0-1): the soft IoU of their blurred silhouettes with the feet and the centre of mass
    lined up, the best over small shifts (a pose drawn a little to the side is still the same pose)."""
    cell = max(1.0, idle_height / SIMILAR_CELLS)
    sil = {name: silhouette(m, cell) for name, m in masks.items() if m.any()}
    if len(sil) < 2:
        return []
    shift_x, shift_y = 4, 2
    margin = shift_x + 3 * SIMILAR_BLUR + 2      # room for the blur and the shifts, so np.roll never wraps a drawing
    left = max(cx for _, _, cx in sil.values()) + margin
    right = max(s.shape[1] - cx for s, _, cx in sil.values()) + margin
    top = max(feet for _, feet, _ in sil.values()) + margin
    gh, gw, feet_row, centre_col = int(top + margin), int(left + right), int(top), int(left)
    placed = {}
    for name, (s, feet, cx) in sil.items():
        grid = np.zeros((gh, gw), np.float32)
        y0, x0 = feet_row - feet, centre_col - round(cx)
        grid[y0:y0 + s.shape[0], x0:x0 + s.shape[1]] = s[:gh - y0, :gw - x0]
        placed[name] = ndimage.gaussian_filter(grid, SIMILAR_BLUR)
    names = list(placed)
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            best = 0.0
            for dy in range(-shift_y, shift_y + 1):
                for dx in range(-shift_x, shift_x + 1):
                    moved = np.roll(placed[b], (dy, dx), axis=(0, 1))   # the margins keep the roll from wrapping
                    inter = np.minimum(placed[a], moved).sum()
                    union = np.maximum(placed[a], moved).sum()
                    best = max(best, float(inter / union) if union else 0.0)
            pairs.append({'a': a, 'b': b, 'similarity': round(best, 3), 'flag': best >= SIMILAR_FLAG})
    pairs.sort(key=lambda p: -p['similarity'])
    return pairs


# ---------------------------------------------------------------- running

def frame_path(s, char, name, source, folder):
    if source == 'raw':
        base = Path(folder) if folder else s.codex_dir(char)
        return base / s.frame(char, name)['file']
    if folder:
        return Path(folder) / s['sprite_name'].format(char=char, frame=name)
    return s.sprite_path(char, name)


def check_frame(path, s, char, source):
    """One frame's measures and flags; also its mask for the pair check."""
    floor = s['alpha_floor']
    arr, has_alpha = read_rgba(path)
    mask = arr[..., 3] > floor
    h, w = mask.shape
    row = {'file': str(path), 'size': [w, h], 'flags': []}
    flags = row['flags']

    bg = background(arr, mask)
    row['background'] = bg
    if source == 'raw':
        row['alpha'] = has_alpha
        row['empty_share'] = round(float(1 - mask.mean()), 3)
        c = max(2, round(min(h, w) * 0.02))
        corners = [mask[:c, :c], mask[:c, -c:], mask[-c:, :c], mask[-c:, -c:]]
        row['corners_empty'] = all(not part.any() for part in corners)
        if not has_alpha:
            flags.append('NO ALPHA')
        if not row['corners_empty']:
            flags.append('corners not empty')
    if bg:
        flags.append(f'background: {bg}')
        row['fringe'] = None
        row['cut_off'] = []
    else:
        row['fringe'] = round(fringe_share(arr, mask), 3)
        if row['fringe'] > FRINGE_SHARE:
            flags.append(f'light fringe {row["fringe"]:.0%}: defringe')
        row['cut_off'] = cut_sides(mask)
        if row['cut_off']:
            flags.append('cut off: ' + ','.join(row['cut_off']))

    # colour shares mean nothing while a background fills the picture
    row['forbidden'] = {}
    for name, share, over, where in [] if bg else forbidden(arr, mask, s.char(char)['forbidden_colours']):
        row['forbidden'][name] = {'share': round(share, 4), 'where': where}
        if over:
            flags.append(f'{name} {share:.1%} ({where})')

    box = drawn_box(mask)
    row['drawn_height'] = box[1] - box[0] + 1 if box else 0
    row['drawn_area'] = int(mask.sum())
    if not box:
        flags.append('EMPTY picture')
    return row, mask


def size_flags(row, idle_row):
    """Height and sqrt(area) against the idle's."""
    if not idle_row or not row['drawn_area']:
        return
    row['height_ratio'] = round(row['drawn_height'] / idle_row['drawn_height'], 3)
    row['area_ratio'] = round((row['drawn_area'] / idle_row['drawn_area']) ** 0.5, 3)
    for key, label in (('height_ratio', 'height'), ('area_ratio', 'area')):
        off = row[key] - 1
        if abs(off) > SIZE_TOLERANCE:
            row['flags'].append(f'{label} {off:+.0%}')


def print_table(rows, source):
    if source == 'raw':
        head = ['frame', 'size', 'alpha', 'empty', 'fringe', 'flags']
        lines = [[name, f'{r["size"][0]}x{r["size"][1]}', 'yes' if r.get('alpha') else 'NO',
                  f'{r["empty_share"]:.0%}', '-' if r['fringe'] is None else f'{r["fringe"]:.0%}',
                  ', '.join(r['flags']) or 'ok'] if 'size' in r else [name, '-', '-', '-', '-', ', '.join(r['flags'])]
                 for name, r in rows.items()]
    else:
        head = ['frame', 'canvas', 'drawn h', 'height', 'area', 'fringe', 'flags']

        def pct(r, key):
            return f'{r[key] - 1:+.0%}' if key in r else '-'

        lines = [[name, f'{r["size"][0]}x{r["size"][1]}', str(r['drawn_height']), pct(r, 'height_ratio'),
                  pct(r, 'area_ratio'), '-' if r['fringe'] is None else f'{r["fringe"]:.0%}',
                  ', '.join(r['flags']) or 'ok'] if 'size' in r else [name, '-', '-', '-', '-', '-', ', '.join(r['flags'])]
                 for name, r in rows.items()]
    widths = [max(len(head[i]), *(len(line[i]) for line in lines)) for i in range(len(head) - 1)]
    fmt = '  '.join(f'{{:<{w}}}' for w in widths) + '  {}'
    print(fmt.format(*head))
    print(fmt.format(*('-' * w for w in widths), '-----'))
    for line in lines:
        print(fmt.format(*line))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--settings', help='sprite_frames.json (default: looked for in this folder and its parents)')
    ap.add_argument('--char', required=True)
    ap.add_argument('--source', choices=['raw', 'fitted'], default='raw')
    ap.add_argument('--dir', help='the frames folder (default: codex_dir for raw, sprites_dir for fitted)')
    ap.add_argument('--frames', help='a,b,c (default: every frame of the character in the settings)')
    ap.add_argument('--json', help='also write the report as JSON here')
    args = ap.parse_args()

    s = load(args.settings)
    names = args.frames.split(',') if args.frames else list(s.frames(args.char))
    rows, masks = {}, {}
    for name in names:
        path = frame_path(s, args.char, name, args.source, args.dir)
        if not path.exists():
            rows[name] = {'file': str(path), 'flags': ['MISSING file']}
            continue
        try:
            rows[name], masks[name] = check_frame(path, s, args.char, args.source)
        except Exception as e:  # a broken file is a finding, not a crash
            rows[name] = {'file': str(path), 'flags': [f'unreadable: {e}']}

    notes, pairs = [], []
    if args.source == 'fitted':
        idle_path = frame_path(s, args.char, 'idle', 'fitted', args.dir)
        idle_row = None
        if idle_path.exists():
            idle_row, idle_mask = check_frame(idle_path, s, args.char, 'fitted')
            if 'idle' not in masks:
                masks['idle'] = idle_mask
        else:
            notes.append(f'no fitted idle at {idle_path}: sizes not compared')
        for r in rows.values():
            if 'size' in r:
                size_flags(r, idle_row)
        idle_height = idle_row['drawn_height'] if idle_row else s.char(args.char)['idle_height']
        pairs = similar_pairs({n: m for n, m in masks.items() if m.any()}, idle_height)
        notes.append(f'height / area: the drawn height and sqrt(drawn area) against the idle; flagged beyond '
                     f'+-{SIZE_TOLERANCE:.0%}. Height differences are expected for crouches, kicks, jumps and '
                     f'lying poses; the area is the steadier measure.')

    print(f'{args.char}: {len(names)} {args.source} frames' + (f' in {args.dir}' if args.dir else ''))
    print()
    print_table(rows, args.source)
    if pairs:
        print()
        print(f'Most similar poses (silhouettes on feet and centre, 1.0 = the same; flagged from {SIMILAR_FLAG}):')
        for p in pairs[:SIMILAR_LIST]:
            print(f'  {p["similarity"]:.2f}  {p["a"]} ~ {p["b"]}' + ('   <- near-duplicate?' if p['flag'] else ''))
    for note in notes:
        print()
        print(note)

    if args.json:
        out = {'char': args.char, 'source': args.source, 'frames': rows,
               'similar_pairs': pairs[:max(SIMILAR_LIST, sum(p['flag'] for p in pairs))], 'notes': notes}
        Path(args.json).write_text(json.dumps(out, indent=2), encoding='utf-8', newline='\n')
        print()
        print(f'JSON: {args.json}')
    return 0


if __name__ == '__main__':
    main()
    sys.exit(0)
