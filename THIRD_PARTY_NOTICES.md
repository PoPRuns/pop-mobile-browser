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

- `web/freej2me-web.jar`: `08ffc41af9e1bf815012a03d87e0af0e894eb98181f42b2302a2febf12b343eb`
- `web/libmidi/libmidi.wasm`: `cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98`
- `web/libmedia/transcode/transcode.wasm`: `a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b`

The static build adds the PoP Mobile resolution and numpad adapters using `tools/build_pages.py` and the hook source in `server.py`. Build output is not the unmodified upstream `main.js`.

**Corresponding-source status (publication pending):** An offline source bundle has been assembled as `pop-mobile-emulator-corresponding-source-v1.tar.gz`, including the full pinned FreeJ2ME/modified FluidSynth source, the original synthesized GM SoundFont source and build inputs, FFmpeg 7.1.1, x264 at `fe9e4a7f39d7a9fd208e4592238f9809d5936439` with patch, and PoP Mobile's adapter source. **It is not published at a public URL yet.** Before enabling the Pages deployment, upload that release asset to the public repository (and make a working direct link available here and beside the runtime), verify the exact archived source corresponds to the shipped binaries, and complete the release checklist in `docs/SOURCE_COMPLIANCE.md`. The media source was collected and inspected but was not independently rebuilt to match the shipped `transcode.wasm`.

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
