# Data Directory

Hugo data files live here. This directory currently contains migrated legacy data and is the day-to-day maintenance source for non-page data.

Files:

- `featured-projects.json`: homepage selected research projects.
- `projects.json`: patent list; each record uses `patent_name` and `inventors` for display.
- `publications.json`: legacy publication migration input; keep unchanged for migration traceability.
- `publication-records.json`: generated publication catalog consumed by the site; do not edit directly.
- `member-aliases.json`: exact author-name-to-member-page mappings used by the publication importer.
- `slides.json`: homepage carousel.
- `legacy-map.json`: legacy ID/URL mapping for migration traceability.

The editable publication source is `frontend/publication-source/publications.csv`, outside this directory so Hugo does not try to parse the CSV as a data file. Run `python3 tools/import_publications.py` after updating it.
