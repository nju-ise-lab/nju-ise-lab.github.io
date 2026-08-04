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
            "layouts/members/list.html",
            "layouts/projects/list.html",
            "layouts/research-results/list.html",
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

    def test_results_do_not_use_pagination(self):
        script = (THEME / "assets" / "js" / "results-filters.js").read_text(
            encoding="utf-8"
        )
        template = (THEME / "layouts" / "research-results" / "list.html").read_text(
            encoding="utf-8"
        )
        css = (THEME / "assets" / "css" / "main.css").read_text(encoding="utf-8")

        self.assertIn("URLSearchParams", script)
        self.assertIn('window.addEventListener("popstate"', script)
        self.assertNotIn('querySelectorAll(":scope', script)
        self.assertNotIn("data-paginated-panel", template)
        self.assertNotIn("data-results-pagination", template)
        self.assertNotIn("setupPagination", script)
        self.assertNotIn(".results-pagination", css)

    def test_teacher_profiles_use_collapsible_output_archives(self):
        template = (THEME / "layouts" / "members" / "single.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("member-profile__hero", template)
        self.assertIn('class="member-output-archive"', template)
        self.assertIn("$publicationPreviewCount := 8", template)

    def test_editorial_footer_structure_is_present(self):
        footer = (THEME / "layouts" / "partials" / "footer.html").read_text(
            encoding="utf-8"
        )

        self.assertIn('class="site-footer__about"', footer)
        self.assertIn("快速入口", footer)
        self.assertIn("南京大学软件学院", footer)


if __name__ == "__main__":
    unittest.main()
