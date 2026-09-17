"""Build five review PDFs and editable LaTeX sources from the research records.

Requires pandoc (or pypandoc_binary) and Tectonic. Run from any directory.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def source(path):
    path=ROOT/path;text=path.read_text()
    text=re.sub(r'^# .*?\n','',text,count=1)
    # Resolve images relative to the source, then keep TeX paths portable to ROOT.
    def picture(m):
        target=(path.parent/m[2]).resolve().relative_to(ROOT)
        return f'![{m[1]}](../../{target.as_posix()})'
    text=re.sub(r'!\[([^]]*)\]\(([^)]+)\)',picture,text)
    def link(m):
        if m[2].startswith(('http:', 'https:', 'mailto:', '#')):
            return m[0]
        name, mark, anchor=m[2].partition('#')
        target=(path.parent/name).resolve().relative_to(ROOT)
        return f'[{m[1]}](../../{target.as_posix()}{mark}{anchor})'
    text=re.sub(r'(?<!!)\[([^]]*)\]\(([^)]+)\)',link,text)
    return re.sub(r'^(#{2,}) ', lambda m: m[1][1:]+' ', text, flags=re.MULTILINE)

def normalized(text):
    text=re.sub(r'^(#{1,6})\s+\d+(?:\.\d+)*\.?\s+', r'\1 ', text, flags=re.MULTILINE)
    # Inline code must remain code, not contain escaped math-mode delimiters.
    def ascii_code(m):
        t=m[0]
        for a,b in {'²':'^2','³':'^3','∫':'integral','∇':'grad','×':'*','−':'-','≤':'<=','≥':'>='}.items():
            t=t.replace(a,b)
        return t
    text=re.sub(r'`[^`\n]+`',ascii_code,text)
    for a,b in {'—':' - ','–':'-','‑':'-','−':'-','≈':r'$\approx$','≤':r'$\leq$',
                '≥':r'$\geq$','×':r'$\times$','∇':r'$\nabla$','Ω':r'$\Omega$',
                'θ':r'$\theta$','ε':r'$\varepsilon$','σ':r'$\sigma$',
                '²':r'$^2$','³':r'$^3$','∞':r'$\infty$','⁻¹⁸':r'$^{-18}$',
                '⁻¹⁴':r'$^{-14}$','⁻':'-','¹':'1','⁴':'4','⁸':'8','∂':r'$\partial$'}.items():
        text=text.replace(a,b)
    return text.replace('Honest accepted (40 cases)', 'Honest accepts / 40').replace('Corrupt accepted (120 cases)', 'Corrupt accepts / 120')

def main():
    p=argparse.ArgumentParser();p.add_argument('--tectonic',default=os.environ.get('TECTONIC','tectonic'))
    a=p.parse_args();pandoc=shutil.which('pandoc')
    if not pandoc:
        import pypandoc;pandoc=pypandoc.get_pandoc_path()
    out=ROOT/'output/pdf';texdir=ROOT/'docs/latex';generated=ROOT/'docs/source/generated'
    for folder in (out,texdir,generated):folder.mkdir(parents=True,exist_ok=True)
    graphics=source(Path('reports/PRIOR_ART.md'))
    graphics=graphics.split('# Closest work and what to reuse',1)[1].split('# Recommended research question',1)[0]
    literature=source(Path('reports/FEM_LITERATURE_AND_EXTENSION.md'))+'\n\\clearpage\n\n# Graphics and adjacent prior art\n'+graphics
    literature+='\n# Paper archive\n\nThe catalog and bibliography are in `papers/`. Downloaded PDFs retain their original authorship and publication notices. The download manifest distinguishes bundled PDFs from source links and unavailable downloads. This package does not bypass publisher access controls.\n'
    status=source(Path('reports/RESEARCH_STATUS.md'))
    # Historical and manufactured numeric tables, excluding duplicated schedule/planning prose.
    historical=status.split('# Correction to historical proposal claims',1)[1].split('# Training pilot scope',1)[0]
    historical=historical.replace('# Manufactured corruption controls', '\\clearpage\n\n# Manufactured corruption controls')
    evidence=source(Path('reports/ASTRA_FEM_FAILURE_RECHECK.md'))+'\n\\clearpage\n\n# A100 training results\n'+source(Path('reports/TRAINING_RESULTS.md'))+'\n\n# Historical audit and manufactured controls\n'+historical
    docs=[('research_proposal','Research Proposal',source(Path('docs/source/research_proposal.md'))),
          ('experiment_protocol','Experiment Protocol and Work Plan',source(Path('docs/source/experiment_protocol.md'))),
          ('literature_survey','Literature Survey and Reuse Decisions',literature),
          ('results_and_failure_audit','Completed Results and Failure Audit',evidence),
          ('working_paper','Auditing Numerical Claims in Editable Engineering SVGs',source(Path('paper/manuscript.md')))]
    built=[]
    for stem,title,text in docs:
        md=generated/f'{stem}.md';md.write_text(normalized(text).strip()+"\n")
        tex=texdir/f'{stem}.tex'
        command=[pandoc,str(md),'-f','markdown+autolink_bare_uris','-t','latex','--standalone','--number-sections',
                 '--toc','--toc-depth=2','--syntax-highlighting=none',
                 '--lua-filter',str(texdir/'inline-code.lua'),
                 '-V','documentclass=article','-V','papersize=a4','-V','fontsize=11pt',
                 '-V','geometry:margin=24mm','-V','colorlinks=true','-V','urlcolor=blue',
                 '-M','title='+title,'-M','author=SVG Patch Lab - Research Working Package',
                 '-M','date=14 September 2026 | CVPR 2027 target',
                 '-H',str(texdir/'header.tex'),'-o',str(tex)]
        subprocess.run(command,cwd=ROOT,check=True)
        log=ROOT/'tmp/pdfs'/f'{stem}.build.txt';log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('w') as stream:
            result=subprocess.run([a.tectonic,str(tex),'--outdir',str(out),'--keep-logs'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(f'Build failed: {log}')
        built.append({'pdf':str((out/f'{stem}.pdf').relative_to(ROOT)),
                      'latex':str(tex.relative_to(ROOT)),'title':title})
        print('BUILT',stem,flush=True)
    # Hand-authored LaTeX (not generated from Markdown); compiled with the same engine and style.
    for stem,title in [('research_overview','Consolidated Research Overview: Problem, Theory, Architecture, Experiments and Plan')]:
        tex=texdir/f'{stem}.tex'
        log=ROOT/'tmp/pdfs'/f'{stem}.build.txt'
        with log.open('w') as stream:
            result=subprocess.run([a.tectonic,str(tex),'--outdir',str(out),'--keep-logs'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(f'Build failed: {log}')
        built.append({'pdf':str((out/f'{stem}.pdf').relative_to(ROOT)),'latex':str(tex.relative_to(ROOT)),'title':title,'source':'hand-authored LaTeX'})
        print('BUILT',stem,flush=True)
    (ROOT/'docs/build_manifest.json').write_text(json.dumps(built,indent=2)+'\n')

if __name__=='__main__':main()
