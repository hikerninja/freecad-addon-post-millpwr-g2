"""Native FreeCAD CAM postprocessor, classic export API (also wrapped by current FreeCAD).
Install this and millpwr_dialect.py together in FreeCAD's user postprocessor path.
"""
import sys
from pathlib import Path

# Resolve symlinks so dependencies are loaded from the
# installed Addon Manager repository.
POSTPROCESSOR_DIR = Path(__file__).resolve().parent

if str(POSTPROCESSOR_DIR) not in sys.path:
    sys.path.insert(0, str(POSTPROCESSOR_DIR))

from millpwr_dialect import Dialect, PostError, canonical

POST_TYPE = "machine"


def _commands(objectslist):
    for obj in objectslist:
        path = getattr(obj, "Path", None)
        if path is None:
            continue
        for command in path.Commands:
            yield command


def _translate_command(dialect, command):
    name = canonical(command.Name)
    params = {str(k).upper(): v for k, v in command.Parameters.items()}
    # FreeCAD may encode F/S/T as separate commands whose value is a parameter.
    if name in ("F", "S") and name not in params:
        raise PostError(f"Missing {name} parameter")
    if name == "M6" and "T" in params:
        dialect.emit("T" + str(int(params.pop("T"))))
    if name in ("G0", "G1", "G2", "G3"):
        dialect.emit(name, params)
    elif name.startswith("T") and name[1:].isdigit():
        dialect.emit(name, params)
    elif name in {"F", "S"}:
        dialect.emit(name, params)
    else:
        dialect.emit(name, params)


def export(objectslist, filename, argstring):
    """FreeCAD invokes this from CAM > Post Process.

    Deliberately no custom arguments in v0.1. Fail before writing any file.
    """
    if (argstring or "").strip():
        raise PostError("v0.1 does not accept postprocessor arguments")
    dialect = Dialect()
    count = 0
    for command in _commands(objectslist):
        try:
            _translate_command(dialect, command)
        except PostError as ex:
            raise PostError(f"At FreeCAD CAM command #{count + 1} ({command.Name}): {ex}") from ex
        count += 1
    if count == 0:
        raise PostError("No CAM toolpath commands found")
    gcode = dialect.finish()
    if filename:
        with open(filename, "w", encoding="ascii", newline="\n") as output:
            output.write(gcode)
    return gcode
