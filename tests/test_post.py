import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "postprocessors"))
from millpwr_dialect import Dialect, PostError
from millpwr_g2_post import export


def cmd(name, **params):
    return SimpleNamespace(Name=name, Parameters=params)


def job(*commands):
    return [SimpleNamespace(Path=SimpleNamespace(Commands=list(commands)))]


class TestDialect(unittest.TestCase):
    def test_header_and_footer(self):
        g = Dialect().finish()
        self.assertIn("G21 G17 G90 G40 G80", g)
        self.assertTrue(g.endswith("M5\nM9\nM2\n"))

    def test_moves_and_feed(self):
        d = Dialect()
        d.emit("G0", {"X": 10, "Y": 0, "Z": 5})
        d.emit("G1", {"X": -2.125, "F": 100})
        self.assertIn("G0 X10 Y0 Z5", d.finish())
        self.assertIn("G1 X-2.125 F100", d.finish())

    def test_arc_incremental_center(self):
        d = Dialect()
        d.emit("G2", {"X": 12, "Y": 4, "I": 1, "J": -1})
        self.assertIn("G2 X12 Y4 I1 J-1", d.finish())

    def test_tool_selection_and_m6(self):
        d = Dialect()
        d.emit("T3")
        d.emit("M6")
        self.assertIn("\nT3\n", d.finish())
        self.assertNotIn("M6", d.finish())

    def test_no_m6_without_tool(self):
        with self.assertRaises(PostError):
            Dialect().emit("M6")

    def test_reject_unsupported_codes(self):
        for code in ("G28", "G54", "G81", "G91", "G43", "M30"):
            with self.subTest(code=code), self.assertRaises(PostError):
                Dialect().emit(code)

    def test_reject_unsafe_arcs(self):
        for kwargs in ({"X": 1, "Y": 2, "R": 3}, {"X": 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(PostError):
                Dialect().emit("G3", kwargs)

    def test_nan_rejected(self):
        with self.assertRaises(PostError):
            Dialect().emit("G0", {"X": float("nan")})

    def test_metric_only(self):
        with self.assertRaises(PostError):
            Dialect().emit("G20")

    def test_no_commands_after_end(self):
        d = Dialect()
        d.emit("M2")
        with self.assertRaises(PostError):
            d.emit("G0", {"X": 1})


class TestFreeCADAdapter(unittest.TestCase):
    def test_export_file_and_contents(self):
        with tempfile.TemporaryDirectory() as td:
            filename = os.path.join(td, "part.nc")
            output = export(job(cmd("T2"), cmd("M6"), cmd("G0", X=0, Y=0, Z=10),
                                cmd("G1", Z=-1, F=100), cmd("G0", Z=10)), filename, "")
            with open(filename, encoding="ascii") as stream:
                self.assertEqual(output, stream.read())
            self.assertIn("T2\nG0 X0 Y0 Z10\nG1 Z-1 F100", output)

    def test_failure_does_not_write_partial_file(self):
        with tempfile.TemporaryDirectory() as td:
            filename = os.path.join(td, "part.nc")
            with self.assertRaises(PostError):
                export(job(cmd("G0", X=1), cmd("G81", Z=-2)), filename, "")
            self.assertFalse(os.path.exists(filename))

    def test_no_empty_job(self):
        with self.assertRaises(PostError):
            export([], None, "")

    def test_reject_unknown_args(self):
        with self.assertRaises(PostError):
            export(job(cmd("G0", X=1)), None, "--units inch")


if __name__ == "__main__":
    unittest.main()
