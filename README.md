# Whatnot Agent

A clean four-stage Playwright architecture:

1. `auth_bootstrap.py` for one-time headed manual login and auth export.
2. `verify_session.py` to classify session state as `VALID`, `EXPIRED`, or `CHECKPOINT`.
3. `extract_orders.py` to navigate and scrape sold orders with no runtime login path.
4. `postprocess_orders.py` to normalize, group buyers, and flag bundles.

## Suggested flow

- Run bootstrap locally in headed mode.
- Reuse `artifacts/auth_state.json` in scheduled runs.
- Run pipeline only after verify passes.
