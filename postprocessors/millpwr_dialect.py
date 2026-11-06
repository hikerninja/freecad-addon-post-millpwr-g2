"""Conservative MILLPWR G2 translation core. Python stdlib only.

Input numbers are FreeCAD CAM's internal millimetres and mm/min.
Version 0.1 supports metric, absolute, XYZ, and incremental IJK arc offsets.
"""
import math
import re

class PostError(ValueError):
    pass

MOTION = {"G0", "G1", "G2", "G3"}
MODAL = {"G17", "G40", "G80", "G90", "G21", "G64"}
M_CODES = {"M0", "M1", "M2", "M3", "M4", "M5", "M7", "M8", "M9"}
_ALLOWED = {"X", "Y", "Z", "I", "J", "K", "F"}


def canonical(name):
    s = str(name).strip().upper().replace(" ", "")
    m = re.fullmatch(r"([GM])(\d+)(?:\.0+)?", s)
    return m.group(1) + str(int(m.group(2))) if m else s


def number(value, decimals=4):
    value = float(value)
    if not math.isfinite(value):
        raise PostError("Non-finite coordinate or parameter")
    rounded = round(value, decimals)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.{decimals}f}".rstrip("0").rstrip(".") if decimals else f"{rounded:.0f}"


class Dialect:
    def __init__(self):
        self.lines = ["(MILLPWR G2 - VERIFY DATUM, TOOL LENGTHS AND CLEARANCE)",
                      "G21 G17 G90 G40 G80"]
        self.has_tool = False
        self.ended = False

    def emit(self, name, params=None):
        if self.ended:
            raise PostError("Commands found after program end")
        cmd = canonical(name)
        args = {str(k).upper(): v for k, v in (params or {}).items()}
        if cmd == "M6":
            if not self.has_tool:
                raise PostError("M6 without a preceding T selection")
            return  # G2 tool selection itself prompts for a change
        if cmd == "G20":
            raise PostError("Inch-mode G20 unsupported in v0.1; use metric CAM")
        if cmd in {"G91", "G54", "G55", "G56", "G57", "G58", "G59", "G28", "G53"}:
            raise PostError(f"Unsupported coordinate/offset mode {cmd}")
        if cmd.startswith("T") and cmd[1:].isdigit():
            if args:
                raise PostError("Unexpected parameters on tool selection")
            tool = int(cmd[1:])
            if tool < 1:
                raise PostError("Tool numbers must be positive")
            self.lines.append(f"T{tool}")
            self.has_tool = True
            return
        if cmd in MOTION:
            if not args or set(args) - _ALLOWED:
                raise PostError(f"Unsupported {cmd} parameters: {sorted(set(args) - _ALLOWED)}")
            coords = {k for k in args if k in "XYZ"}
            if not coords:
                raise PostError(f"{cmd} requires an XYZ endpoint")
            centers = {k for k in args if k in "IJK"}
            if cmd in {"G0", "G1"} and centers:
                raise PostError("IJK only allowed on circular moves")
            if cmd in {"G2", "G3"} and not centers:
                raise PostError("Arc requires incremental I/J/K center offset")
            words = [cmd]
            for key in ("X", "Y", "Z", "I", "J", "K", "F"):
                if key in args:
                    if key == "F" and float(args[key]) <= 0:
                        raise PostError("Feed rate must be positive")
                    words.append(key + number(args[key], 3 if key == "F" else 4))
            self.lines.append(" ".join(words))
            return
        if cmd == "F":
            if set(args) != {"F"} or float(args["F"]) <= 0:
                raise PostError("F requires positive feed")
            self.lines.append("F" + number(args["F"], 3))
            return
        if cmd == "S":
            if set(args) != {"S"} or float(args["S"]) <= 0:
                raise PostError("S requires positive RPM")
            self.lines.append("S" + number(args["S"], 0))
            return
        if cmd in MODAL | M_CODES:
            if args:
                raise PostError(f"Unexpected parameters on {cmd}")
            self.lines.append(cmd)
            if cmd == "M2":
                self.ended = True
            return
        raise PostError(f"Unsupported FreeCAD command: {cmd}")

    def finish(self):
        if not self.ended:
            self.lines += ["M5", "M9", "M2"]
            self.ended = True
        return "\n".join(self.lines) + "\n"
