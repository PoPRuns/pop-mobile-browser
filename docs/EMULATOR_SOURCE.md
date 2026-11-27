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
| [#6](https://github.com/PoPRuns/pop-mobile-browser/issues/6) | Sands of Time (Sharp GX10) | Remapped CJSP sound references in `pop2/e` to the Vodafone sound API. Startup works; SMAF/MMF playback remains unsupported. |
| [#7](https://github.com/PoPRuns/pop-mobile-browser/issues/7) | Sands of Time | Restored standard key callbacks and corrected inherited repaint method references in the CanvasPlus-based `pop2/e` class. |
| [#31](https://github.com/PoPRuns/pop-mobile-browser/issues/31) | Sands of Time | Extended the issue #5 audio polling workaround to another verified `F.class` fingerprint. |
| [#8](https://github.com/PoPRuns/pop-mobile-browser/issues/8) | Sands of Time | Added a null fallback for the `MIDlet-Jar-URL` lookup in the verified `d.c()` method across three class fingerprints (four JAR builds). |
| [#9](https://github.com/PoPRuns/pop-mobile-browser/issues/9) | Sands of Time | Extended the audio polling workaround to the verified `b.run()` class fingerprint, replacing its idle yield with a 1 ms sleep. |
| [#15](https://github.com/PoPRuns/pop-mobile-browser/issues/15) | Warrior Within | Redirected the verified `a.run()` audio polling yield to an interruption-safe 1 ms sleep, preserving the original main game loop. |
| [#17](https://github.com/PoPRuns/pop-mobile-browser/issues/17) | Warrior Within | Decode single-byte text in the verified German `c.class` decoder without relying on the default charset, preventing out-of-range font lookup indices. |
| [#18](https://github.com/PoPRuns/pop-mobile-browser/issues/18) | Warrior Within | Insert an interruption-safe 1 ms sleep at the verified `d.run()` audio polling loop header (CRC32 `4505D84D`); the other two builds are addressed in #35. |
| [#35](https://github.com/PoPRuns/pop-mobile-browser/issues/35) | Warrior Within | Insert an interruption-safe 1 ms sleep at the verified `e.run()` audio polling back edge (CRC32 `BE81D1D7` and `421E90B1`). |
| [#20](https://github.com/PoPRuns/pop-mobile-browser/issues/20) | Warrior Within | Allocate the missing one-byte level-read buffer in the verified `Z.class` (CRC32 `97C913AD`), preserving bytecode offsets and original level resources. |
| [#21](https://github.com/PoPRuns/pop-mobile-browser/issues/21) | Warrior Within | Extend single-byte text decoding to the verified Czech `a.class` (CRC32 `5E9733BD`), retaining the issue #17 decoder mapping. |

All fixes are applied at class load time using exact SHA-256 class fingerprints. Original game JARs, frame interval targets and MIDI/media binaries remain unchanged. Precise timing equivalence has not been established.

To rebuild the current Java component, apply the following patches to the pinned upstream revision using `git apply`, in this order:

1. [issue-11-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-11-busy-wait.patch)
2. [issue-5-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-5-audio-busy-wait.patch)
3. [issue-13-startup-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-13-startup-audio-busy-wait.patch)
4. [issue-6-cjsp-sound-api.patch](../vendor/freej2me-web/web/source-patches/issue-6-cjsp-sound-api.patch)
5. [issue-7-input-callback.patch](../vendor/freej2me-web/web/source-patches/issue-7-input-callback.patch)
6. [issue-31-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-31-audio-busy-wait.patch)
7. [issue-8-missing-jad-url.patch](../vendor/freej2me-web/web/source-patches/issue-8-missing-jad-url.patch)
8. [issue-8-additional-jad-url-builds.patch](../vendor/freej2me-web/web/source-patches/issue-8-additional-jad-url-builds.patch)
9. [issue-9-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-9-audio-busy-wait.patch)
10. [issue-15-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-15-audio-busy-wait.patch)
11. [issue-17-text-encoding.patch](../vendor/freej2me-web/web/source-patches/issue-17-text-encoding.patch)
12. [issue-18-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-18-audio-busy-wait.patch)
13. [issue-35-audio-busy-wait.patch](../vendor/freej2me-web/web/source-patches/issue-35-audio-busy-wait.patch)
14. [issue-20-level-loading.patch](../vendor/freej2me-web/web/source-patches/issue-20-level-loading.patch)
15. [issue-21-text-encoding.patch](../vendor/freej2me-web/web/source-patches/issue-21-text-encoding.patch)

Build using OpenJDK 17 and Apache Ant (`ant -Dant.build.javac.source=1.8`), then copy `web/freej2me-web.jar` into the site vendor directory.

The v0.1.0 corresponding-source archive, the patches above and the current site adapter sources together constitute the corresponding source for the current release.

## Published binary fingerprints

| Component | SHA-256 |
| --- | --- |
| `vendor/freej2me-web/web/freej2me-web.jar` | `b40fd915382f8ec1c19b47f33e7c1e7bf7b2fb365ba32c77f240d2525390ccfd` |
| `vendor/freej2me-web/web/libmidi/libmidi.wasm` | `cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98` |
| `vendor/freej2me-web/web/libmedia/transcode/transcode.wasm` | `a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b` |
| Generated `gm.sf2` within source bundle | `5b1f4a3873294197ee492a182ec955780b495db2ddfeb9635a4faef278cad34e` |

The base archive predates the Java compatibility patches. Use the patches listed above and the current adapter sources when reproducing the bundled runtime. The original upstream media binary has documented source/build inputs but has not been independently reproduced by this project.

## Original FM General MIDI SoundFont

The *PoP Mobile Original FM GM* SoundFont and generated PCM samples are licensed GPL-3.0-or-later by PoP Mobile contributors. Source: [`tools/generate_fm_soundfont.py`](../tools/generate_fm_soundfont.py).
The generator creates its samples mathematically using FM/noise synthesis; it uses no third-party sample recordings. Its output covers 128 GM melodic programs and 47 supported drum notes. It is intentionally retro/synthetic, not an acoustic instrument emulation. To regenerate the `.sf2` from the repository root:

```sh
python3 tools/generate_fm_soundfont.py PoP-Mobile-FM-GM.sf2
sha256sum PoP-Mobile-FM-GM.sf2
```

The expected output SHA-256 is the `gm.sf2` fingerprint above. The SoundFont is compiled into `libmidi.wasm` using generated `gm.h`; it is not downloaded at runtime. Its Emscripten/FluidSynth build inputs are included in the release source archive. Running the Python generator alone does not rebuild Wasm. The rebuilt MIDI module was tested in Firefox. The earlier Roland-identified MIDI binary and SoundFont must not be published, including through Git history.

## Phone profile selection

The catalogue importer derives a `phoneType` hint from the workbook's `Device(s)` column. Recognized single-manufacturer entries select Nokia, Siemens, Motorola or SonyEricsson; unknown, unsupported and mixed entries use the emulator's Nokia default. This is a compatibility hint, not full hardware emulation. The original device text remains unchanged.

The player's manual phone profile override is saved in browser storage per JAR SHA-256. Existing catalogues without `phoneType` retain the emulator's previous behavior until reimported. Older manual settings are not automatically migrated because they may be shared by multiple builds.

## Pages build and validation

`tools/build_pages.py` generates the browser-ready `emulator/src/main.js` from unmodified upstream `web/src/main.js` using resolution, phone profile, FPS and numpad hooks defined in `server.py`. The source-only `docs/` directory is intentionally excluded from the Pages artifact. The released site includes the required license/third-party notices and links to the corresponding-source release above.

Test locally with `python3 -m unittest discover -s tests -p 'test_*.py'`, `node tests/test_jar_library.cjs`, `node tests/test_pages_sw.cjs`, and `python3 tools/build_pages.py`. A browser audio acceptance test is still useful after future binary changes.
