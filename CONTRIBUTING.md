# Contributing

Start with a focused problem, example input/output, and the acceptance criterion. Preserve exact scope isolation and document any change to retries, revisions, expiry, or deletion semantics. New providers must be opt-in, use explicit configuration, and include failure/timeout tests. Never add secrets, private conversations, or fabricated evaluation results.

Before a pull request:

```bash
python -m unittest discover -s tests -v
node --test sdk/javascript/test.mjs
python -m examples.quickstart
python -m evals.run --out work/new-eval.json
```

Update API documentation and capability status when behavior changes. Keep the original license and provenance of any reused third-party material. A synthetic fixture pass is not evidence for a broad performance claim.
