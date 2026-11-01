# Contributing to brasa-templates

Thanks for helping! A new or fixed template reaches every brasa user with a
`brasa update-templates` — no brasa release needed.

## Add or change a template

- One YAML file per template under `templates/<source>/…`. The file name must
  equal the template `id:`.
- Ids are source-prefixed kebab-case: `b3-…`, `bcb-…`, `anbima-…`, `cvm-…`.
- One pull request = the template + its tests + small fixture files + its
  inline `validations:` rules (rules that are true for every user of the
  dataset; see brasa `docs/VALIDATIONS.md`).
- The template format reference is brasa's `docs/TEMPLATES.md`.

## Run the tests (offline)

You need a brasa checkout next to this repo (`../brasa`):

```bash
uv sync
uv run pytest --no-integration
uv run ruff check . && uv run ruff format --check .
uv run pre-commit run --all-files
```

`tests/test_repo_checks.py` runs on every pull request: every template loads,
ids match file names, every rule points to a real dataset, every plan name
matches its file.

## Rules of the road

- **Templates are code.** They can run Python (`exec_code`, `apply_lambda`,
  `function:` imports), so reviews look at them like code.
- **Compatibility:** `brasa.toml` always pins `requires-brasa` with an upper
  bound at the next minor version (`<0.(next minor)`). `main` never requires an
  unreleased brasa. A change that needs a new brasa feature waits on a branch
  until that brasa version is released.
- **Shared vs personal:** this repo holds what is true or useful for everyone.
  Your own download lists and rules about the symbols you care about belong in
  your own template folder (listed before this one in `BRASA_TEMPLATE_PATH`).
