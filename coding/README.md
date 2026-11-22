# Manual coding — how to run it

Files in this folder:

| File | What it is |
|---|---|
| `CODEBOOK.md` / `codebook.json` | Coding rules (A categories, C coverage, D newcomer need + barriers). Edit both together. |
| `assignments.csv` | One row per repo: set (pilot / reliability / main), coding order, unit weight, sensitivity flags. |
| `queue.csv` | The 1,564 agent units to code, in order (≤ 10 per repo). |
| `labels/pass1.jsonl` | Your labels, append-only (every save is kept; the latest per unit wins). |
| `labels/pass2.jsonl` | Blind second coding of the reliability set (a different annotator). |
| `labels/pass2_discarded_*.jsonl` | Earlier pass-2 attempts set aside (kept for the record, never analysed). |
| `annotators.json` | Who each coder is: `human` or `llm` (+ model). The reliability report and the paper's wording follow it. |
| `coder_aliases.json` | Maps alternative spellings of one coder's name together. |
| `fill_v1.py`, `fill_v2.py` | Model fills of missing evidence/need fields, marked `filled_by` in the labels. |
| `prelabels.csv` | Optional LLM category suggestions (created by `gapstudy.prelabel`). |

## Start the tool

```bash
cd ~/CS507A
.venv/bin/python -m gapstudy.labeltool.app          # prints a URL with ?token=...
```

Open the printed URL in your browser, **including the `?token=...` part**. In VS Code (Remote
SSH) port 8507 is forwarded automatically (see the **Ports** tab); otherwise run
`ssh -L 8507:localhost:8507 <login node>` on your laptop first. Stop the server with Ctrl+C.
Labels are saved on every click of **Save & next**, so you can stop at any time.

The token stays the same across restarts (stored in `coding/.labeltool_token`, git-ignored), and
the browser remembers it after the first visit. "Access token missing" means the link was opened
without it, e.g. via the Ports tab's globe button; print the full link with:

```bash
echo "http://localhost:8507/?token=$(cat coding/.labeltool_token)"
```

Keys: `1`–`4` coverage · `A` accept the AI draft · `Ctrl+Enter` save and next · `/` search the human docs.

## Verify mode (AI drafts)

Labels for the pilot and main sets are first drafted by Claude (`coding/drafts.jsonl`, one
rationale per unit). Each verifier enters their name once (saved in the browser). For every unit
the form starts pre-filled with the draft, and its covering human sections are ticked on the
right. Check the draft against the human docs, then either press **Accept draft** (`A`) or
correct the form and save. Each save records the verifier, whether a draft was shown, and which
fields (coverage, categories, evidence, need, barriers, flags) were changed.

**Reliability set: blind.** Its 338 units never show a draft. Pass 1 is the first person's blind
label; pass 2 (`?pass=2` in the link) is a **different** person's blind label of the same units,
for inter-rater agreement. Pass 2 only offers units someone else labelled first.

## What was done (record)

| Set | Repos | Units | How it was coded |
|---|---|---|---|
| Pilot | 20 | 161 | Claude draft → reviewed by the annotator (kept or corrected) |
| Main | 141 | 1,065 | Claude draft → reviewed by the annotator (64 coverage corrections overall) |
| Reliability | 40 | 338 | Pass 1: annotator, blind (no draft). Pass 2: independent second annotator, blind — currently an LLM (OpenAI Codex), see `annotators.json` |

Two earlier pass-2 attempts (κ ≈ 0, nearly every unit labelled agent-only within minutes) were
set aside as `labels/pass2_discarded_*.jsonl`. Final labels are pass 1's; where pass 1 left the
newcomer need/barriers empty on a gap unit, `gapstudy.freeze` takes them from pass 2 when both
coders judged a gap (`need_source` column). To add a **human** second coder later: they label via
`…/?pass=2&token=…` under their own name, you add them to `annotators.json` as `human`, and rerun
`python -m gapstudy.pipeline`.

## After the pilot: report and codebook v1.0

```bash
.venv/bin/python -m gapstudy.pilot_report      # writes analysis/phase4/pilot_report.md
```

It lists every note and flagged unit (the hard cases), consistency problems (e.g. *partial*
without evidence), label distributions and your pace. Send it to Claude to revise the codebook to
v1.0. Then re-check the pilot units against v1.0: open the tool with `&recheck=1` added to the
link. Only pilot units labelled under an older codebook version are shown.

## Optional: LLM category suggestions

Model: **Qwen3-Coder-30B-A3B-Instruct** (Apache-2.0), pinned to revision `b2cff64…`. It runs on
one H100 through vLLM. One-time setup on a login node:

```bash
bash scripts/llm/setup_vllm.sh        # vLLM environment in $SCRATCH/vllm-venv
bash scripts/llm/download_model.sh    # ~61 GB of weights to $SCRATCH/hf_models/
```

Then a trial on 20 units, check the suggestions, and run the rest:

```bash
sbatch --export=ALL,LIMIT=20 scripts/llm/prelabel.sbatch
sbatch scripts/llm/prelabel.sbatch    # skips units already pre-labelled
```

Suggestions appear in the tool as pre-ticked ★ categories. Only categories are pre-labelled;
coverage is always yours, because it is the ground truth for the RQ3 detector. The pilot report
shows how well the suggestions agree with your choices.

## Phase 5: full coding, reliability, freeze

```bash
.venv/bin/python -m gapstudy.progress       # done vs schedule, units/day needed per set
.venv/bin/python -m gapstudy.reliability    # pass 1 vs pass 2: κ with repo-bootstrap CIs → analysis/phase5/reliability.md
.venv/bin/python -m gapstudy.freeze         # checks + writes coding/labels_v1.csv and its sha256
```

`freeze` refuses while units are unlabelled, labelled under an older codebook, or inconsistent
(e.g. *shared* with no evidence ticked, or a gap unit with no newcomer need), and says which.
In practice, run everything with `python -m gapstudy.pipeline` (see the main README). All later analyses read only
`labels_v1.csv`, so the numbers in the paper trace back to one checksummed file.

## Regenerating the inputs

```bash
.venv/bin/python -m gapstudy.units        # data/processed/units.csv
.venv/bin/python -m gapstudy.assign       # assignments.csv, queue.csv (cap 10, seed 507)
```

Do **not** re-run `assign` after coding has started: it would change the queue.
