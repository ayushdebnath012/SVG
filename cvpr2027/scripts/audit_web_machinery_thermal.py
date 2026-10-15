"""Read-only audit of original web CAD and already-solved thermal fields."""
from pathlib import Path
import json, hashlib, zipfile, re
import numpy as np, cadquery as cq
from ansys.mapdl import reader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-machinery-contact-search')
names=['web-cad-fem-shock-absorber','web-cad-fem-screw-jack','web-cad-fem-industrial-thermal','web-cad-fem-piston-pin-assembly']
def save(R,c):
    m=json.loads((R/'download-manifest.json').read_text());c.update(source=m['source'],pinned_tree_revision=m['pinned_tree_revision'],generated_cad=0,new_solver_runs=0,model_calls=0,certified_cases=0)
    (R/'catalog.json').write_text(json.dumps(c,indent=2,allow_nan=False)+'\n')
verified=0
for name in names:
    R=D/name
    for row in json.loads((R/'download-manifest.json').read_text())['files']:
        b=(R/row['path']).read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha1'];verified+=1

R=D/names[0];f=next(R.rglob('*.stp'));s=cq.importers.importStep(str(f)).val();bb=s.BoundingBox();cad=dict(valid=s.isValid(),solids=len(s.Solids()),faces=len(s.Faces()),envelope_mm=[bb.xlen,bb.ylen,bb.zlen]);assert cad['valid'] and cad['solids']==12
v,tr=s.tessellate(.25);v=np.asarray([[p.x,p.y,p.z] for p in v]);fig=plt.figure(figsize=(6.8,4));ax=fig.add_axes([0,0,1,1],projection='3d');ax.add_collection3d(Poly3DCollection(v[np.asarray(tr)],facecolors='#b4c9d8',edgecolors='#465767',linewidths=.12));ax.auto_scale_xyz(*v.T);ax.set_box_aspect(np.maximum(np.ptp(v,axis=0),1),zoom=.84);ax.view_init(18,-55);ax.set_axis_off();fig.savefig(T/'shock-original-STEP-view.png',dpi=180);plt.close(fig)
save(R,dict(collection='Spring-type shock absorber: original CATIA assembly, valid STEP and static FEM plots',new_geometry_families=1,complex_geometry_family=True,CAD_inspection=cad,native_CATPart_definitions=13,native_CATProduct_files=2,neutral_CAD=str(f.relative_to(R)),original_stress_reference=dict(image='result references/stress.png',unit='MPa',minimum=.00072284,maximum=198.44),original_deformation_reference=dict(image='result references/deformation.png',unit='mm',minimum=0,maximum=8.0874),raw_solved_fields=0,dimensioned_drawing_verified=False,license='No explicit data license located; local research only.',limits=['STEP imports as a valid 12-solid, 207-face assembly. Original CATIA definitions and products retained; STEP-to-native configuration and final FEM mesh mapping are pending.', 'WBPJ is an index, not a solved archive: referenced SYS-6/SYS-10 SCDOC and MECHDB files are absent. Source read-me says project folder omitted due size.', 'Force/pressure, fixed-face scopes, exact materials, contact behavior and convergence are not numerically documented in retained files. Plot extrema alone cannot define a reproducible grading task.', 'README claims modal and PSD random-vibration work, but no frequencies, PSD inputs or numerical outputs are uploaded. Count only the displayed static stress/deformation candidate.', 'Time label 1 s is a static load-step label; it is not a damping or impact trajectory. Complex CAD does not establish simulated hydraulic damping.']))

R=D/names[1]
save(R,dict(collection='Mechanical screw jack: native SOLIDWORKS assembly and existing static FEM figures',new_geometry_families=1,complex_geometry_family=True,native_assembly='Screw Jack/CAD/Assem1.SLDASM',native_part_files=7,independent_native_import=False,source_reported_bodies=7,source_reported_envelope_mm=[242.32,365.11,262.46],source_reported_mass_kg=9.077,source_reported_nodes=58642,source_reported_elements=33631,source_load='README: ramped FY=+1000 N, eight bonded contact regions; exact fixed/load-face scopes not uploaded.',source_material=dict(name='Structural Steel',E_MPa=200000,nu=.3,density_kg_mm3=7.85e-6,yield_MPa=250),published_plot_references=dict(VM_max_MPa=5.5054,VM_min_MPa=1.9133e-14,U_max_mm=.0022549,U_min_mm=0,equivalent_elastic_strain_max=5.0912e-5),README_reference_values=dict(VM_max_MPa=5.5224,VM_min_MPa=9.7897e-15,U_max_mm=.0014249),raw_solved_fields=0,dimensioned_drawing_verified=False,license='No explicit data license located; local research only.',limits=['README extrema disagree with unchanged source stress/deformation images. Retain both; do not average them or silently replace a revision.', 'README says STEP, drawings and a complete report are included, but pinned tree has native SLDPRT/SLDASM, five FEM images and a bare WBPJ only. No neutral STEP, SLDDRW, PDF report, MECHDB or RST.', 'Compatible native import and assembly dependency/pose verification are pending. Seven part definitions and one assembly remain one geometry family.', 'Eight bonded regions describe an idealized static assembly, not frictional thread engagement, rotation, lifting cycles or buckling capacity.', 'Displayed safety factor is a capped Stress Tool display; do not turn a >10 or 15 display cap into an exact certified safety margin.']))

def read_deck_blocks(deck):
    ls=deck.splitlines();nodes={};solids={};surfs={};i=0
    while i<len(ls):
        line=ls[i].lower()
        if line.startswith('nblock,3'):
            assert ls[i+1].lower()=='(1i9,3e20.9e3)';i+=2
            while not ls[i].lstrip().startswith('-1'):
                p=ls[i].split();assert len(p)==4;nodes[int(p[0])]=[float(v) for v in p[1:]];i+=1
        elif line.startswith('eblock,19,solid'):
            i+=2
            while not ls[i].lstrip().startswith('-1'):
                rec=[int(v) for v in ls[i].split()];i+=1;n=rec[8]
                while len(rec)<11+n:rec.extend(int(v) for v in ls[i].split());i+=1
                assert len(rec)==11+n;solids.setdefault(rec[0],set()).update(rec[11:])
        elif line.startswith('eblock,10'):
            i+=2
            while not ls[i].lstrip().startswith('-1'):
                rec=[int(v) for v in ls[i].split()];surfs.setdefault(rec[1],set()).update(v for v in rec[5:] if v>0);i+=1
        i+=1
    return nodes,solids,surfs

R=D/names[2];out=R/'read-only-fields';out.mkdir(exist_ok=True);recs=[];members=[];scdocs=[]
archive=R/'SteadyStateThermalAnalysis/Steady_HeatTransfer.zip'
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for x in z.infolist():
        if x.is_dir():continue
        b=(R/'extracted-original'/x.filename).read_bytes();assert b==z.read(x);members.append(dict(path=x.filename,bytes=len(b),CRC32=x.CRC,sha256=hashlib.sha256(b).hexdigest()))
(R/'original-archive-extraction-verification.json').write_text(json.dumps(members,indent=2)+'\n')
for f in sorted(R.rglob('*.scdoc')):
    with zipfile.ZipFile(f) as z:
        assert z.testzip() is None;p=next(n for n in z.namelist() if 'thumbnail' in n.lower());(T/(f.stem+'-'+str(f.stat().st_size)+'-original-thumbnail.png')).write_bytes(z.read(p))
        scdocs.append(dict(path=str(f.relative_to(R)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),archive_CRC_passed=True,native_geometry_members=[n for n in z.namelist() if n.lower().endswith('.sab')],geometry_kernel='Native ACIS SAB cached solids; independent BREP import pending'))
(R/'native-SpaceClaim-container-inspection.json').write_text(json.dumps(scdocs,indent=2)+'\n')
for f in sorted(R.rglob('file.rth')):
    sys=f.parent.parent.name;r=reader.read_binary(str(f),read_mesh=False);assert r.nsets==1
    sh=r._result_solution_header(0);assert sh['numdof']==1 and sh['nfldof']==0
    raw=r.read_record(r._resultheader['rpointers'][0]+sh['ptrNSL']);assert not np.any(raw==2**100)
    ids,temp=r.nodal_solution(0,in_nodal_coord_sys=True);assert temp.shape==(len(ids),1) and np.isfinite(temp).all()
    assert np.array_equal(temp[:,0],raw[np.argsort(r._resultheader['neqv'])])
    deck=(f.parent/'ds.dat').read_text(errors='replace');nodes,solids,surfs=read_deck_blocks(deck);xyz=np.asarray([nodes[int(n)] for n in ids]);outside_type=6 if sys=='SYS' else 3;outside=np.asarray(sorted(surfs[outside_type]));mask=np.isin(ids,outside);assert int(mask.sum())==len(outside)
    native=R/'read-only-fields'/(sys+'-original-temperature-and-deck-coordinates.npz')
    np.savez_compressed(native,source_node_ids=ids,source_temperature_C=temp,source_NBLOCK_xyz_m=xyz,source_exterior_surface_node_ids=outside,source_exterior_surface_mask=mask)
    z=np.load(native);assert np.array_equal(z['source_temperature_C'],r.nodal_solution(0,in_nodal_coord_sys=True)[1]);assert np.array_equal(z['source_NBLOCK_xyz_m'],np.asarray([nodes[int(n)] for n in z['source_node_ids']]))
    rec=dict(system=sys,source_RTH=str(f.relative_to(R)),source_version=r._resultheader.get('verstring'),source_nodes=len(ids),source_elements=len(r._resultheader['eeqv']),saved_sets=1,static_set_label=r.time_values.tolist(),global_temperature_range_C=[float(temp.min()),float(temp.max())],coordinate_envelope_m=np.ptp(xyz,axis=0).tolist(),exterior_surface_node_count=len(outside),exterior_scope='Outer foam' if sys=='SYS' else 'Outer cast iron pipe',exterior_temperature_range_C=[float(temp[mask].min()),float(temp[mask].max())])
    if sys=='SYS':
        interface=np.asarray(sorted((surfs[3]|surfs[4])&solids[2]));imask=np.isin(ids,interface);assert int(imask.sum())==len(interface)
        rec.update(cast_iron_outer_node_count=len(interface),cast_iron_outer_temperature_range_C=[float(temp[imask].min()),float(temp[imask].max())],report_part='C')
        np.savez_compressed(out/'SYS-original-cast-iron-outer-interface.npz',source_node_ids=ids,source_temperature_C=temp,source_outer_cast_iron_node_ids=interface,source_outer_cast_iron_mask=imask)
    else:rec['report_part']='A' if sys=='SYS-1' else 'B'
    cards=[s for s in deck.splitlines() if re.match(r'^(?:/units|toffst|antype|sf,|sfe,|tref|tunif|bfe|MP,|d,|cmsel|CMBLOCK)',s,re.I)];(out/(sys+'-source-selected-cards.txt')).write_text('\n'.join(cards)+'\n');recs.append(rec)
    if sys=='SYS':
        fig=plt.figure(figsize=(7,4));ax=fig.add_axes([.01,.02,.79,.95],projection='3d');sel=np.arange(0,len(ids),6);sc=ax.scatter(*(xyz[sel]*1000).T,c=temp[sel,0],cmap='turbo',s=2,rasterized=True);ax.set_box_aspect(np.ptp(xyz,axis=0));ax.view_init(25,-55);ax.set_axis_off();fig.colorbar(sc,ax=ax,shrink=.75,label='Original nodal temperature [C]');fig.savefig(T/'pipe-C-original-temperature-points.png',dpi=180);plt.close(fig)
    target=128.3 if sys=='SYS' else (128.5 if sys=='SYS-1' else 130.8);peak=rec['cast_iron_outer_temperature_range_C'][1] if sys=='SYS' else rec['exterior_temperature_range_C'][1];assert round(peak,1)==target
(R/'saved-RTH-inspection.json').write_text(json.dumps(recs,indent=2)+'\n')
save(R,dict(collection='Curved steam pipe saved thermal fields and elbow thermal-shock report',new_geometry_families=2,complex_geometry_family=False,classification='Two thermal controls: S-shaped pipe and 90-degree elbow; insulation cases are variants, not families',raw_saved_RTH_candidates=3,saved_result_inventory=recs,published_steady_refs=[dict(part='A',cast_iron_outer_peak_C=128.5,heat_loss_magnitude_W=35.4),dict(part='B',cast_iron_outer_peak_C=130.8,heat_loss_magnitude_W=32.3),dict(part='C',cast_iron_outer_peak_C=128.3,heat_loss_magnitude_W=35.6)],published_elbow_insulation_sweep=dict(thickness_mm=[1.5,2.5,5,10,15,7.5,12.5,10.5],heat_loss_W=[39.835,39.921,40.07,40.147,39.997,40.143,40.096,40.141]),published_elbow_transient=dict(time_minutes=[10,167,90,91,92,95,94],maximum_outer_insulation_temperature_C=[29.62,113.53,106.93,107.15,107.39,108.01,107.79],source_steady_time_minutes=95,raw_transient_results_uploaded=False),source_problem_PDFs=['SteadyStateThermalAnalysis/ProblemStatement.pdf','TransientThermalAnalysis/ProblemStatement.pdf'],dimensioned_drawing_track_complete=False,license='No explicit repository license located; original author/course notices retained; local research only.',limits=['Original native SpaceClaim SAB geometries and matching project archives retained; independent ACIS BREP/body/face import remains pending.', 'Default legacy VTK mesh decoding exited 139. Safe read_mesh=False recovers finite scalar temperatures with exact node IDs; coordinates and scopes copied from original textual NBLOCK/EBLOCK decks. No reconstructed VTK mesh or solver run.', 'Raw-record scalar values and repeat original RTH reads match exactly. Outer surface maxima round to each source A/B/C reference; this verifies reference mapping, not mesh/physics certification.', 'Part C report asks outer cast iron temperature, not outer foam temperature. Native cast iron interface max 128.324369 C differs from foam max 118.774152 C; masks distinguish them.', 'Three steady variants are one pipe family. Heat-loss table magnitudes are published references; signed source reaction screenshots include negative outward values. Heat-flow arrays were not decoded.', 'Elbow report and CAD include temperature-dependent cast iron conductivity, thermal shock and insulation sweep, but no transient RTH/history archive was uploaded.', 'Elbow 95-minute criterion uses 0.95 times temperature in Celsius. Do not silently replace it with 95 percent of temperature rise or absolute Kelvin; exact task convention/time-step assessment remains pending.', 'Problem figures state diameters but do not provide complete manufacturing dimensions. Source statements and CAD views are not complete dimensioned drawing-to-CAD tasks.']))

R=D/names[3];old=D/'web-cad-fem-piston-drawing';a=json.loads((old/'download-manifest.json').read_text());b=json.loads((R/'download-manifest.json').read_text());hs={x['sha256']:x['path'] for x in a['files']};matches=[dict(path=x['path'],existing=hs[x['sha256']]) for x in b['files'] if x['sha256'] in hs];assert len(matches)==8
save(R,dict(collection='Duplicate piston-pin assembly; no new family or static case',duplicate_existing_collection=str(old),new_geometry_families=0,new_analysis_candidates=0,exact_original_file_matches=matches,new_original_files_only=['PISTON DEFORMATION ANIMATION.wmv','PISTON STRESS ANIMATION.wmv'],original_static_stress_peak_MPa=888.01,original_static_U_max_mm=.22122,status='Duplicate; source movies add no new numerical reference',limits=['All original CAD, WBPJ, README and three images match the previously collected piston-drawing source byte-for-byte.', 'Do not count native DWG or missing-SLDPRT assembly again. Existing 888.01 MPa source stress and 0.22122 mm deformation references remain unchanged.']))

leads=[dict(source='https://github.com/ansys/example-data',path='pyworkbench/cooled-turbine-blade/wbpz/cooled_turbine_blade.wbpz',status='Original archive CRC checked; native SCDOC and setup, no RST/RTH solved output. Not admitted.'),dict(source='https://github.com/BaumSebastian/DDACS',status='Deep drawing/cutting has large solved mesh/field dataset; native non-mesh CAD not verified. No local reconstruction or solve.'),dict(source='https://github.com/rakesh12shankar/canopy-cold-plate-cht',status='Native Parasolid CAD and Fluent finite-volume CHT metrics. Pure CFD/FVM source is not admitted to strict FEM track.'),dict(source='https://github.com/ravirajk7171-sudo/Engine-Blower-by-using-SolidWorks',status='Complex CAD and assembly drawing; no FEM results in tree. Not admitted.'),dict(source='https://github.com/mho20045-dot/spring-testing-machine-design-analysis',status='CAD screenshots/report only; no native CAD files. Not admitted.'),dict(source='https://github.com/JayParekh-MechAI/Gearbox-Stress-Analysis-Computer-Aided-Engineering',status='Reports only; no native CAD. Not admitted.'),dict(source='https://github.com/MahsaScript/Ansys_3D_Piston_Problem',status='LS-DYNA mesh/decks and animation, no native CAD. Not admitted.'),dict(source='https://github.com/ARAVINTHKRISHNA-design/Spring-Damping-Modal-Analysis-ANSYS',status='WBPJ, images/video, no native CAD verified. Not admitted.')]
(T/'crawl-leads-and-exclusions.json').write_text(json.dumps(leads,indent=2)+'\n')
v=dict(original_downloads_verified=verified,new_paired_repositories=3,new_geometry_families=4,new_complex_assembly_families=2,new_thermal_controls=2,original_archive_files_byte_verified=len(members),raw_RTH_candidates=3,duplicate_piston_new_family_count=0,certified_cases=0,generated_cad=0,new_solver_runs=0)
(T/'source-verification.json').write_text(json.dumps(v,indent=2)+'\n')
p=D/'web-complex-fem/selected-dataset.json';m=json.loads(p.read_text());m['machinery_thermal_web_extension']=dict(catalogs=[str(D/n/'catalog.json') for n in names],pdf='cvpr2027/output/pdf/web-cad-fem-machinery-thermal.pdf',zip='cvpr2027/output/datasets/web-cad-fem-machinery-thermal.zip',**v,count_policy='Shock and screw jack one family each; curved pipe and elbow two controls. Three insulation RTH variants one curved-pipe family. Existing piston duplicate adds zero. Nodes, animation frames, report time rows and assembly part files do not inflate item counts.');p.write_text(json.dumps(m,indent=2)+'\n');print(v,flush=True)
