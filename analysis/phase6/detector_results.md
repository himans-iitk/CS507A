# RQ3 — Gap detector results

Dev = pilot repos (n = 139 units); test = reliability + main (n = 1284). Agent-directed units excluded. 95% CIs: repo bootstrap.

| Matcher | Score (chosen on dev) | Precision | Recall | F1 agent-only | ROC-AUC | Macro-F1 (3 class) | Gold section in top 1 / top 5 |
|---|---|---|---|---|---|---|---|
| BAAI/bge-base-en-v1.5 | item_mean | 0.68 | 0.84 | 0.75 [0.71, 0.79] | 0.87 [0.85, 0.89] | 0.59 | 0.71 / 0.96 (n = 760) |
| Qwen/Qwen3-Embedding-0.6B | item_cov@0.65 | 0.67 | 0.83 | 0.74 [0.70, 0.78] | 0.84 [0.82, 0.87] | 0.62 | 0.69 / 0.95 (n = 760) |
| sentence-transformers/all-MiniLM-L6-v2 | item_cov@0.55 | 0.62 | 0.90 | 0.73 [0.69, 0.76] | 0.83 [0.80, 0.85] | 0.63 | 0.69 / 0.94 (n = 760) |
| tfidf | item_mean | 0.69 | 0.85 | 0.76 [0.72, 0.79] | 0.88 [0.86, 0.90] | 0.60 | 0.66 / 0.95 (n = 760) |
