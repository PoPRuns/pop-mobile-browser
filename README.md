# PoP Mobile Browser

[This website](https://popruns.github.io/pop-mobile-browser/) is an independent archival catalogue of Prince of Persia Java ME builds, featuring detailed metadata and the option to run JARs in a browser using freej2me-web and CheerpJ.

**No Prince of Persia game JAR files are included in this repository or hosted by the website.** Players supply their own matching JARs.

## Play a game

1. Open the [website](https://popruns.github.io/pop-mobile-browser/), select a game and a JAR build, and click *Play / Load*. If the build is already stored in your browser cache, it can launch directly.
2. Otherwise, click *Find JAR on the J2ME index* to look up that build on [the J2ME search index](https://toca-1.github.io/new-j2me-software-archive-search/), then use *Choose JAR file...* to import your downloaded file.

Controls include fullscreen, restart, automatic closest-fit emulated resolution, per-JAR browser-local screen size overrides (choose a size in the emulator settings and select Restart), and a persistent setting for phone-style versus standard numpad layout.

The emulator automatically selects a supported phone profile from the catalogue's device information. To override it, open the emulator settings (Esc), change **Phone type**, and restart using the emulator's own prompt. The override is saved per JAR in browser storage.

## Start a local preview

Requirements: Python 3.10+ and a current browser supporting Service Workers, Cache Storage, and Web Crypto.

```sh
python3 server.py
```

Open <http://127.0.0.1:8000/>. Do not open `index.html` via `file://`.

To use a local collection of JAR files:

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

## Update the site's data

If the [research spreadsheet](https://docs.google.com/spreadsheets/d/1hBohTK19FVDa8wyGCd-a4xfeli0SKkFb) has been updated, the site's underlying data can be updated as follows -- assuming that Openpyxl is installed (`sudo apt install python3-openpyxl`). Assuming the updated spreadsheet sits in Downloads, run the following command in the terminal from the location of your local repository:

```sh
python3 tools/import_pop_workbook.py \
  "$HOME/Downloads/PoP Java Games (2026 database).xlsm" \
  data/catalogue.json
```

## Emulator source and licensing

The site uses FreeJ2ME-Web and [CheerpJ](https://cheerpj.com/). Source code, build instructions, licenses and credits are available here:

- [Emulator source and build documentation](docs/EMULATOR_SOURCE.md)
- [Third-party notices and credits](THIRD_PARTY_NOTICES.md)
- [GPL-3.0 license for original PoP Mobile code](LICENSE)

Built with CheerpJ.

The Prince of Persia games and associated intellectual property belong to their respective rights holders. This is an independent archival and research project, without affiliation or endorsement.

## Usage of AI

Parts of this project were developed with substantial ChatGPT assistance and have not all been reviewed line by line. While the site's content and functionality have been tested, correct operation is not guaranteed for every file, browser, or configuration.
