# PoP Mobile Browser

[PoP Mobile](https://popruns.github.io/pop-mobile-browser/) is an independent archival catalogue of Prince of Persia Java ME builds, featuring detailed metadata and the option to run JARs in a browser using freej2me-web and CheerpJ.

**No Prince of Persia game JAR files are included in this repository or hosted by the website.** Players supply their own matching JARs.

## Play a game

1. Open the [website](https://popruns.github.io/pop-mobile-browser/), select a game and a JAR build, and click *Play / Load*. If the build is already stored in your browser cache, it can launch directly.
2. Otherwise, click *Find JAR on the J2ME index* to look up that build by SHA-256, then use *Choose JAR file...* to import your downloaded file.

Controls include fullscreen, restart, automatic closest-fit emulated resolution, and a persistent setting for phone-style versus standard numpad layout.

## Start a local preview

Requirements: Python 3.10+ and a current browser supporting Service Workers, Cache Storage, and Web Crypto.

```sh
python3 server.py
```

Open <http://127.0.0.1:8000/>. Do not open `index.html` via `file://`.

To use a local collection: of JAR files:

```sh
python3 server.py --jar-dir '/PATH/TO/YOUR/JAR collection'
```

## Repository layout

- `index.html`, `assets/home.*`: game selection gallery
- `catalogue.html`, `assets/app.js`, `assets/site.css`: build catalogue and player controls
- `assets/jar-library.js`, `sw-jar.js`: SHA-256 verification, browser caching, and byte-range handling
- `data/catalogue.json`: game/build metadata and experimental gameplay groups
- `server.py`: optional local preview and verified local-JAR serving
- `vendor/freej2me-web/web/`: reduced emulator runtime (not the complete upstream source checkout)
- `tools/build_pages.py`, `.github/workflows/pages.yml`: static GitHub Pages build and deployment
- `tools/generate_fm_soundfont.py`: source generator for the replacement MIDI sound bank
- `tools/import_pop_workbook.py`: optional catalogue regeneration from the [research spreadsheet](https://docs.google.com/spreadsheets/d/1hBohTK19FVDa8wyGCd-a4xfeli0SKkFb)
- `tests/`: automated regression checks
- `docs/EMULATOR_SOURCE.md`: emulator source, dependency versions, build provenance, and MIDI details

The original JAR-inspection and gameplay-fingerprinting research utilities are intentionally not part of this slim website repository.

## Development and deployment

Run the automated checks with Python and Node.js:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node tests/test_jar_library.cjs
node tests/test_pages_sw.cjs
```

Generate a static site locally:

```sh
python3 tools/build_pages.py
```

This creates `_site/` for GitHub Pages. The build applies PoP Mobile's screen-resolution and numpad adapters to a generated emulator launcher without changing the vendored upstream JavaScript. GitHub Actions deploys changes affecting the website or build process; documentation-only and test-only pushes do not trigger redeployment. Manual deployment remains available through Actions.

## Emulator source and licensing

The bundled `libmidi.wasm` uses *PoP Mobile Original FM GM*, a procedurally generated General MIDI SoundFont, rather than the upstream sample bank. The generator is [`tools/generate_fm_soundfont.py`](tools/generate_fm_soundfont.py).

- [Emulator source, build provenance, and MIDI details](docs/EMULATOR_SOURCE.md)
- [Complete emulator corresponding-source archive (v0.1.0)](https://github.com/PoPRuns/pop-mobile-browser/releases/download/v0.1.0/pop-mobile-emulator-corresponding-source-v1.tar.gz)
- [Third-party notices and credits](THIRD_PARTY_NOTICES.md)
- [GPL-3.0-or-later license for original PoP Mobile code](LICENSE)

The original FreeJ2ME runtime, FluidSynth, FFmpeg, x264, and other dependencies retain their own licenses and notices. PoP Mobile uses [CheerpJ](https://cheerpj.com/) from its official CDN and displays *Built with CheerpJ* attribution.

The Prince of Persia games and associated intellectual property belong to their respective rights holders. This is an independent archival and research project, without affiliation or endorsement.

## Usage of AI

Parts of this project were developed with substantial ChatGPT assistance and have not all been reviewed line by line. While the site's content and functionality have been tested, correct operation is not guaranteed for every file, browser, or configuration.
