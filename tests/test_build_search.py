"""Regression checks for build-specific catalogue search, especially checksums."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildSearchTests(unittest.TestCase):
    def test_checksum_search_is_build_specific(self):
        # Execute the actual matchesBuild() implementation with a simulated
        # filter bar, not an alternative copy of the search algorithm.
        js = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/app.js', 'utf8');
const start = source.indexOf('  function matchesBuild(b) {');
const end = source.indexOf('\n  const FAMILY_LABELS', start);
assert(start !== -1 && end > start, 'Catalogue search function not found');
const functionSource = source.slice(start, end);
const target = {
  id: '9cd9355f', group: 'HA-G01-o', name: 'Prince of Persia Harem Adventures',
  vendor: 'Gameloft', resolution: '176x208', language: 'English',
  crc32: '4F113839', sha1: '31570e94caacfe07ab7ff043acf9ea5d28e32671',
  sha256: '9cd9355fc8b47e0e73c6b3038ffc30f1bd24c1a27e9894e703e30bc4f7d53eac',
  notesGameplay2: 'Same gameplay as CRC32: 4F113839'
};
const siblings = Array.from({length: 5}, (_, i) => ({
  id: `sibling-${i}`, group: 'HA-G01-o', name: 'Prince of Persia Harem Adventures',
  vendor: 'Gameloft', resolution: '176x208', language: i < 3 ? 'English' : 'Russian',
  crc32: `A8ED15E${i}`, sha1: 'a'.repeat(40), sha256: `${i}`.repeat(64),
  notesGameplay2: 'Same gameplay as CRC32: 4F113839'
}));
const builds = [target, ...siblings];
const group = {id: 'HA-G01-o', notes: ['Same gameplay as CRC32: 4F113839', 'shared archived note']};
const fields = {'filter-search': {value: ''}, 'filter-resolution': {value: ''},
  'filter-language': {value: ''}, 'filter-unplayable': {checked: false}};
const state = {data: {builds}, groupMap: new Map([[group.id, group]])};
const matchesBuild = vm.runInNewContext(functionSource + '\n matchesBuild;',
  {state, $: id => fields[id]});
const find = q => {fields['filter-search'].value = q; return builds.filter(matchesBuild);};
assert.deepEqual(find('4F113839').map(b => b.id), [target.id]);
assert.deepEqual(find('4f113839').map(b => b.id), [target.id]);
assert.deepEqual(find(target.sha1.toUpperCase()).map(b => b.id), [target.id]);
assert.deepEqual(find(target.sha256).map(b => b.id), [target.id]);
assert.deepEqual(find('shared archived note').map(b => b.id), []);
assert.equal(find('HA-G01-o').length, 6, 'Group-ID search must still work');
assert.equal(find('Russian').length, 2, 'Ordinary text filters must still work');
assert.deepEqual(find('Gameloft 4F113839').map(b => b.id), builds.map(b => b.id),
  'General searches containing multiple terms remain supported');
'''
        subprocess.run(['node', '-e', js], cwd=ROOT, check=True)


if __name__ == '__main__':
    unittest.main()
