"""Match the approved MIDI rebuild to its source provenance."""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIDI = ROOT / 'vendor/freej2me-web/web/libmidi/libmidi.wasm'
EXPECTED = 'cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98'
SOURCE_RELEASE_URL = 'https://github.com/PoPRuns/pop-mobile-browser/releases/download/v0.1.0/pop-mobile-emulator-corresponding-source-v1.tar.gz'
SOURCE_RELEASE_SHA256 = 'ad711845e72f1fbbd0491c3642bd2e35b98f4dfd959444e580a88b331cc3fcd9'

class MidiReleaseTests(unittest.TestCase):
    def test_replacement_is_present_and_not_upstream_bank(self):
        wasm = MIDI.read_bytes()
        self.assertEqual(wasm[:4], b'\x00asm')
        self.assertEqual(hashlib.sha256(wasm).hexdigest(), EXPECTED)
        self.assertIn(b'PoP Mobile Original FM GM', wasm)
        self.assertNotIn(b'Roland', wasm)

    def test_notices_track_new_build(self):
        notice = (ROOT / 'THIRD_PARTY_NOTICES.md').read_text()
        self.assertIn(EXPECTED, notice)
        self.assertIn(SOURCE_RELEASE_URL, notice)
        self.assertIn(SOURCE_RELEASE_SHA256, notice)
        self.assertNotIn('publication pending', notice.lower())
        self.assertTrue((ROOT / 'tools/generate_fm_soundfont.py').is_file())

if __name__ == '__main__':
    unittest.main()
