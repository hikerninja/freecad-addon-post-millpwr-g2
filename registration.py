"""Link the Addon Manager-installed post into FreeCAD's user macro directory.

FreeCAD 1.1.x lists posts found in Path.Preferences.searchPathsPost().
A symlink lets Addon Manager update the installed file in place.
"""
from pathlib import Path
import os

POST_NAME = 'millpwr_g2_post.py'


def install_link(addon_root, macro_directory):
    root = Path(addon_root).resolve()
    source = root / 'postprocessors' / POST_NAME
    target = Path(macro_directory).expanduser() / POST_NAME
    if not source.is_file():
        raise FileNotFoundError(f'Addon postprocessor not found: {source}')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        if target.resolve() == source:
            return target
        raise FileExistsError(f'Another postprocessor link already exists: {target}')
    if target.exists():
        raise FileExistsError(f'Cannot replace existing file: {target}')
    target.symlink_to(source)
    return target


def register(freecad, addon_root):
    """Run at FreeCAD startup; do not overwrite a user's custom post."""
    import sys
    root = Path(addon_root).resolve()
    path = str(root / 'postprocessors')
    if path not in sys.path:
        sys.path.insert(0, path)
    return install_link(root, freecad.getUserMacroDir())
