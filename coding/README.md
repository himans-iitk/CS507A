# Manual coding — how to run it

Files in this folder:

| File | What it is |
|---|---|
| `CODEBOOK.md` / `codebook.json` | Coding rules (A categories, C coverage, D newcomer need + barriers). Edit both together. |
| `assignments.csv` | One row per repo: set (pilot / reliability / main), coding order, unit weight, sensitivity flags. |
| `queue.csv` | The 1,564 agent units to code, in order (≤ 10 per repo). |
| `labels/pass1.jsonl` | Your labels, append-only (every save is kept; the latest per unit wins). |
| `labels/pass2.jsonl` | Blind re-code of the reliability set. |
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

Keys: `1`–`4` coverage · `Ctrl+Enter` save and next · `/` search the human docs.

## Order and schedule (deadline: end of November)

| Dates | Step | Units |
|---|---|---|
| Oct 27 – Nov 1 | **Pilot** (20 repos). Note every hard case. Then update the codebook to v1.0 and re-check the pilot units. | 161 |
| Nov 2 – Nov 4 | **Reliability set** (40 repos) — first, so the 14-day clock starts early. | 338 |
| Nov 4 – Nov 14 | **Main set** (141 repos), ~100 units/day. | 1,065 |
| Nov 16 – Nov 19 | **Re-code**: open `…/?pass=2&token=…`. Only reliability units whose first label is ≥ 14 days old appear, shuffled, with your first labels hidden. | 338 |

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
.venv/bin/python -m gapstudy.reliability    # after the re-code: κ with repo-bootstrap CIs → analysis/phase5/reliability.md
.venv/bin/python -m gapstudy.freeze         # checks + writes coding/labels_v1.csv and its sha256
```

`freeze` refuses while units are unlabelled, labelled under an older codebook, or inconsistent
(e.g. *shared* with no evidence ticked), and says which. All later analyses read only
`labels_v1.csv`, so the numbers in the paper trace back to one checksummed file.

## Regenerating the inputs

```bash
.venv/bin/python -m gapstudy.units        # data/processed/units.csv
.venv/bin/python -m gapstudy.assign       # assignments.csv, queue.csv (cap 10, seed 507)
```

Do **not** re-run `assign` after coding has started: it would change the queue.
