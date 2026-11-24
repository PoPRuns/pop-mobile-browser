"""Warrior Within edition mapping, preview assets and future workbook imports."""
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


class WarriorWithinFamilyTests(unittest.TestCase):
    def make_workbook(self, entries):
        workbook = Workbook()
        workbook.remove(workbook.active)
        for name, *_ in importer.COLLECTIONS:
            workbook.create_sheet(name).append(HEADERS)
        for i, (group, note) in enumerate(entries, 1):
            row = [''] * len(HEADERS)
            row[0] = group
            row[1] = 'Prince of Persia: Warrior Within'
            row[3] = '1.0'
            row[4] = 'Gameloft'
            row[7:9] = ['176x208', 'English']
            row[19] = note
            row[20] = 123456
            row[23] = f'{i:064x}'
            workbook['WW'].append(row)
        return workbook

    def test_import_preserves_subgroups_and_build_level_notes(self):
        wb = self.make_workbook([
            ('WW-G01-a', ''),
            ('WW-G01-b', 'Limit FPS to 15'),
            ('WW-G02-c', 'Unplayable'),
            ('WW-G02-d', ''),
        ])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'input.xlsm'
            out = Path(temp) / 'data.json'
            wb.save(path)
            data = importer.convert(path, out)
            self.assertTrue(out.is_file())
        builds = [b for b in data['builds'] if b['game'] == 'warrior-within']
        families = [f for f in data['families'] if f['game'] == 'warrior-within']
        self.assertEqual([b['group'] for b in builds], ['WW-G01-a', 'WW-G01-b', 'WW-G02-c', 'WW-G02-d'])
        self.assertEqual([b['family'] for b in builds], ['WW-G01', 'WW-G01', 'WW-G02', 'WW-G02'])
        self.assertEqual([b['variant'] for b in builds], ['a', 'b', 'c', 'd'])
        self.assertEqual([f['id'] for f in families], ['WW-G01', 'WW-G02'])
        self.assertEqual([f['count'] for f in families], [2, 2])
        self.assertEqual([f['image'] for f in families], [
            'assets/previews/ww-g01.png', 'assets/previews/ww-g02.png',
        ])
        self.assertEqual([b['unplayable'] for b in builds], [False, False, True, False])
        self.assertEqual([b['fpsLimit'] for b in builds], [None, 15, None, None])

    def test_rejects_unrecognized_ww_family_without_writing_data(self):
        wb = self.make_workbook([('WW-G03-a', '')])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'input.xlsm'
            out = Path(temp) / 'data.json'
            wb.save(path)
            with self.assertRaisesRegex(ValueError, 'unrecognized gameplay family'):
                importer.convert(path, out)
            self.assertFalse(out.exists())

    def test_site_shows_two_previews_and_correct_names(self):
        js = (ROOT / 'assets/app.js').read_text()
        css = (ROOT / 'assets/site.css').read_text()
        for fid, label in [('WW-G01', 'Standard Edition'), ('WW-G02', 'Compact Edition')]:
            self.assertIn(f"'{fid}': '{label}'", js)
            self.assertIn(f"'{fid}': 'assets/previews/{fid.lower()}.png'", js)
            self.assertGreater((ROOT / 'assets/previews' / f'{fid.lower()}.png').stat().st_size, 1000)
        self.assertIn('families.length === 2', js)
        self.assertIn('body.two-family-overview-mode .family-grid', css)
        self.assertIn("'warrior-within': 'WARRIOR WITHIN'", js)
        self.assertIn("'HA-G03': 'Alternate Edition'", js)
        self.assertIn("'SoT-G01': 'Standard Edition'", js)


if __name__ == '__main__':
    unittest.main()
