"""The project's sprite-frames settings: one JSON file (`sprite_frames.json` in the project root) that every script in
this skill reads, so the same scripts work for any game (canvas, sizes, folders differ per project).

Every script takes `--settings PATH`; without it, the file is looked for in the current folder and its parents.
Paths in the file are relative to the folder the file is in (or absolute: the raw-art folder may live elsewhere).

    from sf_settings import load
    s = load(args.settings)
    s.codex_dir('xlr8')            -> Path of the character's Codex folder
    s.frame('xlr8', 'walk_01')     -> {'file': ..., 'factor': 1.0, 'centring': 'legs'}
"""
import json
from pathlib import Path

FILE_NAME = 'sprite_frames.json'

DEFAULTS = {
    'raw_art': 'character_raw_art',        # <raw_art>/<char>/<char>_reference, <char>_codex, <char>_prompts.md (copy)
    'prompts_dir': 'docs/characters',      # the master prompts file: <prompts_dir>/<char>_prompts.md
    'sprites_dir': 'assets/sprites',       # where fitted frames go (the game's sprites)
    'sprite_name': '{char}_{frame}.png',
    'anchors_name': '{char}_anchors.json',  # effect sheets: where each packed piece lies, next to the sprites
    'art_style': 'docs/art_style.md',
    'canvas_min': 500,                     # fitted frames: at least this wide and tall...
    'canvas_step': 20,                     # ...growing in these steps when a pose is bigger
    'feet_margin': 6,                      # the lowest drawn pixel sits this far above the canvas bottom
    'leg_share': 0.3,                      # 'legs' centring: the lowest share of the drawing counts as legs
    'alpha_floor': 20,                     # alpha at or below this counts as empty
    'alpha_round_up': 250,                 # alpha at or above this becomes 255 (AI cut-outs are 253-254 inside)
    'review_background': [22, 26, 48],     # review sheets: the game's background colour
    'fps': 8,                              # review animations
}

CHARACTER_DEFAULTS = {
    'idle': None,                          # the idle picture (relative to the character folder, or absolute)
    'idle_height': 468,                    # the idle's drawn height on the fitted canvas, px
    'game_scale': 1.0,                     # how the game scales the fitted frames (review sheets show game size)
    'reference_dir': None,                 # default <raw_art>/<char>/<char>_reference
    'codex_dir': None,                     # default <raw_art>/<char>/<char>_codex
    'forbidden_colours': [],               # [{"name", "hue": [lo, hi] (0-360), "min_saturation", "min_value", "max_share"}]
    'white_threshold': 200,                # cutout.py: brighter than this counts as white background (pale: ~240)
    'frames': {},                          # frame -> {"file", "factor", "centring": "legs" | "mass", "mirror"}
    'sheets': {},                          # effect sheets, see fit_frames.py
}

FRAME_DEFAULTS = {'file': None, 'factor': 1.0, 'centring': 'legs', 'mirror': False}   # mirror: drawn facing the wrong way


def find(start=None):
    folder = Path(start or Path.cwd()).resolve()
    for d in (folder, *folder.parents):
        if (d / FILE_NAME).exists():
            return d / FILE_NAME
    raise FileNotFoundError(f'no {FILE_NAME} in {folder} or its parents: pass --settings')


class Settings:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.root = self.path.parent
        data = json.loads(self.path.read_text(encoding='utf-8'))
        self.data = {**DEFAULTS, **data}

    def __getitem__(self, key):
        return self.data[key]

    def p(self, value):
        """A path from the file: relative to the settings file's folder unless absolute."""
        value = Path(value)
        return value if value.is_absolute() else self.root / value

    def characters(self):
        return list(self.data.get('characters', {}))

    def char(self, char):
        return {**CHARACTER_DEFAULTS, **self.data.get('characters', {}).get(char, {})}

    def char_dir(self, char):
        return self.p(self.data['raw_art']) / char

    def reference_dir(self, char):
        c = self.char(char)
        return self.p(c['reference_dir']) if c['reference_dir'] else self.char_dir(char) / f'{char}_reference'

    def codex_dir(self, char):
        c = self.char(char)
        return self.p(c['codex_dir']) if c['codex_dir'] else self.char_dir(char) / f'{char}_codex'

    def idle_path(self, char):
        c = self.char(char)
        if not c['idle']:
            return None
        idle = Path(c['idle'])
        return idle if idle.is_absolute() else self.char_dir(char) / idle

    def prompts_master(self, char):
        return self.p(self.data['prompts_dir']) / f'{char}_prompts.md'

    def prompts_copy(self, char):
        return self.char_dir(char) / f'{char}_prompts.md'

    def sprites_dir(self):
        return self.p(self.data['sprites_dir'])

    def sprite_path(self, char, frame):
        return self.sprites_dir() / self.data['sprite_name'].format(char=char, frame=frame)

    def frames(self, char):
        return {name: self.frame(char, name) for name in self.char(char)['frames']}

    def frame(self, char, name):
        spec = self.char(char)['frames'].get(name, {})
        out = {**FRAME_DEFAULTS, **spec}
        out['file'] = out['file'] or f'{name}.png'
        return out


def load(path=None):
    return Settings(path or find())
