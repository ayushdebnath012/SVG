# Released drawing inputs: evaluation only

Public CADGenBench cases 149 and 131, by HuggingAI4Engineering, with geometry sourced from Mecado. The upstream dataset card declares ODC-BY. Preserve attribution and the included source card. These cases and derivatives are excluded from training.

`manifest.json` pins downloaded image content. The original `input.png` is accompanied by three enlarged crops; crops add no geometry or dimensions. Private reference geometry was not downloaded. This is a local partial audit, not an official leaderboard reproduction.

Run a fresh attempt (incurs OpenAI API usage):

```sh
.venv/bin/python cvpr2027/scripts/cad_released_drawing_probe.py NEW_OUTPUT_DIRECTORY --case 131
```

The runner uses `gpt-6-astra`, high effort, up to 24,000 output tokens per API turn and four CAD tool calls. Credentials are read from the existing environment or ignored `.env`, never from these data files. Existing completed runs cannot be overwritten. `--resume` resumes the saved request after an operational/API interruption; it does not create an independent trial or a failure confirmation.

Audit saved solids without API calls:

```sh
cvpr2027/tmp/cad-runtime/bin/python cvpr2027/scripts/audit_released_149.py INPUT.step OUTPUT.json
cvpr2027/tmp/cad-runtime/bin/python cvpr2027/scripts/audit_released_131.py INPUT.step OUTPUT.json
```

CadQuery 2.8 / OCP 7.9.3.1.1 was used. Chrome renders the exported SVG. The local checks cover only named dimensional features and are not a full-shape verifier. Representation-dependent surface counts require manual review before any failure verdict.
