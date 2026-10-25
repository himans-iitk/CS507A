from gapstudy.units import clean, features, split


def kinds(units):
    return [(u.kind, u.level, u.heading) for u in units]


def test_title_h1_then_h2_h3_sections_with_paths():
    doc = "# CLAUDE.md\n\nIntro line.\n\n## Build\nRun make.\n\n### Tests\nRun make test.\n\n## Style\nUse black.\n"
    units = split(doc)
    assert kinds(units) == [("preamble", None, ""), ("section", 2, "Build"),
                            ("section", 3, "Tests"), ("section", 2, "Style")]
    assert units[0].text == "Intro line."
    assert units[2].heading_path == "Build > Tests"
    assert units[2].text == "Run make test."


def test_h4_stays_inside_its_section():
    units = split("# T\n## A\ntext\n#### detail\nmore\n## B\nx\n")
    assert units[0].heading == "A" and "#### detail\nmore" in units[0].text


def test_heading_with_only_subsections_is_not_a_unit():
    units = split("# T\n## Commands\n### Build\nmake\n### Test\nmake test\n")
    assert [u.heading for u in units] == ["Build", "Test"]
    assert units[0].heading_path == "Commands > Build"


def test_multiple_h1_are_sections_and_h3_still_splits():
    units = split("# Overview\nabout\n## Detail\nd\n### Sub\ns\n# Rules\nr\n")
    assert [(u.level, u.heading) for u in units] == [(1, "Overview"), (2, "Detail"), (3, "Sub"), (1, "Rules")]
    assert units[2].heading_path == "Overview > Detail > Sub"


def test_docs_starting_at_h3_use_top_two_levels():
    units = split("### A\na\n#### A1\nb\n##### deep\nc\n### B\nd\n")
    assert [(u.level, u.heading) for u in units] == [(3, "A"), (4, "A1"), (3, "B")]
    assert "##### deep" in units[1].text


def test_hash_lines_inside_code_fences_are_not_headings():
    units = split("# T\n## Setup\n```bash\n# install deps\npip install .\n```\n## Next\nx\n")
    assert [u.heading for u in units] == ["Setup", "Next"]
    assert "# install deps" in units[0].text


def test_setext_headings_are_recognised():
    units = split("Title\n=====\n\nBuild\n-----\nmake\n\nTest\n----\nmake test\n")
    assert [u.heading for u in units] == ["Build", "Test"]


def test_no_headings_falls_back_to_blocks_and_merges_lead_in():
    units = split("- Main branch is master\n- Run cargo fmt\n\nBefore committing run:\n\n```\nmake verify\n```\n")
    assert [u.kind for u in units] == ["block", "block"]
    assert units[1].text.startswith("Before committing run:") and "make verify" in units[1].text


def test_title_only_doc_uses_blocks_without_title():
    units = split("# My agent rules\n\nFirst paragraph.\n\nSecond paragraph.\n")
    assert [u.text for u in units] == ["First paragraph.", "Second paragraph."]


def test_front_matter_and_comments_removed():
    text = clean('---\napplyTo: "**/*.ts"\n---\n# T\n<!-- BEGIN RULES -->\n## A\nx\n')
    assert "applyTo" not in text and "BEGIN" not in text
    assert [u.heading for u in split(text)] == ["A"]


def test_comments_inside_code_fences_are_kept():
    text = clean("<!-- hide -->\n```markdown\n<!-- translated-from: en -->\n```\n")
    assert "hide" not in text and "translated-from" in text


def test_bold_pseudo_heading_merges_with_next_block():
    units = split("**Guardrails**\n\n- never push to main\n- keep diffs small\n\nOther rule.\n")
    assert [u.text.split("\n")[0] for u in units] == ["**Guardrails**", "Other rule."]


def test_features():
    f = features("Commands", "```bash\nnpm run build && npm test\n```\n")
    assert f["code_only"] and f["has_code"] and not f["long"] and not f["toc"]
    assert features("Lists", "- a\n- b\n1. c\n")["list_items"] == 3


def test_table_of_contents_detected():
    anchors = "1. [Overview](#overview)\n2. [Build](#build)\n3. [Testing](#testing)\n"
    assert features("Guide", anchors)["toc"]
    assert features("Table of Contents", "- see below")["toc"]
    assert not features("Docs", "- [API](docs/api.md)\n- [CLI](docs/cli.md)\n- [FAQ](faq.md)\n")["toc"]
