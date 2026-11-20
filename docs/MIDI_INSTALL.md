# Install the rebuilt MIDI module in your private PoP Mobile working checkout

Apply this drop-in update after the earlier **Pages + licensing** update was installed. It contains the maintainer-built replacement `libmidi.wasm`, notices, original sound bank generator and tests. It does **not** delete your earlier Git commits or change repository visibility.

```sh
cd ~/pop-mobile-browser
unzip -o ~/Downloads/pop-mobile-midi-verified-update.zip -d .
python3 -m unittest discover -s tests -p 'test_*.py'
node tests/test_jar_library.cjs
node tests/test_pages_sw.cjs
python3 tools/build_pages.py
python3 server.py --jar-source local
```

Then open http://127.0.0.1:8000/ with Firefox and play an actual MIDI-using JAR. Review `docs/MIDI_AUDIO_TEST.md`. When it plays acceptably, commit this change to your **private** development repository.

**Do not publish the original private Git history.** The old binary remains in its earlier commits. See `docs/PUBLIC_REPOSITORY.md` for the later clean-public-history procedure.

The combined source bundle `pop-mobile-emulator-corresponding-source-v1.tar.gz` is a **separate artifact** to be published as a versioned release download when the public release is ready. Do not unzip it over your working project and do not add the 27 MB source tarball directly to your regular repository unless you deliberately want to carry it there.
