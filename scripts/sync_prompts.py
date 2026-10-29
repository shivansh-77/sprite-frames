"""Copies a character's master prompts file (in the project's prompts folder) to the copy that sits next to its art, so
Codex reads the latest. Run after every change to the master (ticks, Fix lines, new prompts); never edit the copy.

    python sync_prompts.py --settings sprite_frames.json --char xlr8      (or --all)
"""
import argparse
import shutil
import sys

sys.dont_write_bytecode = True                       # no __pycache__ next to the skill's scripts
from sf_settings import load                         # noqa: E402


def sync(s, char):
    master, copy = s.prompts_master(char), s.prompts_copy(char)
    if not master.exists():
        print(f'{char}: no master at {master}')
        return
    copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(master, copy)
    print(f'{char}: {master} -> {copy}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--settings')
    ap.add_argument('--char')
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    s = load(args.settings)
    for c in (s.characters() if args.all else [args.char]):
        sync(s, c)
