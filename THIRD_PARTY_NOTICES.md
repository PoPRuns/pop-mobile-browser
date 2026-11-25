# Third-Party Software Notices

This site uses the following third-party software components. Their respective copyrights and licenses remain with their original authors.

## freej2me-web / FreeJ2ME

- Project: https://github.com/zb3/freej2me-web
- Original FreeJ2ME: https://github.com/hex007/freej2me
- License: GNU General Public License version 3 or later
- License text: `vendor/freej2me-web/LICENSE`
- Upstream revision: `c19416e75cbc15f9a27f7e967ee81cb108761e30`
- Corresponding upstream source: https://github.com/zb3/freej2me-web/tree/c19416e75cbc15f9a27f7e967ee81cb108761e30

The emulator includes ObjectWeb ASM, FluidSynth, FFmpeg and x264. The vendored FreeJ2ME `LICENSE` includes the ObjectWeb ASM BSD-style license and attribution. The compiled emulator and its dependencies are distributed in `vendor/freej2me-web/web/`.

**Corresponding source:** [Download the v0.1.0 base source archive](https://github.com/PoPRuns/pop-mobile-browser/releases/download/v0.1.0/pop-mobile-emulator-corresponding-source-v1.tar.gz) (SHA-256: `ad711845e72f1fbbd0491c3642bd2e35b98f4dfd959444e580a88b331cc3fcd9`). The base archive includes the upstream and modified dependency sources, license texts and build scripts. The archive, additional source patches and current site adapter sources together provide the corresponding source for the bundled emulator. See [emulator source and build instructions](https://github.com/PoPRuns/pop-mobile-browser/blob/main/docs/EMULATOR_SOURCE.md) for the current patches, source locations and build provenance.

## MIDI replacement and FluidSynth

- MIDI renderer: customized FluidSynth 2.4.0 source in the corresponding-source bundle (LGPL-2.1-or-later; retain upstream notices).
- Sound bank: **PoP Mobile Original FM GM**, produced entirely by `tools/generate_fm_soundfont.py` (PoP Mobile original source licensed GPL-3.0-or-later).
- The original SoundFont is compiled into the modified `web/libmidi/libmidi.wasm` (SHA-256: `cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98`). Source and build instructions are included in the corresponding source described above.

## FFmpeg and x264

- FFmpeg source: https://github.com/FFmpeg/FFmpeg (tag `n7.1.1`); LGPL-2.1-or-later generally, with GPL-covered features enabled for this build.
- x264 source: https://code.videolan.org/videolan/x264 (commit `fe9e4a7f39d7a9fd208e4592238f9809d5936439`), GPL-2.0-or-later.
- `transcode.wasm` is built using FFmpeg with `--enable-gpl` and `--enable-libx264`. License texts, the x264 patch and build scripts are in the corresponding source.

## CheerpJ

- Project: https://cheerpj.com/
- Licensing: https://cheerpj.com/docs/licensing
- CheerpJ is proprietary software provided by Leaning Technologies.
- PoP Mobile is intended to qualify for the free Community License as a non-commercial open-source project, subject to CheerpJ's current eligibility requirements. CheerpJ is loaded from its official CDN.

Built with CheerpJ.

## Third-party artwork

Certain game-related images are used for identification and illustration. Their inclusion does not transfer copyright or imply endorsement by the original rights holders. See `assets/covers/POPRUNS-LICENSE.txt` for the available attribution information. Redistribution requires appropriate authorization.

## Prince of Persia games

The Prince of Persia games and associated intellectual property belong to their respective rights holders. This site is an independent archival and research project, and the underlying repository hosts no JAR files.
