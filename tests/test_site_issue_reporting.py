"""Site issues use an auto-labeled GitHub template instead of title matching."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SiteIssueReportingTests(unittest.TestCase):
    def test_site_reporting_link_uses_labeled_template(self):
        template = ROOT / '.github/ISSUE_TEMPLATE/site-bug.md'
        text = template.read_text(encoding='utf-8')
        frontmatter = text.split('---', 2)[1]
        self.assertIn("labels: 'site-bug'", frontmatter)
        self.assertIn("title: '[Site] Bug report'", frontmatter)
        for page in ('index.html', 'catalogue.html'):
            html = (ROOT / page).read_text(encoding='utf-8')
            self.assertIn('issues/new?template=site-bug.md', html)
            self.assertNotIn('issues/new?title=%5BSite%5D', html)

    def test_site_footer_links_use_responsive_single_row(self):
        for page in ('home.css', 'site.css'):
            css = (ROOT / 'assets' / page).read_text(encoding='utf-8')
            self.assertIn('.footer-credits{display:flex;flex-direction:row;flex-wrap:wrap;', css)
            self.assertIn('.footer-credits>a{white-space:nowrap}', css)
        self.assertIn('.site-footer .footer-credits{display:flex;flex-direction:row;', (ROOT / 'assets/site.css').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
