# MILLPWR G2 CAM postprocessor for FreeCAD 1.1.x

**EXPERIMENTAL: NO LIVE CUTTING.** This repository targets ACU-RITE MILLPWR G2 on ACER E-MILL 3VKH-54. Its output has not been verified in a real FreeCAD installation or controller. It is not a substitute for a safe machine setup, interlocks, or operator verification.

## Install with FreeCAD Addon Manager (once hosted in Git)

1. Push the *contents* of this directory to a GitHub or GitLab repository; the `package.xml` must be at repository root. The supplied ZIP is a source release, not a hosted Git repository.
2. FreeCAD 1.1.4: **Tools > Addon Manager > Configure > Custom repositories**, enter the Git repository URL and add/install it. Exact UI may vary.
3. Restart FreeCAD. `Init.py` should execute on startup, adding the postprocessor import directory to Python's search path and making a symlink from FreeCAD's actual macro directory to the Git-managed `postprocessors/millpwr_g2_post.py`. It does not overwrite a pre-existing file or symlink.
4. **View > Panels > Python console** and run the verification below. If registration fails, look in **View > Panels > Report view**.
5. In **CAM** choose `millpwr_g2` as the Job postprocessor, create a simple 3-axis metric path with explicit tool controller and export `.nc`.

### Verify registration in FreeCAD Python console

```python
import FreeCAD as App
import Path
from pathlib import Path as FSPath
print('Macro:', App.getUserMacroDir())
print('CAM post paths:', Path.Preferences.searchPathsPost())
print('Available:', Path.Preferences.allAvailablePostProcessors())
print('Linked:', (FSPath(App.getUserMacroDir()) / 'millpwr_g2_post.py').is_symlink())
```

If it is not listed, confirm where the addon was installed via `App.getUserAppDataDir()` and check that `Init.py` ran. FreeCAD user macro path is determined at runtime, so this works with Flatpak without hardcoding `~/.var/app/...`. It assumes Flatpak permits symlinks inside the FreeCAD user data directory.

## File design

- `Init.py`: FreeCAD startup registration.
- `registration.py`: idempotent macro-directory symlink; won't replace existing files.
- `postprocessors/millpwr_g2_post.py`: legacy FreeCAD CAM `export(objectslist, filename, argstring)` adapter, supported by the FreeCAD 1.1.4 compatibility wrapper.
- `postprocessors/millpwr_dialect.py`: strict, stdlib-only metric G-code formatting.
- `tests/`: fake FreeCAD CAM objects plus path registration tests.

## Development tests

```bash
python3 -m unittest discover -s tests -v
```

If VS Code is not showing tests, use **Python: Configure Tests** and choose **unittest** with:

- start directory: `tests`
- pattern: `test_*.py`

This repository includes a workspace [settings.json](/home/tim/Documents/projects/freecad-addon-post-millpwr-g2/.vscode/settings.json) that matches that configuration.

CI runs Python 3.11 and 3.13; this is **not** a substitute for a FreeCAD GUI integration test.

## Controller safety and limitations

Current commands: G0/G1/G2/G3 with XYZ and IJK, G17/G21/G40/G64/G80/G90, Tn, M0/M1/M2/M3/M4/M5/M7/M8/M9, S and F. Unknown commands intentionally fail. G20, G91, G54+, G43, cutter comp, canned cycles and unsupported formats fail. No automatic tool-length compensation is generated; tool numbers and actual offsets must be matched to the controller's library. Confirm arc-center conventions, supported G/M codes, datum conventions, spindle/coolant control, and machine travel against the *installed firmware/manual* before any machining.

Do not run this code unattended. Compare to known-good NC samples, inspect the CNC graphical preview, then dry-run with tool clear of stock/clamps and reduced override in a safe setup.

### Uninstall

Remove the addon via Addon Manager, and remove **only** the symlink `millpwr_g2_post.py` in the macro directory (do not delete an unrelated existing file). Before uninstalling, record the macro path using `App.getUserMacroDir()`.

## References

- [FreeCAD 1.1.4 postprocessor factory](https://github.com/FreeCAD/FreeCAD/blob/1.1.4/src/Mod/CAM/Path/Post/Processor.py)
- [FreeCAD Addon Manager](https://github.com/FreeCAD/AddonManager)
- [FreeCAD CAM postprocessor customization](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/CAM_Postprocessor_Customization.md)
