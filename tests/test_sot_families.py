"""Regression checks for the Sands of Time gameplay-family overview."""
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook
from tools import import_pop_workbook as importer

ROOT = Path(__file__).resolve().parents[1]
HEADERS = [
    'Gameplay Group (experimental)', 'Applet Name', 'Title Screen Name',
    'Applet Version', 'Applet Author', 'CLDC', 'MIDP', 'Screen Dimension',
    'Language', 'About section Name', 'About section Version',
    'About section Author', 'Source filenames',
    'File name (according to old zip)', 'Archive paths',
    'Internet Archive URLs', 'Device(s)', 'Notes (general)',
    'Notes (gameplay)', 'Notes #2 (gameplay)', 'Size (Bytes)',
    'CRC32', 'SHA-1', 'SHA-256',
]


class SandsOfTimeFamilyTests(unittest.TestCase):
    def test_sot_groups_become_two_families_without_changing_build_ids(self):
        workbook = Workbook()
        workbook.remove(workbook.active)
        for sheet, *_ in importer.COLLECTIONS:
            workbook.create_sheet(sheet).append(HEADERS)
        sot = workbook['SoT']
        for i, group in enumerate(['SoT-G01-a', 'SoT-G01-b', 'SoT-G02-a', 'SoT-G02-h'], start=1):
            row = [''] * len(HEADERS)
            row[0], row[1], row[3], row[4] = group, 'Prince of Persia SoT', '1.0', 'Gameloft SA'
            row[7], row[8], row[20], row[23] = '128x160', 'English', 89208, f'{i:064x}'
            if i == 4:
                row[18] = 'Unplayable'
            sot.append(row)
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'data.xlsm'
            target = Path(temp) / 'catalogue.json'
            workbook.save(source)
            data = importer.convert(source, target)
            families = [f for f in data['families'] if f['game'] == 'sands-of-time']
            builds = [b for b in data['builds'] if b['game'] == 'sands-of-time']
            self.assertEqual([f['id'] for f in families], ['SoT-G01', 'SoT-G02'])
            self.assertEqual([f['count'] for f in families], [2, 2])
            self.assertEqual([b['group'] for b in builds],
                             ['SoT-G01-a', 'SoT-G01-b', 'SoT-G02-a', 'SoT-G02-h'])
            self.assertEqual([b['variant'] for b in builds], ['a', 'b', 'a', 'h'])
            self.assertEqual([b['family'] for b in builds],
                             ['SoT-G01', 'SoT-G01', 'SoT-G02', 'SoT-G02'])
            self.assertTrue(builds[-1]['unplayable'])
            self.assertEqual([f['image'] for f in families],
                             ['assets/previews/sot-g01.png', 'assets/previews/sot-g02.png'])
            self.assertTrue(target.is_file())

    def test_ui_displays_sot_previews_and_preserves_harem(self):
        js = (ROOT / 'assets/app.js').read_text(encoding='utf-8')
        self.assertIn("'SoT-G01': 'Standard Edition'", js)
        self.assertIn("'SoT-G02': 'Compact Edition'", js)
        self.assertIn("'SoT-G01': 'assets/previews/sot-g01.png'", js)
        self.assertIn("'SoT-G02': 'assets/previews/sot-g02.png'", js)
        self.assertIn("'HA-G01': 'assets/previews/harem-g01.png'", js)
        for family, label in (
            ('HA-G01', 'Standard Edition'),
            ('HA-G02', 'Compact Edition'),
            ('HA-G03', 'Alternate Edition'),
            ('SoT-G01', 'Standard Edition'),
            ('SoT-G02', 'Compact Edition'),
        ):
            self.assertIn(f"'{family}': '{label}'", js)
        card_renderer = js.split('  function renderFamilyCard(family, builds) {', 1)[1].split('  function render() {', 1)[0]
        self.assertNotIn('family-card-code', card_renderer)
        self.assertIn("data.game.id === 'sands-of-time' ? 'Sands of Time' : data.game.sheet.toUpperCase()", js)
        self.assertIn('const hasFamilies = families.length > 0;', js)
        self.assertIn('family-overview-mode', js)
        for name in ('sot-g01.png', 'sot-g02.png'):
            self.assertGreater((ROOT / 'assets/previews' / name).stat().st_size, 1000)


if __name__ == '__main__':
    unittest.main()
