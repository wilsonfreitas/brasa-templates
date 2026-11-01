"""Repo-wide checks for brasa-templates, run on every pull request."""

from pathlib import Path

from brasa.engine.download_plan import load_plan
from brasa.engine.template import (
    get_template_folders,
    list_plan_sources,
    list_template_sources,
    retrieve_template,
)
from brasa.engine.validations import collect_rules

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"


def _ours(entries):
    return [e for e in entries if e.source.resolve() == ROOT]


def _template_files():
    return [
        f
        for f in TEMPLATES.rglob("*.yaml")
        if "legacy" not in f.relative_to(TEMPLATES).parts
    ]


def test_templates_load_from_this_repo():
    entries = _ours(list_template_sources())
    assert len(entries) == len(_template_files())
    for entry in entries:
        # retrieve_template also fails when `id` differs from the file name
        assert retrieve_template(entry.name).id == entry.name


def test_only_templates_dir_is_read():
    for entry in _ours(list_template_sources()):
        assert TEMPLATES in entry.path.resolve().parents


def test_brasa_toml_is_valid():
    folder = next(f for f in get_template_folders() if f.root.resolve() == ROOT)
    assert folder.error is None
    assert folder.name == "brasa-templates"
    assert folder.requires


def test_rule_keys_point_to_real_datasets():
    _, _, problems = collect_rules()
    assert [p.description for p in problems] == []


def test_plan_names_match_files():
    for entry in _ours(list_plan_sources()):
        assert load_plan(entry.name).name == entry.name
