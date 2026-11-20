# PoP Mobile original FM General MIDI bank

**Status:** Generated SF2 validated locally with FluidSynth; replacement MIDI Wasm needs an Emscripten build and game-audio test.

- Copyright (C) 2026 PoP Mobile contributors; GPL-3.0-or-later.
- Original source: [`tools/generate_fm_soundfont.py`](../tools/generate_fm_soundfont.py).
- Output: `PoP-Mobile-FM-GM.sf2` (2,392,308 bytes).
- Exact generation command: `python3 tools/generate_fm_soundfont.py PoP-Mobile-FM-GM.sf2`.
- 128 GM melodic program presets (bank 0), 47 drum keys (bank 128, program 0).
- All samples created by mathematical FM/noise synthesis in Python. No audio recordings, third-party SoundFonts, or pre-existing PCM waveforms are incorporated.
- Sound is deliberately synthetic, not a faithful reproduction of acoustic GM instruments; playtesting needed.
- The SF2 is embedded in the WebAssembly MIDI module using generated `gm.h`; it is not loaded directly by the current player.
- Unlike upstream FreeJ2ME's bank, this file contains no Roland samples or metadata.

## Verification

- The generated RIFF/SF2 file was accepted by system `libfluidsynth.so.3` in this environment.
- The validator successfully rendered audible-level (nonzero) samples for all 128 program presets and the 47 GM drum keys.
- SHA-256 is recorded in the release build kit and can be checked using `sha256sum`.

## Copyright and licensing

The generating Python code and resulting generated PCM samples are licensed under GPL-3.0-or-later by the project contributors. Retain the generator, source, full GPL text, and attribution when distributing the embedded bank.
