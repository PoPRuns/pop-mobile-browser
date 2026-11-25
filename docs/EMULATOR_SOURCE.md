# Emulator source, build provenance and MIDI sound bank

This site bundles a reduced freej2me-web runtime, based on upstream commit [`c19416e75cbc15f9a27f7e967ee81cb108761e30`](https://github.com/zb3/freej2me-web/tree/c19416e75cbc15f9a27f7e967ee81cb108761e30). Its Java build uses upstream sources plus the runtime compatibility patches described below, and its media build uses upstream sources and tools; its MIDI module was rebuilt with an original synthesized SoundFont (to avoid using the runtime's old, Roland-identified MIDI sound bank). See the repository's [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) and [`LICENSE`](../LICENSE) for applicable licenses and attributions.

## Corresponding source for v0.1.0

[Download the complete corresponding-source archive](https://github.com/PoPRuns/pop-mobile-browser/releases/download/v0.1.0/pop-mobile-emulator-corresponding-source-v1.tar.gz) (SHA-256: `ad711845e72f1fbbd0491c3642bd2e35b98f4dfd959444e580a88b331cc3fcd9`). The release bundle contains the pinned upstream FreeJ2ME source and Java build scripts, modified FluidSynth 2.4.0 source, the original generated SoundFont and its generator, FFmpeg 7.1.1, pinned x264 commit `fe9e4a7f39d7a9fd208e4592238f9809d5936439` and patch, corresponding WebAssembly build scripts, and this site's adapter sources. The media build specifies Emscripten SDK `3.1.67`; FFmpeg was built with GPL features and x264.

## Runtime compatibility patches

The bundled Java emulator includes the following patches to address playback and performance issues:

| Issue | Game | Fix |
|---|---|---|
| [#11](https://github.com/PoPRuns/pop-mobile-browser/issues/11) | Harem Adventures – Chapter 1 | Added a 1 ms sleep to frame-deadline polling in `prince/l`. |
| [#5](https://github.com/PoPRuns/pop-mobile-browser/issues/5) | Sands of Time | Added a 1 ms sleep to audio polling in `F.run()`. |
| [#13](https://github.com/PoPRuns/pop-mobile-browser/issues/13) | Harem Adventures | Added 1 ms sleeps to paused-state polling in `F.run()` and audio polling in `L.run()`. |

All fixes are applied at class load time using exact SHA-256 class fingerprints. Original game JARs, frame interval targets and MIDI/media binaries remain unchanged. Precise timing equivalence has not been established.

To rebuild the current Java component, apply the following patches to the pinned upstream revision using `git apply`, in this order:

1. [issue-11-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-11-busy-wait.patch)
2. [issue-5-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-5-audio-busy-wait.patch)
3. [issue-13-startup-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-13-startup-audio-busy-wait.patch)

Build using OpenJDK 17 and Apache Ant (`ant -Dant.build.javac.source=1.8`), then copy `web/freej2me-web.jar` into the site vendor directory.

The v0.1.0 corresponding-source archive, the patches above and the current site adapter sources together constitute the corresponding source for the current release.

## Published binary fingerprints

| Component | SHA-256 |
| --- | --- |
| `vendor/freej2me-web/web/freej2me-web.jar` | `ee54975540c927e2978c51dcb47e9828aa5f52a1e0900927a84cc175bfede4a6` |
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
