"""A language pack must not count as a deployed CDUMM overlay."""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
runtime = Path(os.environ["APPDIR"]) / "share/amethyst-mod-manager" if os.environ.get("APPDIR") else REPO / "src"
sys.path.insert(0, str(runtime))
spec = importlib.util.spec_from_file_location(
    "crimson_test_backend", REPO / "src/Games/Crimson Desert/crimson_desert_backend.py"
)
backend = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backend
spec.loader.exec_module(backend)


class OverlayVerificationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.game = Path(self.tmp.name)
        (self.game / "meta").mkdir()
        (self.game / "meta/0.papgt").write_bytes(b"0037\0")
        voice = self.game / "0037"
        voice.mkdir()
        (voice / "0.paz").write_bytes(b"voice")
        (voice / "0.pamt").write_bytes(b"voice index")

    def test_reserved_voice_pack_is_not_an_overlay(self):
        with self.assertRaises(backend.CrimsonBackendError):
            backend.verify_overlay(self.game)

    def test_overlay_must_also_be_registered(self):
        overlay = self.game / "0041"
        overlay.mkdir()
        (overlay / "_cdumm_overlay.marker").write_text("overlay_dir=0041\n")
        (overlay / "0.paz").write_bytes(b"modded data")
        (overlay / "0.pamt").write_bytes(b"modded index")
        with self.assertRaises(backend.CrimsonBackendError):
            backend.verify_overlay(self.game)
        (self.game / "meta/0.papgt").write_bytes(b"0037\0" + b"0041\0")
        backend.verify_overlay(self.game)


if __name__ == "__main__":
    unittest.main()
