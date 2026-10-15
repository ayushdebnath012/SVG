# Astra morphing-wing Test 7 trial

One paid call; low reasoning; complete code; no repairs. Source CAD and source numerical table were already present in v1.7. This is a newly tested case, not a newly discovered dataset.

| Output | Astra (Hz) | Published (Hz) | Error |
|---|---:|---:|---:|
| f_1B_Hz | 8.701469 | 9.32097 | -6.646% |
| f_1T_Hz | 110.8133 | 118.63 | -6.589% |
| f_2B_Hz | 54.13494 | 57.9984 | -6.661% |

Canonical numerical score: 0/1. Sandbox execution succeeded in 7.99 seconds. No resource limit hit; frozen inputs unchanged. Workflow review pending.

All values miss the provisional 5% band. Two quadratic solid meshes change by 0.041%, 0.484%, and 0.051%. Reference workbook T128/T129/T130 checked directly. Source BDF E=2.11 GPa, nu=0.3, density=1180 agree with prompt and submitted material. Source shell versus submitted solid formulation needs independent adjudication; this is not yet a confirmed capability failure.

Call cost conservative estimate: $0.2375375. Session total: $1.1049250 of $1.25; remaining $0.1450750. No further calls dispatched.

Source: https://data.mendeley.com/datasets/8jxw5533py/1

Evidence: request.json, response.json, submission/main.py, replay/execution.json, replay/outputs/, scoring/score.json, outcome.json.
