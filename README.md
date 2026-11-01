# brasa-templates

The official **templates**, **download plans** and **validation rules** for
[brasa](https://github.com/wilsonfreitas/brasa) — Brazilian market and economic
data (B3, BCB, ANBIMA, CVM, …).

brasa is the engine; this repo is a **template folder** it reads:

```
brasa.toml      # which brasa versions these templates work with
templates/      # dataset definitions (download, parse, ETL), one YAML per template
plans/          # download recipes, called by name: brasa download --plan <name>
validations/    # extra rule files (most rules live inside the templates)
tests/ data/    # tests and fixtures for the templates (not read by brasa)
```

## Use it

Point brasa at a clone of this repo:

```bash
git clone https://github.com/wilsonfreitas/brasa-templates ~/brasa-templates
export BRASA_TEMPLATE_PATH=~/brasa-templates        # or template_path in ~/.config/brasa/config.toml
brasa list-templates
```

(From brasa-core 0.5, `brasa init` clones it for you and `brasa update-templates`
pulls new versions.)

Templates are code — they can run Python — so only use template folders you trust.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). License: MIT.
