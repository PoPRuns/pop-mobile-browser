# Emulator source, build provenance and MIDI sound bank

This site bundles a reduced freej2me-web runtime, based on upstream commit [`c19416e75cbc15f9a27f7e967ee81cb108761e30`](https://github.com/zb3/freej2me-web/tree/c19416e75cbc15f9a27f7e967ee81cb108761e30). Its Java build uses upstream sources plus the Chapter 1 patch described below, and its media build uses upstream sources and tools; its MIDI module was rebuilt with an original synthesized SoundFont (to avoid using the runtime's old, Roland-identified MIDI sound bank). See the repository's [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) and [`LICENSE`](../LICENSE) for applicable licenses and attributions.

## Corresponding source for v0.1.0

[Download the complete corresponding-source archive](https://github.com/PoPRuns/pop-mobile-browser/releases/download/v0.1.0/pop-mobile-emulator-corresponding-source-v1.tar.gz) (SHA-256: `ad711845e72f1fbbd0491c3642bd2e35b98f4dfd959444e580a88b331cc3fcd9`). The release bundle contains the pinned upstream FreeJ2ME source and Java build scripts, modified FluidSynth 2.4.0 source, the original generated SoundFont and its generator, FFmpeg 7.1.1, pinned x264 commit `fe9e4a7f39d7a9fd208e4592238f9809d5936439` and patch, corresponding WebAssembly build scripts, and this site's adapter sources. The media build specifies Emscripten SDK `3.1.67`; FFmpeg was built with GPL features and x264.

## Chapter 1 runtime compatibility fix (issue #11)

The current Java emulator adds the [Chapter 1 source patch](https://github.com/PoPRuns/pop-mobile-browser/blob/main/vendor/freej2me-web/web/source-patches/issue-11-busy-wait.patch) to the pinned upstream Java source above. It matches the exact SHA-256 of the affected `prince/l` class and inserts a 1 ms sleep into its busy-wait loop at class load time, leaving the original game JAR and its 110 ms frame target unchanged. Precise timing equivalence has not been established. The MIDI and media WebAssembly builds are unchanged. The v0.1.0 archive remains the base corresponding-source bundle; use it together with this patch and the current site adapter source in this repository.

Rebuild the Java component from a clean checkout of the pinned upstream commit using OpenJDK 17 and Apache Ant: apply the patch with `git apply /path/to/issue-11-busy-wait.patch`, then run `ant -Dant.build.javac.source=1.8`. Copy only `web/freej2me-web.jar` into the site vendor directory.

## Published binary fingerprints

| Component | SHA-256 |
| --- | --- |
| `vendor/freej2me-web/web/freej2me-web.jar` | `70d84f5335e16842cdda59249af83e98dfa18c1da713a0a12364715b6f4961ce` |
| `vendor/freej2me-web/web/libmidi/libmidi.wasm` | `cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98` |
| `vendor/freej2me-web/web/libmedia/transcode/transcode.wasm` | `a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b` |
| Generated `gm.sf2` within source bundle | `5b1f4a3873294197ee492a182ec955780b495db2ddfeb9635a4faef278cad34e` |

## Original FM General MIDI SoundFont

The *PoP Mobile Original FM GM* SoundFont and generated PCM samples are licensed GPL-3.0-or-later by PoP Mobile contributors. Source: [`tools/generate_fm_soundfont.py`](../tools/generate_fm_soundfont.py).
The generator creates its samples mathematically using FM/noise synthesis; it uses no third-party sample recordings. Its output covers 128 GM melodic programs and 47 supported drum notes. It is intentionally retro/synthetic, not an acoustic instrument emulation. To regenerate the `.sf2` from the repository root:

```sh
python3 tools/generate_fm_soundfont.py PoP-Mobile-FM-GM.sf2
sha256sum PoP-Mobile-FM-GM.sf2
```

The expected output SHA-256 is the `gm.sf2` fingerprint above. The SoundFont is compiled into `libmidi.wasm` using generated `gm.h`; it is not downloaded at runtime. Its Emscripten/FluidSynth build inputs are included in the release source archive. Running the Python generator alone does not rebuild Wasm.

## Pages build and validation

`tools/build_pages.py` generates the browser-ready `emulator/src/main.js` from unmodified upstream `web/src/main.js` using resolution, phone profile, FPS and numpad hooks defined in `server.py`. The source-only `docs/` directory is intentionally excluded from the Pages artifact. The released site includes the required license/third-party notices and links to the corresponding-source release above.

Test locally with `python3 -m unittest discover -s tests -p 'test_*.py'`, `node tests/test_jar_library.cjs`, `node tests/test_pages_sw.cjs`, and `python3 tools/build_pages.py`. A browser audio acceptance test is still useful after future binary changes.
