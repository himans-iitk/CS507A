"""Fill D1/D2 for the 7 reliability units whose pass-1 label lacks a newcomer need and whose
pass-2 coder did not judge them a gap (so combine() cannot borrow one). Drafted by Claude,
marked filled_by. Coverage, categories and evidence are untouched."""
import json

from gapstudy.labels import LabelStore

NEED = {  # need, barriers
    "getsentry/sentry-javascript::agent::1": ("product_domain", ["domain_expertise"]),
    "Azure/dalec::agent::0": ("product_domain", ["domain_expertise"]),
    "mkwatson/ai-fastify-template::agent::21": ("dev_environment_tools", ["technical_background"]),
    "microsoft/autogen::agent::11": ("software_architecture", ["code_architecture", "finding_artifacts"]),
    "julep-ai/julep::agent::6": ("developer_documentation", ["process_practices"]),
    "julep-ai/julep::agent::20": ("development_process", ["process_practices"]),
    "Teri-anric/AnimeStarsExtensions::agent::0": ("development_process", ["contribution_flow"]),
}
cb = json.load(open("coding/codebook.json"))
store = LabelStore()
latest = store.latest(1)
for uid, (need, bars) in NEED.items():
    r = dict(latest[uid])
    assert r["coverage"] in ("agent_only", "partial") and not r.get("need"), uid
    assert need in cb["needs"] and all(b in cb["barriers"] for b in bars)
    r.update(need=need, barriers=bars, filled_by="claude-opus-5.5", filled_fields=["need", "barriers"], tool="fill")
    for k in ("pass", "saved_at"):
        r.pop(k, None)
    store.save(1, r)
print("filled", len(NEED))
