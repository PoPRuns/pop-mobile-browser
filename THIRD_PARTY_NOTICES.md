# Third-Party Software Notices

This site uses the following third-party software components. Their respective copyrights and licenses remain with their original authors.

## freej2me-web / FreeJ2ME

- Project: https://github.com/zb3/freej2me-web
- Original FreeJ2ME: https://github.com/hex007/freej2me
- License: GNU General Public License version 3 or later
- License text: `vendor/freej2me-web/LICENSE`
- Upstream revision: `c19416e75cbc15f9a27f7e967ee81cb108761e30`
- Corresponding upstream source: https://github.com/zb3/freej2me-web/tree/c19416e75cbc15f9a27f7e967ee81cb108761e30

The emulator includes third-party dependencies with additional licensing requirements, including ObjectWeb ASM, FluidSynth, FFmpeg and x264. The full vendored FreeJ2ME `LICENSE` includes the ObjectWeb ASM BSD-style license and attribution, which apply to the bundled ASM classes. Its compiled Java and WebAssembly artifacts are vendored in `vendor/freej2me-web/web/`. They are published with the site when the GitHub Pages workflow is enabled.

Binary SHA-256 identifiers for this release (FreeJ2ME `c19416e`, with PoP Mobile MIDI replacement):

- `web/freej2me-web.jar`: `ee54975540c927e2978c51dcb47e9828aa5f52a1e0900927a84cc175bfede4a6`
- `web/libmidi/libmidi.wasm`: `cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98`
- `web/libmedia/transcode/transcode.wasm`: `a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b`

The static build adds the PoP Mobile resolution, phone profile, FPS and numpad adapters using `tools/build_pages.py` and the hook source in `server.py`. Build output is not the unmodified upstream `main.js`.

**Complete corresponding source (v0.1.0):** [Download the source archive](https://github.com/PoPRuns/pop-mobile-browser/releases/download/v0.1.0/pop-mobile-emulator-corresponding-source-v1.tar.gz)

SHA-256: `ad711845e72f1fbbd0491c3642bd2e35b98f4dfd959444e580a88b331cc3fcd9`

The archive contains pinned FreeJ2ME source, modified FluidSynth 2.4.0 source, the PoP Mobile original FM General MIDI SoundFont and its generator, FFmpeg 7.1.1, the pinned x264 source and patch, applicable license texts, build scripts and PoP Mobile adapters. The MIDI replacement was rebuilt and tested in Firefox. The original FreeJ2ME Java and media binaries have documented source/build inputs but were not independently reproduced from source.

### Updated Java emulator (issue #11)

The current Java binary includes the [Chapter 1 compatibility source patch](https://github.com/PoPRuns/pop-mobile-browser/blob/main/vendor/freej2me-web/web/source-patches/issue-11-busy-wait.patch). The patch is also distributed at `emulator/source-patches/issue-11-busy-wait.patch` on the deployed site. Use the v0.1.0 corresponding-source archive above as the base, together with all three Java patches and the current site adapter source ([repository](https://github.com/PoPRuns/pop-mobile-browser)). Apply the issue #11, issue #5 and issue #13 patches in that order to the pinned FreeJ2ME source and run `ant -Dant.build.javac.source=1.8` with OpenJDK 17. The original game JAR is not modified. The MIDI and media binaries are unchanged.

### Additional Java emulator update (issue #5)

The current Java binary also includes the [Sands of Time audio busy-wait source patch](https://github.com/PoPRuns/pop-mobile-browser/blob/main/vendor/freej2me-web/web/source-patches/issue-5-audio-busy-wait.patch). It is distributed at `emulator/source-patches/issue-5-audio-busy-wait.patch`. Apply the issue #11 patch first and then the issue #5 patch to the pinned upstream Java source, followed by the issue #13 patch below. Use all three Java patches with the base corresponding-source archive and the current repository adapter sources. Original game JARs and the MIDI and media WebAssembly binaries are unchanged.

### Updated Java emulator (issue #13)

The current Java binary additionally includes the [Harem Adventures startup and audio compatibility source patch](https://github.com/PoPRuns/pop-mobile-browser/blob/main/vendor/freej2me-web/web/source-patches/issue-13-startup-audio-busy-wait.patch). It is distributed at `emulator/source-patches/issue-13-startup-audio-busy-wait.patch` on the deployed site. Apply it after the Chapter 1 and Sands of Time patches and before building with Ant. All three patches are required for the current Java build. The original game JARs and MIDI/media binaries remain unchanged.

## MIDI replacement and FluidSynth

- MIDI renderer: customized FluidSynth 2.4.0 source in the corresponding-source bundle (LGPL-2.1-or-later; retain upstream notices).
- Sound bank: **PoP Mobile Original FM GM**, produced entirely by `tools/generate_fm_soundfont.py` (PoP Mobile original source licensed GPL-3.0-or-later).
- Sound bank SHA-256: `5b1f4a3873294197ee492a182ec955780b495db2ddfeb9635a4faef278cad34e` (file: `web/libmidi/wasm/lib/gm.sf2` in the source package).
- The SoundFont and generated `gm.h` replace the previous upstream bank; the newly rebuilt `libmidi.wasm` is **not an unmodified upstream binary**.
- The earlier Roland-identified MIDI binary and SoundFont **must not be made public**, including through old Git commit history.

## FFmpeg and x264

- FFmpeg source: https://github.com/FFmpeg/FFmpeg (tag `n7.1.1`); LGPL-2.1-or-later generally, with GPL-covered features enabled for this build.
- x264 source: https://code.videolan.org/videolan/x264 (commit `fe9e4a7f39d7a9fd208e4592238f9809d5936439`), GPL-2.0-or-later.
- `transcode.wasm` is built using FFmpeg with `--enable-gpl` and `--enable-libx264`. License texts, the x264 patch and build scripts are in the source package. Do not describe this particular module as LGPL-only.
- The builder specifies Emscripten SDK `3.1.67`.

The local preview server dynamically adds PoP Mobile resolution and numpad-layout adapters to `web/src/main.js` as it serves the JavaScript. The Pages build applies the same hooks to a generated copy using `tools/build_pages.py`. The vendored upstream `main.js` is otherwise unchanged.

## CheerpJ

- Project: https://cheerpj.com/
- Licensing: https://cheerpj.com/docs/licensing
- CheerpJ is proprietary software provided by Leaning Technologies.
- PoP Mobile is intended to qualify for the free Community License as a non-commercial open-source project, subject to CheerpJ's current eligibility requirements. CheerpJ is loaded from its official CDN.

Built with CheerpJ.

## Third-party artwork

Certain game-related images are used for identification and illustration. Their inclusion does not transfer copyright or imply endorsement by the original rights holders. See `assets/covers/POPRUNS-LICENSE.txt` for the available attribution information; verify that any public redistribution of these images is authorized.

## Prince of Persia games

The Prince of Persia games and associated intellectual property belong to their respective rights holders. This site is an independent archival and research project, and the underlying repository hosts no JAR files.
