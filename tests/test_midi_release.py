"""Match the approved MIDI rebuild to its source provenance."""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIDI = ROOT / 'vendor/freej2me-web/web/libmidi/libmidi.wasm'
EXPECTED = 'cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98'

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
        self.assertIn('publication pending', notice)
        self.assertTrue((ROOT / 'tools/generate_fm_soundfont.py').is_file())

if __name__ == '__main__':
    unittest.main()
