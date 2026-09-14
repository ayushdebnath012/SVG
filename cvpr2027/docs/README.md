# Research documents

Five review PDFs are in `../output/pdf/`; corresponding standalone LaTeX files are in `latex/`. Markdown is the canonical authoring format. The builder combines the proposal/protocol sources here with `../reports/` and `../paper/manuscript.md`; editing generated LaTeX directly is possible but a rebuild replaces it.

From the `cvpr2027` folder:

```sh
.venv/bin/python -m pip install -r requirements-docs.txt
# Install Tectonic 0.17.0 or newer using its official distribution.
.venv/bin/python scripts/build_docs.py --tectonic /path/to/tectonic
```

Tectonic official releases: https://github.com/tectonic-typesetting/tectonic/releases . The first compilation downloads TeX packages and needs network access. `TECTONIC` can alternatively specify the binary, or put `tectonic` on PATH. Pandoc is supplied by the pinned `pypandoc_binary` dependency. The locally downloaded compiler is intentionally outside version control in `.tools/`.

To compile one generated LaTeX document independently, run Tectonic on `docs/latex/<name>.tex`. Its image paths are relative to the LaTeX file's directory (`../../paper/...` or `../../runs/...`). With a conventional XeLaTeX toolchain, change into `docs/latex/` and compile there, repeating for the contents and references. These are working article layouts, not the venue's official style.

The source mapping is visible in `scripts/build_docs.py`. `build_manifest.json` lists the five outputs. `latex/header.tex` and `latex/inline-code.lua` control typography and identifier wrapping. PDF build logs and temporary page renders are ignored. `scripts/verify_package.py` checks the packaged hashes; `reports/pdf_qa.json` records final PDF page counts and layout checks.

The proposal and protocol explicitly distinguish hypotheses from completed measurements. The survey includes primary-source links; `papers/references.bib` is a reusable bibliography, and the working paper still needs its final venue-specific citation and formatting pass.
