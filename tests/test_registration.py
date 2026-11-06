import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from registration import install_link, register


class TestRegistration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'addon'
        (self.root / 'postprocessors').mkdir(parents=True)
        (self.root / 'postprocessors' / 'millpwr_g2_post.py').write_text('pass\n')
        self.macro = Path(self.temp.name) / 'macro'

    def test_creates_symlink(self):
        link = install_link(self.root, self.macro)
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), (self.root / 'postprocessors' / link.name).resolve())

    def test_idempotent(self):
        self.assertEqual(install_link(self.root, self.macro), install_link(self.root, self.macro))

    def test_does_not_overwrite_existing_file(self):
        self.macro.mkdir()
        (self.macro / 'millpwr_g2_post.py').write_text('custom')
        with self.assertRaises(FileExistsError):
            install_link(self.root, self.macro)
        self.assertEqual((self.macro / 'millpwr_g2_post.py').read_text(), 'custom')

    def test_does_not_overwrite_foreign_link(self):
        self.macro.mkdir()
        foreign = Path(self.temp.name) / 'foreign.py'
        foreign.write_text('pass')
        (self.macro / 'millpwr_g2_post.py').symlink_to(foreign)
        with self.assertRaises(FileExistsError):
            install_link(self.root, self.macro)

    def test_register_adds_import_path(self):
        fake_freecad = SimpleNamespace(getUserMacroDir=lambda: str(self.macro))
        register(fake_freecad, self.root)
        self.assertIn(str((self.root / 'postprocessors').resolve()), sys.path)
        self.assertTrue((self.macro / 'millpwr_g2_post.py').is_symlink())

    def test_missing_source_fails(self):
        (self.root / 'postprocessors' / 'millpwr_g2_post.py').unlink()
        with self.assertRaises(FileNotFoundError):
            install_link(self.root, self.macro)


if __name__ == '__main__':
    unittest.main()
