# PolicyClaw Eval Results

- **Overall:** 12/12 passed (100.0%)
- **Threshold:** ≥ 85% required
- **Mode:** mock (OPENAI_API_KEY absent — stages exercise deterministic fallbacks)
- **LLM config resolved:** model=gpt-5-mini, base=https://api.openai.com/v1

## By stage

| Stage | Passed | Total | Rate |
|-------|-------:|------:|-----:|
| affordability | 1 | 1 | 100% |
| extract | 3 | 3 | 100% |
| life_event | 2 | 2 | 100% |
| recommend | 3 | 3 | 100% |
| score | 3 | 3 | 100% |

## Case detail

- ✅ `extract.happy_path_medical` — ok
- ✅ `extract.policy_id_echoes` — ok
- ✅ `extract.gotcha_count_matches_flags` — ok
- ✅ `score.subscores_in_range` — ok
- ✅ `score.overall_not_over_95` — ok
- ✅ `score.narratives_non_empty` — ok
- ✅ `recommend.verdict_label_valid` — ok
- ✅ `recommend.at_least_two_reasons` — ok
- ✅ `recommend.projected_savings_nonneg` — ok
- ✅ `life_event.four_scenarios` — ok
- ✅ `life_event.covered_le_total` — ok
- ✅ `affordability.three_scenarios_ordered` — ok
