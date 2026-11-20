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
        self.assertIn("setJarStatus('');", script)
        self.assertNotIn("JAR not cached. Open its SHA-256 entry",script)
        self.assertIn("el.hidden = !message", script)

    def test_status_messages_are_temporary_and_reports_identify_the_build(self):
        script = (ROOT / "assets/app.js").read_text()
        html = (ROOT / "catalogue.html").read_text()
        self.assertIn("const JAR_STATUS_DURATION_MS = 5000", script)
        self.assertIn("clearTimeout(jarStatusTimer)", script)
        self.assertIn("el.hidden = true", script)
        self.assertIn("setJarStatus(''); // Clear a pending notification", script)
        self.assertIn('id="player-report-issue"', html)
        self.assertIn('target="_blank" rel="noopener noreferrer"', html)
        for field in ('build.sha256', 'build.sourceFilenames', 'build.vendor', 'build.version', 'build.size', 'build.game'):
            self.assertIn(field, script)
        self.assertIn("issueUrl.searchParams.set('body', body)", script)
        self.assertIn("$('player-report-issue').href = playerIssueUrl(build)", script)
        self.assertIn("$('play-heading').textContent = [build.name, build.resolution].filter(Boolean).join(' · ')", script)
        self.assertNotIn('→ ${screen.width}', script)

    def test_local_vs_browser_source_preflight(self):
        script = (ROOT / "assets/app.js").read_text()
        lib = (ROOT / "assets/jar-library.js").read_text()
        self.assertIn("async function loadVerifiedLocal(build, ticket)", script)
        self.assertIn("async function reachableLocal(build)", lib)
        self.assertIn("return (await response.blob()).size === Number(build.size);",lib)

if __name__ == "__main__":
    unittest.main()
