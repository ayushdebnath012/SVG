"""Build a portable Colab GPU notebook with public data, contracts, scripts and no credentials."""
import base64,hashlib,io,json,tarfile,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/multisource-cad-edits-v1';bio=io.BytesIO()
with tarfile.open(fileobj=bio,mode='w:gz') as t:
 def add(name,data):
  info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;t.addfile(info,io.BytesIO(data))
 for name in ['train_multisource_cad_colab.py','cad_edit_contracts.py','cad_editor_geometry.py','verify_mechanical_cad_edits.py','mechanical_cad_fem.py','run_verified_cad_edit.py','score_multisource_cad_geometry.py','colab_verify_mechanical_examples.py']:
  add('scripts/'+name,(ROOT/'scripts'/name).read_bytes())
 m=json.loads((DATA/'manifest.json').read_text());m['prepared_local_file_hashes']=m['files'];m['files']={}
 for split in ['train','validation','test']:
  rows=list(map(json.loads,(DATA/f'{split}.jsonl').read_text().splitlines()))
  for r in rows:
   if r.get('reference_step'):r['reference_step']='/content/cad_edit/references/'+r['id']+'.step'
  data=''.join(json.dumps(r)+'\n' for r in rows).encode();m['files'][split]=hashlib.sha256(data).hexdigest();add('data/'+split+'.jsonl',data)
 m['portable_reference_remap']='Only STEP metadata paths changed; instructions, source/target strings and patches unchanged.';add('data/manifest.json',json.dumps(m,indent=2).encode())
 for f in (ROOT/'data/benchcad-online-edit-v1/reference-step').glob('*.step'):add('references/'+f.name,f.read_bytes())
 add('example-contracts.json',(ROOT/'runs/mechanical-cad-fem-20261002/contracts.json').read_bytes())
payload=bio.getvalue();encoded='\n'.join(textwrap.wrap(base64.b64encode(payload).decode(),1024));cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s,hidden=False):cells.append(dict(cell_type='code',execution_count=None,outputs=[],metadata={'cellView':'form','source_hidden':True} if hidden else {},source=s.splitlines(True)))
md('# Mechanical CAD editing: multi-source QLoRA + executed geometry + FEM\n\nFresh Qwen2.5-Coder-3B-Instruct, two epochs, BenchCAD + Microsoft CAD-Editor.\nUse **Runtime → Change runtime type → GPU**, then **Run all**. This notebook contains the audited public edit subset and its STEP references; no SSH passwords or API keys.\n\nThe model predicts edits. External solvers validate geometry and six explicitly contracted FEM examples. Missing/failed FEM stays not verified. Actual operating safety is not established. No drawing-perception or FEM-reward training is claimed.')
code('!pip -q install "transformers==4.51.3" "peft==0.15.2" accelerate bitsandbytes "cadquery==2.8.0" "gmsh==4.15.2" meshio scipy\n!apt-get -qq update && apt-get -qq install -y libglu1-mesa libgl1\nimport torch\nassert torch.cuda.is_available(), "Select a GPU runtime first"\nprint(torch.cuda.get_device_name(0), torch.cuda.mem_get_info())')
code('#@title Unpack audited public CAD edit data and scripts\nimport base64, hashlib, io, tarfile\nfrom pathlib import Path\n# Audited public source package; embedded for a credential-free portable notebook.\nencoded = """\n'+encoded+'\n"""\nbundle=base64.b64decode(encoded)\nassert hashlib.sha256(bundle).hexdigest()=="'+hashlib.sha256(payload).hexdigest()+'"\nROOT=Path("/content/cad_edit"); ROOT.mkdir(exist_ok=True)\nwith tarfile.open(fileobj=io.BytesIO(bundle),mode="r:gz") as t: t.extractall(ROOT,filter="data")\nprint("Source package verified and extracted")',True)
md('## Training and before/final evaluation\n\n4-bit NF4 double quantization; BF16 on capable GPUs, FP16 on T4. LoRA rank 16, alpha 320, last 12 blocks, all attention/MLP projections. Effective batch four; 4,096-token context; 768-token generation cap. Final checkpoint only. All retained held-out cases are evaluated and exclusions recorded. No reference edits repair model outputs.')
code('import subprocess, sys, json\nfrom pathlib import Path\nROOT=Path("/content/cad_edit")\nRUN=ROOT/"results"\nif (RUN/"run_manifest.json").exists() and json.loads((RUN/"run_manifest.json").read_text())["status"]=="completed":\n    print("Completed run already exists; not training twice")\nelse:\n    assert not RUN.exists(), "Incomplete run exists: inspect before resuming or choose a new output directory"\n    process=subprocess.Popen([sys.executable,"-u",str(ROOT/"scripts/train_multisource_cad_colab.py"),"--data",str(ROOT/"data"),"--output",str(RUN)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)\n    for line in process.stdout: print(line,end="",flush=True)\n    assert process.wait()==0, "Training failed; inspect the log"')
md('## Execute both native CAD representations\n\nBenchCAD uses author-released STEP targets. CAD-Editor uses locally reconstructed six-bit sketch/extrude targets; these are not author-released STEP files. Geometry metrics stay separate by dataset.')
code('for label in ["base","trained"]:\n    subprocess.run([sys.executable,"-u",str(ROOT/"scripts/score_multisource_cad_geometry.py"),str(RUN/(label+"-predictions.jsonl"))],check=True)\nprint(json.loads((RUN/"trained-predictions-geometry.json").read_text()))')
md('## FEM of the NEW adapter\n\nAudit all six illustrated held-out cases. Fixed synthetic E=210,000 MPa, nu=0.3, units mm/N/MPa and 1 N geometric end-band loads. The shaft fixture co-rotates. Invalid patches, unmeshable parts, unanchored components and unconverged responses fail verification. Similar compliance cannot override a wrong solid. Stress is diagnostic; no strength claim.')
code('subprocess.run([sys.executable,"-u",str(ROOT/"scripts/colab_verify_mechanical_examples.py"),"--root",str(ROOT),"--run",str(RUN)],check=True)')
md('## Save results\n\nThe ZIP contains model adapters, manifests, raw predictions, native geometry scores and FEM solver fields. Download before disconnecting; Colab storage is ephemeral. No Google Drive mount is required.')
code('import zipfile\nfrom google.colab import files\narchive=Path("/content/multisource-cad-colab-results.zip")\nwith zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:\n    for f in RUN.rglob("*"):\n        if f.is_file() and "checkpoints" not in f.parts: z.write(f,f.relative_to(RUN))\nprint("Completed artifact:",archive)\nfiles.download(str(archive))')
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(colab=dict(name='Mechanical_CAD_Multisource_FEM_Train.ipynb',provenance=[]),accelerator='GPU',kernelspec=dict(name='python3',display_name='Python 3'),language_info=dict(name='python')),cells=cells)
out=ROOT/'notebooks/Mechanical_CAD_Multisource_FEM_Train.ipynb';out.write_text(json.dumps(nb,indent=1)+'\n');(ROOT/'tmp/multisource-colab-source.tar.gz').write_bytes(payload);print(out,'bytes',out.stat().st_size)
