"""FreeCAD Module startup hook. Invoked when FreeCAD loads the installed addon."""
from pathlib import Path
try:
    import FreeCAD
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from registration import register
    register(FreeCAD, Path(__file__).resolve().parent)
except Exception as exc:
    # Registration error should not stop FreeCAD from starting.
    try:
        FreeCAD.Console.PrintError(f'MILLPWR G2 registration failed: {exc}\n')
    except Exception:
        pass
