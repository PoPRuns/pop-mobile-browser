"""Regression: never start an emulator iframe without a known JAR source."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class TestPlayerJarGate(unittest.TestCase):
    def test_player_uses_verification_gate(self):
        script = (ROOT / "assets/app.js").read_text()
        self.assertIn("state.readyPlaySha !== state.selectedPlay", script)
        self.assertIn("$('restart-play').disabled = true", script)
        self.assertIn("jarLibrary.reachableLocal(build)", script)
        self.assertIn("await jarLibrary.cached(build)", script)
        self.assertIn("await jarLibrary.storeFile(build, file)", script)
        self.assertIn("JAR not cached", script)

    def test_local_vs_browser_source_preflight(self):
        script = (ROOT / "assets/app.js").read_text()
        lib = (ROOT / "assets/jar-library.js").read_text()
        self.assertIn("async function loadVerifiedLocal(build, ticket)", script)
        self.assertIn("async function reachableLocal(build)", lib)
        self.assertIn("return (await response.blob()).size === Number(build.size);",lib)

if __name__ == "__main__":
    unittest.main()
