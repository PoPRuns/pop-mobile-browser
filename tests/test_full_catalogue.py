"""Data integrity and navigation checks for the nine-collection JAR browser."""
import json, re, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/catalogue.json').read_text(encoding='utf8'))
class FullCatalogueTests(unittest.TestCase):
 def test_game_and_build_counts(self):
  self.assertEqual(len(DATA['games']),9)
  self.assertEqual(len(DATA['builds']),950)
  self.assertEqual(len({b['sha256'] for b in DATA['builds']}),950)
  self.assertEqual(sum(g['groups'] for g in DATA['games']),489)
  self.assertEqual(sum(g['count'] for g in DATA['games']),950)
  self.assertEqual(len(DATA['relatedFiles']),19)
 def test_integrity_metadata_and_game_references(self):
  ids={g['id'] for g in DATA['games']}
  groups={g['id']:g for g in DATA['groups']}
  for build in DATA['builds']:
   self.assertIn(build['game'],ids)
   self.assertRegex(build['sha256'],r'^[a-f0-9]{64}$')
   self.assertRegex(build['sha1'],r'^[a-f0-9]{40}$')
   self.assertTrue(4<=build['size']<=8*1024*1024)
   self.assertIn(build['group'],groups)
   self.assertIn(build['sha256'],groups[build['group']]['buildIds'])
   self.assertTrue(all(url.startswith('https://archive.org/download/') for url in build['urls']))
 def test_needs_review_is_not_a_gameplay_group(self):
  unclassified=[b for b in DATA['builds'] if b['game']=='needs-review']
  self.assertEqual(len(unclassified),22)
  self.assertTrue(all(b['unclassified'] for b in unclassified))
  self.assertTrue(all(g['unclassified'] for g in DATA['groups'] if g['game']=='needs-review'))
  self.assertEqual(next(g for g in DATA['games'] if g['id']=='needs-review')['groups'],0)
 def test_navigation_and_player_contract(self):
  home=(ROOT/'index.html').read_text()
  catalogue=(ROOT/'catalogue.html').read_text()
  app=(ROOT/'assets/app.js').read_text()
  self.assertIn('assets/home.js',home)
  self.assertIn('href="index.html"',catalogue)
  self.assertIn('id="player-stage"',catalogue)
  self.assertIn('id="jar-index-link"',catalogue)
  self.assertNotIn('id="jar-recover"',catalogue)
  self.assertIn("data.game.id",app)
  self.assertIn("const requested = new URLSearchParams(location.search).get('game')",app)
  self.assertNotIn('The JAR service worker is active, but the emulator iframe is not controlled.',app)
if __name__=='__main__':unittest.main()
