# MIDI build provenance (2026-11-20)

Upstream freej2me-web: `c19416e75cbc15f9a27f7e967ee81cb108761e30`. New MIDI Wasm built by project maintainer using Emscripten 3.1.67 and matching upstream modified FluidSynth source.

| Artifact | SHA-256 |
| --- | --- |
| `vendor/freej2me-web/web/freej2me-web.jar` | `08ffc41af9e1bf815012a03d87e0af0e894eb98181f42b2302a2febf12b343eb` |
| `vendor/freej2me-web/web/libmidi/libmidi.wasm` | `cfe6a6910c54d5a292b1edf6810f895d588f6c0c2841c7c4c78297097ead1d98` |
| `vendor/freej2me-web/web/libmedia/transcode/transcode.wasm` | `a8831d65180feea3ad3a05911c5197a4ce7fd34e0b5d14e5db038ea9c45c0d5b` |
| Generated `gm.sf2` (in source bundle) | `5b1f4a3873294197ee492a182ec955780b495db2ddfeb9635a4faef278cad34e` |

Inputs reviewed: uploaded MIDI source archive and separately collected FFmpeg/x264 source trees. All binary names/hashes refer to this release candidate. The MIDI rebuild was done on the maintainer's Ubuntu VM; no independent media or Java rebuild was performed in the review environment.

Source release artifact: `pop-mobile-emulator-corresponding-source-v1.tar.gz`. Do not activate public Pages release until this file has been published alongside the binaries and its download link added to notices.
