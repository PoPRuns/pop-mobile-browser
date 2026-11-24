"""Workbook-driven Harem family, playback-hint and static asset regressions."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server
from tools import import_pop_workbook as importer

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None


class FamilyTests(unittest.TestCase):
    def test_note_classifier(self):
        self.assertEqual(importer.classify_notes(['', 'Limit FPS to 15', '']), (False, 15))
        self.assertEqual(importer.classify_notes(['UNPLAYABLE: broken text', 'limit fps to 30', '']), (True, 30))
        self.assertEqual(importer.classify_notes(['', '', 'limit FPS to 60']), (False, 60))
        self.assertEqual(importer.classify_notes(['Playable', 'No speed limitation']), (False, None))
        with self.assertRaisesRegex(ValueError, 'conflicting FPS'):
            importer.classify_notes(['Limit FPS to 15', 'Limit FPS to 30'])

    @unittest.skipIf(Workbook is None, 'openpyxl not installed')
    def test_workbook_to_families_with_individual_flags(self):
        wb = Workbook()
        wb.remove(wb.active)
        for sheet, *_ in importer.COLLECTIONS:
            ws = wb.create_sheet(sheet)
            headers = [
                'Gameplay Group (experimental)', 'Applet Name', 'Title Screen Name',
                'Applet Version', 'Applet Author', 'CLDC', 'MIDP', 'Screen Dimension',
                'Language', 'About section Name', 'About section Version',
                'About section Author', 'Source filenames',
                'File name (according to old zip)', 'Archive paths',
                'Internet Archive URLs', 'Device(s)', 'Notes (general)',
                'Notes (gameplay)', 'Notes #2 (gameplay)', 'Size (Bytes)',
                'CRC32', 'SHA-1', 'SHA-256'
            ]
            ws.append(headers)
        ws = wb['Harem Adventures']
        for i, (group, notes) in enumerate([
            ('HA-G01-a', ['', '', '']),
            ('HA-G01-b', ['', 'Limit FPS to 15', '']),
            ('HA-G02', ['', 'Unplayable, text broken', '']),
            ('HA-G03', ['Limit FPS to 30', '', '']),
        ], 1):
            record = [''] * 24
            record[0] = group
            record[1] = 'Prince of Persia'
            record[3:5] = ['1.0', 'Gameloft']
            record[7:9] = ['128x128', 'English']
            record[16] = ['Siemens S55', 'Nokia Series 60', 'LG U880', 'Sony Ericsson T610'][i-1]
            record[17:20] = notes
            record[20] = 89208.0
            record[23] = f'{i:064x}'
            ws.append(record)
        with tempfile.TemporaryDirectory() as d:
            workbook = Path(d) / 'research.xlsm'
            output = Path(d) / 'catalogue.json'
            wb.save(workbook)
            result = importer.convert(workbook, output)
            self.assertEqual(len(result['families']), 3)
            self.assertEqual([g['count'] for g in result['families']], [2, 1, 1])
            self.assertEqual([b['family'] for b in result['builds']], ['HA-G01','HA-G01','HA-G02','HA-G03'])
            self.assertEqual([b['variant'] for b in result['builds']], ['a','b','',''])
            self.assertEqual([b['phoneType'] for b in result['builds']], ['Siemens','Nokia',None,'SonyEricsson'])
            self.assertEqual(result['builds'][0]['device'], 'Siemens S55')
            self.assertEqual([b['fpsLimit'] for b in result['builds']], [None,15,None,30])
            self.assertEqual([b['unplayable'] for b in result['builds']], [False,False,True,False])
            self.assertEqual(json.loads(output.read_text())['families'][0]['count'], 2)

    def test_ui_and_assets(self):
        page = (ROOT / 'catalogue.html').read_text()
        js = (ROOT / 'assets/app.js').read_text()
        for marker in ('id="families"', 'id="filter-unplayable"', 'id="family-back"'):
            self.assertIn(marker, page)
        self.assertIn('families: (entire.families || [])', js)
        self.assertIn('params.set(\'fpsLimit\'', js)
        self.assertIn('b.unplayable &&', js)
        self.assertIn('renderFamilyCard', js)
        for img in ('harem-g01.png', 'harem-g02.png', 'harem-g03.png'):
            self.assertGreater((ROOT / 'assets' / 'previews' / img).stat().st_size, 1000)

    def test_injected_display_fps_pacing_without_vendor_modification(self):
        upstream = (ROOT / 'vendor/freej2me-web/web/src/main.js').read_text()
        adapted = server.inject_fps_hook(server.inject_numpad_hook(server.inject_resolution_hook(upstream)))
        self.assertNotIn('popFpsNatives', upstream)
        self.assertIn('...popFpsNatives', adapted)
        self.assertIn('ctx === screenCtx', adapted)
        self.assertIn('[15, 30, 60].includes(', adapted)
        self.assertIn('await new Promise(resolve => setTimeout', adapted)


if __name__ == '__main__':
    unittest.main()
