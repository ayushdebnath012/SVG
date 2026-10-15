"""Read original CAD containers, published tables and saved results; never solve."""
from pathlib import Path
import json, re, hashlib, zipfile, csv, olefile
import numpy as np, pymupdf
from ansys.mapdl import reader

D=Path('cvpr2027/data'); T=Path('cvpr2027/tmp/cad-fem-machine-variety-search')
names=['web-cad-fem-portal-frame','web-cad-fem-bolted-truss','web-cad-fem-cubesat-frame']
verified=0
def save(R,c):
    m=json.loads((R/'download-manifest.json').read_text())
    c.update(source=m['source'],source_revision=m['pinned_tree_revision'],generated_cad=0,new_solver_runs=0,model_calls=0,certified_cases=0)
    (R/'catalog.json').write_text(json.dumps(c,indent=2,allow_nan=False)+'\n')
for name in names:
    R=D/name
    for x in json.loads((R/'download-manifest.json').read_text())['files']:
        b=(R/x['path']).read_bytes()
        assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['git_blob_sha1']
        verified+=1
    containers=[]
    for f in sorted(R.rglob('*')):
        if f.suffix.lower() not in ['.sldprt','.sldasm','.par','.asm']:continue
        rec=dict(path=str(f.relative_to(R)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),independent_geometry_import=False)
        if olefile.isOleFile(f):
            with olefile.OleFileIO(f) as z:
                ss=z.listdir();rec.update(container='OLE compound file',streams=len(ss),parasolid_streams=['/'.join(p) for p in ss if 'PARASOLID' in '/'.join(p).upper()])
        else:rec['container']='Opaque proprietary binary; source identifies SOLIDWORKS 2024. No geometry validation inferred from extension.'
        containers.append(rec)
    (R/'read-only-native-CAD-container-inspection.json').write_text(json.dumps(containers,indent=2)+'\n')

R=D/names[0]; reports=[]
values=[('steel-Static ASTM A36 It1.pdf',474.9,5.124,.001715,682917,374468,20168.1),('steel-Static ASTM A992 It2.pdf',474.9,5.124,.001715,682917,374468,20167.2),('steel-Static It3.pdf',463.5,13100000,.001526,682215,374164,20155.7),('steel-Static It4.pdf',353.2,5.077,.001113,699218,384721,20168.2),('steel-Static Final .pdf',317.4,5.117,.001157,705930,388199,20168.7)]
for name,vm,u,eps,nn,ne,ry in values:
    doc=pymupdf.open(R/'Report'/name);txt='\n'.join(p.get_text() for p in doc)
    (T/('portal--'+Path(name).stem+'.txt')).write_text(txt)
    stress_page=next(i+1 for i,p in enumerate(doc) if 'VON: von Mises Stress' in p.get_text())
    reports.append(dict(original_report='Report/'+name,stress_table_page=stress_page,peak_published_VM_MPa=vm,peak_published_U_mm=u,peak_published_equivalent_strain=eps,nodes=nn,elements=ne,published_reaction_Y_N=ry,status='Rejected failed disconnected-body study' if 'It3' in name else 'Published scalar candidate; exact native revision and load scope pending'))
(R/'published-static-reference-tables.json').write_text(json.dumps(reports,indent=2)+'\n')
save(R,dict(collection='Haunched steel portal frame: native CAD, fabrication drawings and published FEM reports',geometry_families=1,complex_FEM_family_candidate=True,native_CAD_files=4,dimensioned_source_PDFs=['Drawings/Steel 1.pdf','Drawings/hexagon nut .pdf','Drawings/hhb(grade a)_is.pdf'],BOM='Drawings/BOM.pdf',independent_native_import=False,raw_solved_field_files=0,static_reports=reports,source_buckling_multiplier=5.0498,buckling_source='Report/Buckling 1-Mode List-1.csv',final_material=dict(name='ASTM A992',E_Pa=2e11,nu=.26,rho_kg_m3=7850,yield_Pa=3.45e8),final_source_load='Normal force value 10000 N on 2 faces; gravity 9.81 m/s2; fixed 2 faces; global bonded interaction. Final report says no connector definitions, large displacement off.',license='No explicit repository license; original proprietary/confidential title-block notice retained; local research collection.',limits=['Steel drawing title block says INCHES; nut/bolt drawings say MILLIMETERS and reports use mm. No unit correction made. Drawing dated 28 November may precede 5 December final geometry.', 'README names Universal_Formats but tree has no STEP/IGES. Compatible native import, assembly references and exact final body revision pending.', 'Two loaded faces and reaction 20168.7 N require total-versus-per-face force scope reconciliation; do not assume README 10 kN is the total resultant.', 'Only source report tables/plots, not CWR/raw stress arrays. Five iterations are one family; failed It3 displacement 13.1 million mm cannot be a target.', 'README pre-tension claim is unsupported by final report: no connector definitions and one globally bonded component. Not a validated bolt/contact test.', 'It4 353.2 MPa, final 317.4 MPa and slide cover PASS 353 MPa belong to different iterations. No averaging or silent replacement.', 'Buckling export calls factor 5.0498 and load 50.5 kN; exact buckling load/base study not frozen. Hand calculations do not establish mesh convergence or certification.']))

R=D/names[1];f=R/'Abaqus simulation data/Abaqus_node_displacement_data.csv'
with f.open() as fp:
    rd=csv.reader(fp);header=next(rd);a=np.asarray([[float(v) for v in row] for row in rd])
assert a.shape==(9,19) and np.isfinite(a).all()
np.savez_compressed(R/'original-Abaqus-position-export.npz',source_header=np.asarray(header),source_mass_load_kg=a[:,0],source_node_XY_values=a[:,1:].reshape(9,9,2),source_node_labels=np.asarray(list('ABCDEFGHI')))
z=np.load(R/'original-Abaqus-position-export.npz');assert np.array_equal(z['source_node_XY_values'].reshape(9,18),a[:,1:])
save(R,dict(collection='Bolted plywood truss native Solid Edge assembly and existing Abaqus joint-position export',geometry_families=1,complex_CAD_family=True,complex_FEM_family_candidate=False,classification='Idealized 2D truss control linked to complex 3D assembled CAD; not a solved 3D contact assembly',native_CAD='3D_Model/INTRO TO ME/FINAL TRUSS ASSEMBLY.asm',native_part_files=17,original_CAE='Abaqus simulation data/final_intro_to_mae.cae',original_result_CSV=str(f.relative_to(R)),source_export_rows=9,source_joint_labels=list('ABCDEFGHI'),source_load_mass_kg=a[:,0].tolist(),source_XY_units='Not printed in original export or report; unresolved',source_XY_at_1kg=a[-1,1:].reshape(9,2).tolist(),source_solver_description='Abaqus T2D2 linear pinned-joint truss, E=6 GPa, density=600 kg/m3, fixed and rolling supports',raw_ODB_present=False,original_dimensioned_drawing=False,license='MIT; LICENSE retained',limits=['CSV stores deformed joint positions, not displacement vectors: B y remains 94.05 and I x is 293.598 at 1 kg. No zero-load row; no baseline generated from polynomial fits.', 'Nine load rows 0.15..1 kg conflict with report ten stages and stated lower force 0.981 N. 0.15 kg times 9.81 equals 1.4715 N; original contradictory statement retained.', 'No section area, exact loading joint, units or fixed/roller mapping verified. Native Solid Edge assembly/component import and CAD-to-CAE mapping pending.', 'Physical 3D eccentricity/bolted joints and failure above ~0.5 kg appear in experiments, whereas FEM is idealized planar T2D2. Experimental curves and polynomial coefficients are separate, not raw FEM stresses.', 'Original CAE preserved but not opened via executing Abaqus; ODB absent. Joint labels are publisher A-I, not known solver node IDs. Nine stages do not add nine CAD families.']))

R=D/names[2];archive=R/'Final_Solution.wbpz';members=[]
with zipfile.ZipFile(archive) as zz:
    assert zz.testzip() is None
    for i in zz.infolist():
        if i.is_dir():continue
        b=(R/'extracted-original'/i.filename).read_bytes();assert b==zz.read(i)
        members.append(dict(path=i.filename,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),CRC32=i.CRC))
(R/'original-archive-extraction-verification.json').write_text(json.dumps(members,indent=2)+'\n')
for sys in ['SYS-3','SYS-4']:
    f=R/'extracted-original/M5A-NV_files/dp0'/sys/'MECH/file.rst';r=reader.read_binary(str(f));us=[]
    for i in range(r.nsets):ids,u=r.nodal_solution(i);assert np.isfinite(u).all();us.append(u)
    np.savez_compressed(R/'read-only-fields'/(sys+'-all-original-normalized-modes.npz'),source_node_ids=ids,source_normalized_modes=np.asarray(us),source_set_values=r.time_values)
    z=np.load(R/'read-only-fields'/(sys+'-all-original-normalized-modes.npz'))
    for i in range(r.nsets):assert np.array_equal(z['source_normalized_modes'][i],r.nodal_solution(i)[1])
for f in R.glob('read-only-fields/*original-nodal-solution.npz'):
    sys=f.name.split('-original')[0];r=reader.read_binary(str(R/'extracted-original/M5A-NV_files/dp0'/sys/'MECH'/('file.rth' if sys=='SYS' else 'file.rst')));assert np.array_equal(np.load(f)['source_nodal_solution'],r.nodal_solution(0)[1])
save(R,dict(collection='Held CubeSat publisher/archive mismatch; unidentified thermal assembly saved fields',paired_CubeSat_family_count=0,complex_CubeSat_case_count=0,status='HELD: downloaded project does not match source CubeSat screenshots',native_CAD_in_archive='M5A-NV_files/dp0/SYS/DM/SYS.agdb',native_CAD_container='HDF5 with compressed native Parasolid transmit stream; read-only byte extraction retained. Independent BREP import not performed.',archive_member_files=len(members),distinct_parent_saved_analyses=4,worker_partition_RSTs_not_cases=2,source_units='MKS: m, Pa; temperature Celsius (TOFFST 273.15)',actual_source_setup='Thermal convection h=5 W/m2/K to 20 C, volumetric HGEN 240000 W/m3 on source _CM58; structural imported body temperature and TREF 22 C with fixed support; perturbation buckling and prestressed modal.',archive_result_inventory=json.loads((R/'saved-field-inspection.json').read_text()),license='MIT; LICENSE retained',limits=['Original screenshots show perforated CubeSat frame with directional y max 0.25521 mm and z max 0.1942 mm. Archived mesh is 170 x 70 x 100 mm, block-like assembly with silicon/copper/aluminum properties. No matching CubeSat CAD/result reference confirmed.', 'Archive CAD/result provenance is retained for investigation; wrong title cannot turn these arrays into CubeSat ground truth. No verified complex family increment.', 'Archived structural U norm max 0.0380408988 mm, averaged corner-node VM 149.622039 MPa; 2021 of 6871 stress rows finite, 4850 missing. Keep missing values masked.', 'SYS-3 set labels 1189.359672/1207.052483 are dimensionless linear buckling load multipliers, not Hertz. SYS-4 ten labels 1880.788..4335.842 are prestressed modal frequencies in Hertz; vectors have arbitrary modal scale.', 'No fatigue life reference or physical launch loading is established. Archive temperatures 38.827006..40.300339 C do not validate space thermal conditions.']))

leads=[dict(source='https://data.mendeley.com/datasets/vkhtwb774t/1',status='FEM force XLSX and figures available; original file list has no native CAD. Not admitted.'),dict(source='https://data.mendeley.com/datasets/k75hh792k9/1',status='Two STEP CAD proxies, two topology STL files and load figure only; no saved results. 22 MPa is prescribed load, not FEM score. Not admitted.'),dict(source='https://data.mendeley.com/datasets/6ympzc5rkt/1',status='Publisher offers STEP and K/M/mapping; matrices are operators, not solved response. Six multipart archive files about 1.1GB; not downloaded, no solved reference verified.'),dict(source='https://github.com/biofluids/scripts-and-drawings',status='Native CAD plus material routines only; no saved FEM result.'),dict(source='https://github.com/PacktPublishing/Practical-Finite-Element-Simulations-with-SOLIDWORKS-2022',status='Complex chapter CAD files but only two saved CWR for simple vase; chapter CAD alone not counted.'),dict(source='https://github.com/khameelbm/Exploring-Finite-Element-Simulations-with-SOLIDWORKS',status='Book source mirror; no extra family count.'),dict(source='https://github.com/careervrosterm/engineering-portfolio',status='Portfolio PDF only, no native CAD files.')]
(T/'crawl-leads-and-exclusions.json').write_text(json.dumps(leads,indent=2)+'\n')
v=dict(original_downloads_verified=verified,archive_members_byte_verified=len(members),paired_source_evidence_families=2,complex_FEM_family_candidates=1,idealized_truss_controls=1,CubeSat_mismatch_held=1,certified_cases=0,generated_cad=0,new_solver_runs=0)
(T/'source-verification.json').write_text(json.dumps(v,indent=2)+'\n')
p=D/'web-complex-fem/selected-dataset.json';m=json.loads(p.read_text());m['portal_truss_archive_mismatch_web_extension']=dict(catalogs=[str(D/n/'catalog.json') for n in names],pdf='cvpr2027/output/pdf/web-cad-fem-portal-truss.pdf',zip='cvpr2027/output/datasets/web-cad-fem-portal-truss.zip',**v,count_policy='Portal iterations/buckling one family. Truss nine load rows one idealized control. CubeSat archive mismatch adds zero verified CubeSat families. Source findings not certified benchmark items.');p.write_text(json.dumps(m,indent=2)+'\n')
print(v)
