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

## Optional: LLM category suggestions

Serve any open-source instruction model with an OpenAI-compatible API (vLLM, Ollama or
llama.cpp), then:

```bash
.venv/bin/python -m gapstudy.prelabel --base-url http://localhost:8000/v1 --model <model> --limit 20
```

Check the 20 trial suggestions before running on everything. Suggestions appear in the tool as
pre-ticked ★ categories. Only categories are pre-labelled; coverage is always yours, because it is
the ground truth for the RQ3 detector. Record the exact model name and version for the paper.

Running a model on the cluster: compute nodes have no internet, so download the weights on a
login node, then start the server inside a GPU job (`salloc --gpus=1 ...`) and tunnel to it.

## Regenerating the inputs

```bash
.venv/bin/python -m gapstudy.units        # data/processed/units.csv
.venv/bin/python -m gapstudy.assign       # assignments.csv, queue.csv (cap 10, seed 507)
```

Do **not** re-run `assign` after coding has started: it would change the queue.
