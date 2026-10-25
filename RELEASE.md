# Release checklist

Run these in order once coding is complete. Steps marked **(you)** publish something or need your
accounts; nothing here is automated.

## 1. Results

- [ ] `python -m gapstudy.reliability` → report κ in the paper
- [ ] `python -m gapstudy.freeze` → `coding/labels_v1.csv` + `.sha256` (no `--force`)
- [ ] `python -m gapstudy.detector.evaluate` → `analysis/phase6/`, `detector/config.json`
- [ ] (optional) LLM judge job, then re-run `evaluate`
- [ ] `python -m gapstudy.analysis.report` → `analysis/phase7/results.md`
- [ ] `python -m gapstudy.paper_numbers` → no `[TBD]` left except those you fill by hand
- [ ] Fill the `% TODO` blocks in `paper/main.tex` (RQ2 tables, discussion, conclusion)
- [ ] Check every bibliography entry marked `VERIFY` in `paper/refs.bib`; add the original
      citation of Steinmacher et al.'s 58-barrier model
- [ ] Edit the *Use of AI Tools* paragraph so it describes your own use accurately
- [ ] `cd paper && latexmk -pdf main.tex`; read the PDF end to end

## 2. Data licensing — decide before archiving

`data/processed/corpus/` holds copies of 603 README, CONTRIBUTING and agent files (plus 525
`docs/` files) from public repositories; each stays under its owner's license, and some may have
none. Options:

1. **Keep them in the release** (common in MSR datasets; the source dataset does the same), with the
   note in `LICENSE`.
2. **Ship identifiers only:** remove `corpus/` from the archive and keep `corpus_manifest.csv` (repo,
   commit, blob SHAs); users re-create it with `python -m gapstudy.fetch`, and the blob SHAs prove
   they got identical files.

The GitHub repository is already public, so option 1 is the current state.

## 3. Archive (you)

- [ ] Log in to <https://zenodo.org> with GitHub and enable the `himans-iitk/CS507A` repository
- [ ] On GitHub, create a release (e.g. `v1.0`); Zenodo archives it and mints a DOI, using
      `.zenodo.json` and `CITATION.cff`
- [ ] Put the DOI into `paper/main.tex` (Data Availability) and `README.md`
