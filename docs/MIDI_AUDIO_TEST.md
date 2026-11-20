# MIDI audio acceptance test

The new synthesized SoundFont is smaller and intentionally sounds different from the upstream bank. Matching WebAssembly symbols only proves interface compatibility, not audio quality.

## Local test on Ubuntu

1. Keep a backup of the working project or rely on the existing **private** Git repository. Apply the ZIP update from the `~/pop-mobile-browser` directory.
2. Run `python3 -m unittest discover -s tests -p 'test_*.py'` and, if Node.js is installed, `node tests/test_jar_library.cjs` and `node tests/test_pages_sw.cjs`.
3. Start `python3 server.py --jar-source local` and open `http://127.0.0.1:8000/` in Firefox. Don't use `file://`.
4. Choose a build known to play a MIDI soundtrack, press **Play**, and allow CheerpJ to initialize. If audio is blocked, click or interact with the game and check tab muting/Firefox autoplay settings.
5. Listen for a recognisable tune, non-silent notes, no constant clipping or unexpectedly loud output, and reasonably smooth game responsiveness. Change the numpad toggle to check controls still work.
6. Restart the player and test a second suitable build. Note the game/build SHA-256, which mode you tested, whether the music played, and any Firefox console errors.
7. Run `python3 tools/build_pages.py` to verify the static website bundles the replacement binary; this isn't a substitute for testing the deployed static site in Firefox.

**Do not set the Pages publication variable or make a repo public merely because the unit tests pass.**
