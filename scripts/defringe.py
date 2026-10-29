"""Remove the light ring a white-background cut-out leaves around a sprite (or the pink one magenta leaves).

When a frame is cut out of a white background, the anti-aliased pixels of its dark outline are half outline, half
white: they stay as a light grey ring. In the game (a dark background, the sprite rescaled every frame) that ring
flickers as white lines and specks. This un-mixes those edge pixels from the background colour: each one takes the
colour of the solid neighbour (within 2 px) that is furthest from the background colour (for white: the darkest, the
outline; "far" is measured in brightness steps, each channel weighted as the eye sees it) and keeps only as much
alpha as that colour contributed, so the ring becomes a soft dark edge. Size, position and the feet row don't change.
Run it on every frame cut from a white background: on the raw art in the Codex folder after cutout.py, before
fit_frames.py (fitting again then keeps the clean edge), or on a fitted sprite.

  python defringe.py walk_01.png                              clean in place (the original is backed up first)
  python defringe.py land.png --hole 150,404 --hole 57,459    also remove white trapped between claws
  python defringe.py walk_01.png --out preview.png            write elsewhere, leave the picture as it is
  python defringe.py web.png --bg magenta                     the pink spill of a magenta background

--hole X,Y       also make the light blob at (X, Y) (px in the picture) transparent: background colour trapped
                 between claws or between an arm and the body. Check each one by eye first: to the script, teeth and
                 highlights look exactly like trapped white.
--band PX        how far in from the edge to clean (default 2.5)
--bg COLOUR      the background it was cut from: white (default), magenta or R,G,B. cutout.py already un-mixes
                 magenta exactly, so magenta is only for pictures cut out elsewhere that kept a pink ring; check
                 the result by eye (the band's lighter-than-outline pixels are un-mixed too)
--settings S     take the "solid" alpha from the settings' alpha_round_up (default 250)
--backup-dir D   where the original goes when cleaning in place (default: before_defringe/ next to the picture;
                 keep it out of folders the game ships). An existing backup is never overwritten (_1, _2... suffixes).

Ported from the Alien Fight project's defringe_sprite.py (white only there; on white this gives the same result).
Needs Pillow, numpy and scipy.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.dont_write_bytecode = True                       # no __pycache__ next to the skill's scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cutout import backup                            # noqa: E402

COLOURS = {'white': (255, 255, 255), 'magenta': (255, 0, 255)}
SOLID = 250              # alpha at or above this counts as solid (a pixel whose colour can be trusted)
LUMA = np.array([0.299, 0.587, 0.114])   # how bright each channel looks
MIN_STEP = 8             # a pixel must be this much nearer the background than its solid neighbour to count as mixed


def parse_colour(text):
    if text in COLOURS:
        return np.array(COLOURS[text], float)
    try:
        rgb = [float(v) for v in text.split(',')]
    except ValueError:
        rgb = []
    if len(rgb) != 3:
        raise SystemExit(f'--bg: white, magenta or R,G,B, not {text!r}')
    return np.array(rgb)


def unmix(rgb, alpha, mask, bg, solid=SOLID, radius=2):
    """Pixels in `mask` nearer the background colour than a solid neighbour: colour = the solid neighbour within
    `radius` furthest from the background, alpha = how much of that colour the pixel holds over the background."""
    h, w = alpha.shape
    far = np.abs(rgb - bg) @ LUMA          # how far each colour is from the background (on white: 255 - brightness)
    # the search keeps the smallest value, so solid pixels enter as -far and everything else as +inf
    padded = np.pad(np.where(alpha >= solid, -far, np.inf), radius, constant_values=np.inf)
    best = np.full((h, w), np.inf)
    best_y = np.zeros((h, w), int)
    best_x = np.zeros((h, w), int)
    ys, xs = np.mgrid[0:h, 0:w]
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            cand = padded[radius + dy:radius + dy + h, radius + dx:radius + dx + w]
            better = cand < best
            best = np.where(better, cand, best)
            best_y = np.where(better, ys + dy, best_y)
            best_x = np.where(better, xs + dx, best_x)

    sel = mask & np.isfinite(best) & (-best > far + MIN_STEP + 1e-6)   # 1e-6: float noise at exact ties
    fg = rgb[best_y[sel], best_x[sel]]
    px = rgb[sel]
    # least squares: px = k * fg + (1 - k) * bg
    k = ((bg - px) * (bg - fg)).sum(1) / (((bg - fg) ** 2).sum(1) + 1e-6)
    rgb, alpha = rgb.copy(), alpha.copy()
    rgb[sel] = fg
    alpha[sel] = alpha[sel] * np.clip(k, 0, 1)
    return rgb, alpha, int(sel.sum())


def remove_holes(rgb, alpha, points, bg):
    """Make the blob of near-background colour nearest each (x, y) point transparent. Near = every channel within 80
    of the background and the difference about the same on all of them (for white: light and unsaturated)."""
    d = rgb - bg
    near = (alpha > 0) & (np.abs(d).max(-1) < 80) & (d.max(-1) - d.min(-1) < 28)
    labels, _ = ndimage.label(near)
    ly, lx = np.nonzero(labels)
    removed = 0
    for x, y in points:
        if not len(lx):
            raise SystemExit(f'No background-coloured blob near {x},{y}.')
        k = np.argmin((lx - x) ** 2 + (ly - y) ** 2)
        if (lx[k] - x) ** 2 + (ly[k] - y) ** 2 > 9:
            raise SystemExit(f'No background-coloured blob within 3 px of {x},{y}.')
        blob = labels == labels[ly[k], lx[k]]
        alpha = np.where(blob, 0.0, alpha)
        removed += int(blob.sum())
    return alpha, removed


def defringe(img, bg=COLOURS['white'], band=2.5, holes=(), solid=SOLID):
    """RGBA float array -> (cleaned RGBA float array, edge pixels cleaned, trapped pixels removed)."""
    bg = np.asarray(bg, float)
    rgb, alpha = img[..., :3], img[..., 3]
    alpha, removed = remove_holes(rgb, alpha, holes, bg)
    edge = (alpha > 0) & (ndimage.distance_transform_edt(alpha > 0) <= band)
    rgb, alpha, fixed = unmix(rgb, alpha, edge, bg, solid)
    return np.dstack([rgb, alpha]), fixed, removed


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('image', type=Path)
    p.add_argument('--out', type=Path, help='write here instead of overwriting the image')
    p.add_argument('--hole', action='append', default=[], help='X,Y of a leftover background blob to remove')
    p.add_argument('--band', type=float, default=2.5)
    p.add_argument('--bg', default='white')
    p.add_argument('--settings', type=Path)
    p.add_argument('--backup-dir', type=Path)
    args = p.parse_args()

    solid = SOLID
    if args.settings:
        from sf_settings import load
        solid = int(load(args.settings)['alpha_round_up'])
    img = np.asarray(Image.open(args.image).convert('RGBA')).astype(np.float64)
    if img[..., 3].min() == 255:
        raise SystemExit(f'{args.image}: no transparency; cut it out first (cutout.py)')
    points = [tuple(int(v) for v in h.split(',')) for h in args.hole]
    out, fixed, removed = defringe(img, parse_colour(args.bg), args.band, points, solid)

    dest = args.out
    if dest is None:
        dest = args.image
        saved = backup(args.image, args.backup_dir or args.image.parent / 'before_defringe')
        print(f'original saved to {saved}')
    Image.fromarray(out.clip(0, 255).round().astype(np.uint8), 'RGBA').save(dest)
    print(f'{dest}: {fixed} edge pixels cleaned, {removed} trapped pixels removed')


if __name__ == '__main__':
    main()
