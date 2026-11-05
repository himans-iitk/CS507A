import json, sys
from gapstudy.labels import LabelStore
EV = {
 "AgustinOberg/leshi-ui::agent::28": ["README::13","README::14"],
 "microsoft/GSL::agent::5": ["README::3","README::5"],
 "christianhelle/autofaker::agent::4": ["README::4","CONTRIBUTING::10"],
 "christianhelle/autofaker::agent::8": ["README::3","README::4"],
 "christianhelle/autofaker::agent::20": ["README::4","CONTRIBUTING::10"],
 "valkey-io/valkey-glide::agent::10": ["README::6","CONTRIBUTING::4"],
 "hahwul/dalfox::agent::6": ["CONTRIBUTING::3","CONTRIBUTING::4","CONTRIBUTING::5"],
 "hahwul/dalfox::agent::7": ["README::1","README::6"],
 "hahwul/dalfox::agent::14": ["README::1","README::6"],
 "zenml-io/zenml::agent::15": ["CONTRIBUTING::6"],
 "zenml-io/zenml::agent::24": ["CONTRIBUTING::11","CONTRIBUTING::12"],
 "microsoft/powerplatform-vscode::agent::2": ["README::0"],
 "estruyf/vscode-demo-time::agent::3": ["README::4"],
 "miurla/morphic::agent::7": ["README::8"],
 "luno/luno-mcp::agent::5": ["README::14","CONTRIBUTING::3"],
 "ArtifactLabs/git-recycle-bin::agent::7": ["CONTRIBUTING::0"],
 "TanStack/router::agent::2": ["README::1","README::3"],
 "TanStack/router::agent::6": ["CONTRIBUTING::0"],
 "featureform/enrichmcp::agent::2": ["README::17","README::20"],
 "sbalci/ClinicoPathJamoviModule::agent::6": ["README::14","README::19"],
 "karakeep-app/karakeep::agent::3": ["README::1"],
 "bruin-data/bruin::agent::4": ["README::0"],
 "riffcc/flagship::agent::7": ["README::0","README::4","CONTRIBUTING::2"],
 "Nugine/const-str::agent::4": ["README::0"],
 "Nugine/const-str::agent::9": ["README::0","CONTRIBUTING::0"],
 "safe-global/safe-wallet-monorepo::agent::0": ["README::1"],
 "safe-global/safe-wallet-monorepo::agent::1": ["README::11","CONTRIBUTING::3"],
 "microsoft/qsharp::agent::4": ["README::1","README::4"],
 "towns-protocol/towns::agent::8": ["README::0"],
 "actnwit/RhodoniteTS::agent::17": ["README::3"],
 "actnwit/RhodoniteTS::agent::20": ["README::2"],
 "receptron/mulmocast-app::agent::13": ["CONTRIBUTING::2"],
 "stellar/stellar-cli::agent::12": ["CONTRIBUTING::7"],
 "thirdweb-dev/js::agent::10": ["CONTRIBUTING::4"],
 "monarch-initiative/aurelian::agent::7": ["CONTRIBUTING::4"],
 "jdx/mise::agent::7": ["README::8"],
 "Azure/terraform-azurerm-avm-res-keyvault-vault::agent::4": ["README::11"],
 "owncast/owncast::agent::8": ["README::7","README::8"],
 "AccelerationConsortium/ac-training-lab::agent::4": ["CONTRIBUTING::4"],
 "evmts/guillotine::agent::17": ["CONTRIBUTING::15"],
 "operaton/operaton::agent::17": ["README::4","CONTRIBUTING::5"],
}
NEED = {  # need, barriers
 "dagster-io/dagster::agent::12": ("task_process", ["process_practices"]),
 "dotnet/core::agent::14": ("development_process", ["process_practices"]),
 "zenml-io/zenml::agent::23": ("development_process", ["process_practices"]),
 "claude-did-this/MCPControl::agent::2": ("development_process", ["process_practices"]),
 "Nugine/const-str::agent::9": ("low_level_design", ["technical_background"]),
 "openai/openai-agents-js::agent::13": ("dev_environment_tools", ["environment_setup"]),
 "stellar/stellar-cli::agent::12": ("dev_environment_tools", ["environment_setup"]),
 "mikedemarais/granola-ts-client::agent::17": ("development_process", ["process_practices"]),
 "dotnet/docs-desktop::agent::0": ("development_process", ["contribution_flow"]),
 "owncast/owncast::agent::6": ("development_process", ["contribution_flow"]),
 "owncast/owncast::agent::8": ("development_process", ["process_practices"]),
 "evmts/tevm-monorepo::agent::13": ("dev_environment_tools", ["environment_setup"]),
 "binbashar/le-ref-architecture-doc::agent::6": ("repository_search", ["finding_artifacts"]),
}
cb = json.load(open("coding/codebook.json"))
import pandas as pd
hum = set(pd.read_csv("data/processed/units.csv").query("doc != 'agent'").unit_id)
store = LabelStore(); latest = store.latest(1)
n = 0
for uid in sorted(set(EV) | set(NEED)):
    r = dict(latest[uid]); filled = []
    if uid in EV:
        ev = [f"{uid.split('::')[0]}::{e}" for e in EV[uid]]
        assert all(e in hum for e in ev), (uid, ev)
        assert r["coverage"] in ("partial", "shared") and not r.get("evidence"), uid
        r["evidence"] = ev; filled.append("evidence")
    if uid in NEED:
        need, bars = NEED[uid]
        assert r["coverage"] in ("agent_only", "partial") and not r.get("need"), uid
        assert need in cb["needs"] and all(b in cb["barriers"] for b in bars)
        r["need"] = need; filled.append("need")
        if not r.get("barriers"):
            r["barriers"] = bars; filled.append("barriers")
    r.update(needs_detail=False, filled_by="claude-opus-5.5", filled_fields=filled, tool="fill")
    for k in ("pass", "saved_at"): r.pop(k, None)
    if "--dry" not in sys.argv: store.save(1, r)
    n += 1
print("filled", n)
