"""Cut a picture out of a solid white or magenta background (AI image tools often can't give real transparency).

fit_frames.py does this by itself to every opaque picture it reads, so this script is only needed to cut a picture
out on its own: to look at the cut-out, or to defringe it (defringe.py) before fitting.

  python cutout.py walk_01.png                      cut out in place (the original is backed up first)
  python cutout.py walk_01.png --out cut.png        write elsewhere, leave the picture as it is
  python cutout.py idle.png --bg white --white-threshold 240      a pale character on white

--bg auto (default)   decided by the picture's border: magenta (#FF00FF-ish) or white (all channels >= 235); a picture
                      that already has transparency is left as it is
--bg white            the white around the drawing (everything light that touches the picture's edge) and enclosed
                      see-through holes (60 px or more, nearly pure white) go; small white highlights inside stay.
                      The 2 px rim of the drawing is un-mixed from the white (its alpha = how much of it isn't white)
--white-threshold N   how light (darkest channel >= N) a pixel must be to count as white background (default 200;
                      pale characters, e.g. a light grey body, need 240 or more or they get eaten)
--bg magenta          every pixel's alpha comes from how much magenta it holds, and its colour is un-mixed from it,
                      so the soft edge keeps no pink. Never ask for green: it eats green parts of the drawing
--settings S --char C read --white-threshold from the character's "white_threshold" in the settings (if set)
--backup-dir DIR      where the original goes when cutting in place (default: before_cutout/ next to the picture);
                      an existing backup is never overwritten (_1, _2... suffixes)

Ported from the Alien Fight project's fit_sprite.py (white) and fit_spidermonkey.py's load (magenta).
Needs Pillow, numpy and scipy.
"""
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.dont_write_bytecode = True                       # no __pycache__ next to the skill's scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))

WHITE_THRESHOLD = 200     # darkest channel at or above this = white background (fit_sprite.py)
MAGENTA = (255, 0, 255)


def border_colour(a):
    """The median colour of the picture's outermost rows and columns."""
    border = np.concatenate([a[0, :, :3], a[-1, :, :3], a[:, 0, :3], a[:, -1, :3]])
    return np.median(border, axis=0)


def background_of(a):
    """'transparent', 'magenta', 'white' or None (a solid colour this script can't remove)."""
    if a[..., 3].min() < 255:
        return 'transparent'
    bg = border_colour(a)
    if bg[0] > 200 and bg[1] < 80 and bg[2] > 200:
        return 'magenta'
    if (bg >= 235).all():
        return 'white'
    return None


def key_magenta(a):
    """Alpha from how much magenta each pixel holds; its colour un-mixed from the magenta: c = k * fg + (1 - k) * bg."""
    a = a.copy()
    bg = border_colour(a)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    pink = np.clip(np.minimum(r, b) - g, 0, None) / (min(bg[0], bg[2]) - bg[1])
    k = np.clip(1 - (pink - 0.15) / 0.7, 0, 1)
    a[..., :3] = np.clip((a[..., :3] - (1 - k[..., None]) * bg) / np.maximum(k[..., None], 1e-3), 0, 255)
    a[..., 3] = k * 255
    return a


def remove_white(a, threshold=WHITE_THRESHOLD):
    """The white that touches the picture's edge, and big enclosed white holes, made transparent; the drawing's rim
    un-mixed from white (no light halo, as far as one pass can: defringe.py cleans what's left)."""
    rgb = a[..., :3].astype(np.float64).copy()
    mn = rgb.min(axis=2)
    labels, count = ndimage.label(mn >= threshold)
    edge = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
    bg = np.isin(labels, list(edge))
    for lab in range(1, count + 1):                  # enclosed see-through holes, not highlights
        if lab not in edge:
            m = labels == lab
            if m.sum() >= 60 and mn[m].mean() >= 235:
                bg |= m
    alpha = np.where(bg, 0.0, 255.0)
    # The anti-aliased rim: estimate how much of each pixel is drawing and strip the white it was blended with
    rim = ndimage.binary_dilation(bg, iterations=2) & ~bg
    cover = np.clip((255 - mn) / 225.0, 0, 1)
    alpha[rim] = cover[rim] * 255
    k = np.maximum(cover[rim], 0.05)[:, None]
    rgb[rim] = np.clip((rgb[rim] - (1 - k) * 255) / k, 0, 255)
    return np.dstack([rgb, alpha])


def cut_out(a, bg='auto', white_threshold=WHITE_THRESHOLD):
    """RGBA float array -> (cut-out RGBA float array, what was removed: 'transparent' = nothing, 'white', 'magenta').
    Raises ValueError when bg is 'auto' and the background is neither."""
    kind = background_of(a) if bg == 'auto' else bg
    if kind == 'transparent':
        return a, kind
    if kind == 'magenta':
        return key_magenta(a), kind
    if kind == 'white':
        return remove_white(a, white_threshold), kind
    raise ValueError(f'no transparency and the background ({border_colour(a).round()}) is neither white nor '
                     f'magenta: cut it out first (or ask the image tool for white, magenta or transparent)')


def backup(path, folder):
    """Copies `path` into `folder` without overwriting an earlier backup; returns where it went."""
    folder.mkdir(parents=True, exist_ok=True)
    dest, n = folder / path.name, 1
    while dest.exists():
        dest, n = folder / f'{path.stem}_{n}{path.suffix}', n + 1
    shutil.copy2(path, dest)
    return dest


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('images', nargs='+', type=Path)
    p.add_argument('--out', type=Path, help='write here instead of in place (one image only)')
    p.add_argument('--bg', choices=['auto', 'white', 'magenta'], default='auto')
    p.add_argument('--white-threshold', type=int)
    p.add_argument('--settings', type=Path)
    p.add_argument('--char')
    p.add_argument('--backup-dir', type=Path)
    args = p.parse_args()
    if args.out and len(args.images) > 1:
        raise SystemExit('--out takes one image')

    threshold = args.white_threshold
    if threshold is None and args.settings and args.char:
        from sf_settings import load
        threshold = load(args.settings).char(args.char).get('white_threshold')
    threshold = threshold or WHITE_THRESHOLD

    for path in args.images:
        a = np.array(Image.open(path).convert('RGBA')).astype(np.float64)
        try:
            out, kind = cut_out(a, args.bg, threshold)
        except ValueError as e:
            raise SystemExit(f'{path}: {e}')
        if kind == 'transparent':
            print(f'{path}: already transparent, left as it is')
            continue
        dest = args.out
        if dest is None:
            dest = path
            saved = backup(path, args.backup_dir or path.parent / 'before_cutout')
            print(f'  original saved to {saved}')
        Image.fromarray(out.clip(0, 255).round().astype(np.uint8), 'RGBA').save(dest)
        print(f'{dest}: {kind} background removed' + (f' (threshold {threshold})' if kind == 'white' else ''))


if __name__ == '__main__':
    main()
