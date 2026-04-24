# PolicyClaw Evals

Deterministic pass/fail harness for the four-call GLM pipeline plus the
FutureClaw simulation surface. Complements `backend/tests/` (which exercises
individual functions) by asserting end-to-end properties that must hold for
every `PolicyInput` fixture — verdict labels are valid, health sub-scores are
bounded, life-event scenarios are the right count, etc.

## Run

From the repo root:

```bash
python evals/run.py
```

Exit code 0 on ≥ 85% pass rate, 1 otherwise — so CI / `make ci-local` can gate
on it. Latest committed run result:
[`results.md`](results.md).

## How it works

- `cases.json` — declarative case list. Each entry has a `stage`
  (`extract` / `score` / `recommend` / `life_event` / `affordability`), an
  `input_fixture` key, and an `expected` block of property assertions.
- `fixtures/policy_inputs.py` — canned `PolicyInput` objects for the three
  Malaysian policy archetypes the demo covers (young-saver medical, takaful
  family, mid-life critical illness).
- `run.py` — loads cases, invokes the matching service-layer call
  (`analyze_policy_xray`, `analyze_health_score`, `analyze_policy_verdict`,
  `simulate_life_events`, `monte_carlo_affordability`), applies the
  assertions, tallies, and writes [`results.md`](results.md).

## Mock vs live GLM

`run.py` clears `GLM_API_KEY` before importing `app.*`, so every stage falls
into its deterministic mock/heuristic path. This is intentional: a judge
running the harness without an API key still gets a meaningful signal, and
CI doesn't burn live GLM credits. To run against real GLM, comment out the
`os.environ.pop("GLM_API_KEY", None)` line at the top of `run.py` and export
your key.

## Adding a case

1. Add the scenario to `cases.json` with a new `id`.
2. If you need a new fixture, add it to `fixtures/policy_inputs.py`.
3. If you need a new assertion keyword, wire it in
   `_check_assertions` in `run.py`.
4. Re-run and commit the updated `results.md`.

## Known limits

- The `annotate` GLM call (ClawView) needs real PDF bytes + PyMuPDF
  bounding boxes; it's exercised by `backend/tests/test_orchestrator.py`
  instead of this harness.
- Mock outputs are stable by design — if you upgrade the heuristics, expect
  to retune some `expected` bounds (e.g. `overall_max`).
