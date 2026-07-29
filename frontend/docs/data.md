# Data Directory

Hugo data files live here. This directory currently contains migrated legacy data and is the day-to-day maintenance source for non-page data.

Files:

- `featured-projects.json`: homepage selected research projects.
- `projects.json`: patent list; records use `patent_name` and `inventors`; imported application data may also include `public_number`, `application_number`, `application_date`, and `applicants`.
- `publications.json`: legacy publication migration input; keep unchanged for migration traceability.
- `publication-records.json`: generated publication catalog consumed by the site; do not edit directly.
- `member-aliases.json`: exact author-name-to-member-page mappings used by the publication importer.
- `software-copyrights.json`: software copyright records shown in the research-results tabs.
- `slides.json`: homepage carousel.
- `legacy-map.json`: legacy ID/URL mapping for migration traceability.

The editable publication source is `frontend/publication-source/publications.csv`, outside this directory so Hugo does not try to parse the CSV as a data file. Run `python3 tools/import_publications.py` after updating it.

Each software copyright can use `software_name`, `registration_number`, `year`, and an `owners` array. Empty fields are hidden.
