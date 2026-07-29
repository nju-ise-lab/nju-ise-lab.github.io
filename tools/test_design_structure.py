from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "frontend" / "themes" / "ise"


class DesignStructureTest(unittest.TestCase):
    def test_redundant_page_header_is_removed_from_inner_pages(self):
        partial = THEME / "layouts" / "partials" / "page-header.html"
        self.assertTrue(partial.exists())

        for relative in (
            "layouts/news/list.html",
            "layouts/activities/list.html",
            "layouts/members/list.html",
            "layouts/platform/list.html",
        ):
            content = (THEME / relative).read_text(encoding="utf-8")
            self.assertNotIn('partial "page-header.html"', content)

    def test_refreshed_design_classes_are_present(self):
        css = (THEME / "assets" / "css" / "main.css").read_text(encoding="utf-8")

        for selector in (
            ".page-header",
            ".home-feature-grid",
            ".publication-year-group",
            ".member-section-heading",
            ".project-card-list",
            ".related-card-list",
        ):
            self.assertIn(selector, css)

    def test_homepage_delay_effects_are_removed(self):
        home = (THEME / "layouts" / "index.html").read_text(encoding="utf-8")
        base = (THEME / "layouts" / "_default" / "baseof.html").read_text(encoding="utf-8")
        script = THEME / "assets" / "js" / "home-effects.js"

        self.assertNotIn("home-stats", home)
        self.assertNotIn("home-stat-card", home)
        self.assertNotIn("data-count", home)
        self.assertNotIn("data-reveal", home)
        self.assertFalse(script.exists())
        self.assertNotIn('resources.Get "js/home-effects.js"', base)

    def test_homepage_stats_cards_are_removed(self):
        css = (THEME / "assets" / "css" / "main.css").read_text(encoding="utf-8")

        self.assertNotIn(".home-stats", css)
        self.assertNotIn(".home-stat-card", css)


if __name__ == "__main__":
    unittest.main()
