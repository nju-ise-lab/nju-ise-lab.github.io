# ISE Quick

ISE Quick is the lightweight rebuild of the Nanjing University ISE lab website.

## Structure

```text
ise-quick/
  frontend/   Hugo static website
  backend/    Lightweight view counter API
  migration/  Legacy data conversion pipeline
  docs/       Project-local decisions and handoff notes
```

## Current Decisions

- Frontend: Hugo static site with a custom lightweight theme.
- Backend: small view counter API, planned as Go + SQLite.
- Content updates: edit Markdown/JSON files and rebuild the static site.
- Homepage: carousel, latest news, academic activities, and featured research projects.
- Platform product URL: `/platform/`.
- Search and CMS are intentionally out of scope for the first release.
- Legacy database access is paused; current migration input comes from exported legacy public API data.

## Development Rule

New work should live under `ise-quick/`. The old `ise/` and `ise_lab_front/` projects have been removed from this workspace after migration.

## Handoff Notes

- See `docs/project-overview-architecture.md` for project introduction and architecture.
- See `docs/cloud-deployment-guide.md` for cloud server deployment.
- See `docs/decisions.md` for confirmed architecture decisions.
- See `docs/checklist.md` for manual verification before launch.
- See `docs/implementation-status.md` for the latest implementation and verification status.
- See `docs/content-maintenance-guide.md` for the day-to-day content update guide.
