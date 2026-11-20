# Source and publication checklist (MIDI replacement candidate)

**Status: not yet approved for a public release.** This is an engineering audit, not legal advice.

## Verified against the maintainer's Ubuntu build

- Source revision: freej2me-web `c19416e75cbc15f9a27f7e967ee81cb108761e30`.
- New `libmidi.wasm`: **cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98**, 2,631,359 bytes.
- FreeJ2ME `freej2me-web.jar`: **08ffc41af9e1bf815012a03d87e0af0e894eb98181f42b2302a2febf12b343eb**.
- Original media `transcode.wasm`: **a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b**.
- Original synthesized replacement GM SoundFont: **5b1f4a3873294197ee492a182ec955780b495db2ddfeb9635a4faef278cad34e**.
- New MIDI Wasm has valid WebAssembly format, all 18 original exported names, the same two imports, and contains the replacement SoundFont bytes. A text search found no `Roland` identifier.
- The uploaded MIDI source archive contains the exact new `.wasm`, generated `gm.sf2`/`gm.h`, generator, modified FluidSynth and build scripts. It contains no `init.zip` or upstream old SoundFont.
- FFmpeg 7.1.1 and pinned x264 source with applied patch were previously collected. The assembled release bundle puts them at the build script's expected paths.

## Before publication

1. **Gameplay acceptance:** Test a Java ME game that really uses MIDI in Firefox/PoP Mobile after installing the new binary. Check the sound at normal volume, switching games and restarting. Test a static `_site` preview if possible.
2. **Source availability:** Publish `pop-mobile-emulator-corresponding-source-v1.tar.gz` to the eventual **public** repository as a versioned release asset *before or together with* the binary deployment. Add a confirmed working URL to `THIRD_PARTY_NOTICES.md`, and make the link accessible from the Pages website. GPLv3 §6(d) requires equivalent access to source from the same distribution channel. Confirm actual archive contents and license requirements.
3. **Media/Java build review:** Full versions/build scripts are included, but an independent reconstruction of the original `transcode.wasm` and Java binary is not yet demonstrated. Review source versions/patches and preserve any additional third-party notices.
4. **Cover-art rights:** The six current JPEG cover images are game/publisher artwork; don't assume site-code licensing covers them. Obtain permission or prepare a clean public snapshot with only original abstract/CSS title cards.
5. **Git history:** The private development repository's earlier commit includes the original MIDI Wasm and artwork. **Do not turn that existing history public**, even after new replacements. Keep it private; create a separate clean public repository history from a reviewed working-tree export (or use carefully reviewed history rewriting).
6. **CheerpJ:** Confirm project meets current Community License terms. Keep the official CDN and visible *Built with CheerpJ* credit.
7. **Pages:** Keep `POP_MOBILE_PUBLICATION_APPROVED` unset until the public repository and source URL are ready and actual browser testing passes.

## Next action

Install the patched `libmidi.wasm` and run the local browser smoke test described in `docs/MIDI_AUDIO_TEST.md`. Then prepare the clean public snapshot and release assets. Don't delete your private repo.
