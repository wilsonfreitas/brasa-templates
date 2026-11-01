# CLAUDE.md

This repo is **brasa-templates**: the official template folder for brasa
(templates, download plans, validation rules). The engine lives in the sibling
repo `../brasa` (`~/dev/python/brasa`).

## Always use uv

```bash
uv sync                          # installs brasa from ../brasa (editable)
uv run pytest --no-integration   # offline tests
uv run pytest                    # + integration tests (internet)
uv run ruff check . && uv run ruff format --check .
uv run pre-commit run --all-files
```

## Definition of Done

All three must pass: tests, ruff, pre-commit.

## Layout

- `templates/**.yaml` — templates (file name = `id:`); format reference: `../brasa/docs/TEMPLATES.md`
- `plans/*.yaml` — download plans (`name:` = file name)
- `validations/*.yaml` — extra rule files (`layer.dataset` → rules); most rules are inline `validations:` blocks
- `brasa.toml` — `requires-brasa` (upper bound `<0.(next minor)`)
- `tests/`, `data/` — template tests and fixtures; `tests/test_repo_checks.py` = repo-wide checks

## Workflow

- Linear issues for this repo carry the `templates` label (project brasa).
- One issue = one repo. A change that also needs the engine is a separate
  brasa issue that blocks the templates one; `main` never requires an
  unreleased brasa.
