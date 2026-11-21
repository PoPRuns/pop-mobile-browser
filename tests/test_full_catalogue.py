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
 def test_compact_catalogue_matches_home_navigation(self):
  home=(ROOT/'index.html').read_text()
  catalogue=(ROOT/'catalogue.html').read_text()
  app=(ROOT/'assets/app.js').read_text()
  for text in ('Prince of Persia · Java Mobile Game Archive', 'Source code', 'NOT AFFILIATED WITH UBISOFT OR GAMELOFT'):
   self.assertIn(text,home)
   self.assertIn(text,catalogue)
  self.assertIn('id="game-title"',catalogue)
  self.assertIn('id="result-count"',catalogue)
  self.assertNotIn('id="sort-results"',catalogue)
  self.assertNotIn("$('sort-results')",app)
  self.assertNotIn('jar-file-name',app)
  self.assertIn('${escape(b.sha256)}</code>',app)
  self.assertNotIn('b.sha256.slice(',app)
  self.assertIn('id="filter-search"',catalogue)
  for removed_id in ('view-groups','view-builds','filter-group','filter-favorites','local-status'):
   self.assertNotIn('id="'+removed_id+'"',catalogue)
   self.assertNotIn("$('"+removed_id+"')",app)
  for removed_copy in ('Showing records from the supplied research spreadsheet.', 'BROWSER PLAY · CHOOSE YOUR OWN VERIFIED JAR', 'Import or use cached JAR', 'Play / Load', 'Play / load JAR'):
   self.assertNotIn(removed_copy,catalogue+app)
  self.assertIn('>Play</button>',app)
  self.assertLess(catalogue.index('id="filter-search"'),catalogue.index('id="filter-resolution"'))
  self.assertLess(catalogue.index('id="filter-resolution"'),catalogue.index('id="filter-language"'))
  self.assertIn("data.game.ungrouped ? 'Others' : data.game.title",app)
  for removed in ('game-masthead', 'stats-band', 'collection-highlight', 'side-index-link', 'about-section', 'GO DEEPER', 'id="how-play"'):
   self.assertNotIn(removed,catalogue)
  for missing_id in ('game-year','game-description','featured-title','featured-description','collection-subheading','stat-game-label','game-switcher','stat-builds','stat-groups','stat-screens','stat-langs','collection-count','how-play'):
   self.assertNotIn("$('"+missing_id+"')",app)
 def test_details_are_inline_and_build_specific(self):
  html=(ROOT/'catalogue.html').read_text()
  app=(ROOT/'assets/app.js').read_text()
  self.assertNotIn('details-modal',html+app)
  self.assertNotIn('renderGroupDetails',app)
  self.assertIn('class="inline-build-details"',app)
  self.assertIn('aria-expanded="${expanded}"',app)
  self.assertIn('aria-controls="${escape(detailsId)}"',app)
  self.assertIn("setBuildDetails(build, !state.expandedBuilds.has(build))",app)
  self.assertIn("state.buildMap.has(sha) ? sha",app)
  self.assertIn("else if (action === 'copy') copyText(button.dataset.copy)",app)
  details=app.split('  function renderBuildDetails(b) {',1)[1].split('  async function copyText',1)[0]
  for label in ('Display','Language','Device','CLDC / MIDP','Applet version','In-game version','In-game author','File size','CRC32','SHA-1','SHA-256'):
   self.assertIn(label,details)
  for label in ('Archive references','EXTERNAL ARCHIVE SOURCES','RESEARCH NOTES','SOURCE FILENAME','CATALOGUED ARCHIVE PATHS','SELECT A RECORDED JAR BUILD'):
   self.assertNotIn(label,details)
 def test_navigation_and_player_contract(self):
  home=(ROOT/'index.html').read_text()
  catalogue=(ROOT/'catalogue.html').read_text()
  app=(ROOT/'assets/app.js').read_text()
  self.assertIn('assets/home.js',home)
  self.assertIn('href="index.html"',catalogue)
  self.assertIn('id="player-stage"',catalogue)
  # Play: compact controls appear before verified JAR actions and the screen.
  self.assertNotIn('EXPERIMENTAL / BROWSER EMULATION',catalogue)
  self.assertNotIn('id="play-notice"',catalogue)
  self.assertNotIn('jar-help',catalogue)
  self.assertNotIn('id="player-fullscreen-label"',catalogue)
  self.assertNotIn("$('play-notice')",app)
  self.assertNotIn("$('player-fullscreen-label')",app)
  self.assertLess(catalogue.index('id="player-controls"'),catalogue.index('id="jar-source-panel"'))
  self.assertLess(catalogue.index('id="jar-source-panel"'),catalogue.index('id="player-stage"'))
  self.assertIn('aria-label="Enter fullscreen"',catalogue)
  self.assertIn("button.title = active ? 'Exit fullscreen' : 'Enter fullscreen'",app)

  self.assertIn('id="jar-index-link"',catalogue)
  self.assertNotIn('id="jar-recover"',catalogue)
  self.assertIn("state.currentGame = data.game",app)
  self.assertIn("const requested = new URLSearchParams(location.search).get('game')",app)
  self.assertNotIn('The JAR service worker is active, but the emulator iframe is not controlled.',app)
if __name__=='__main__':unittest.main()
