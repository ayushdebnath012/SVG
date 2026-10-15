"""Read-only audit of native CAD, embedded Elmer fields and saved ANSYS results."""
from pathlib import Path
import json,hashlib,zipfile,re,xml.etree.ElementTree as E
import numpy as np,cadquery as cq,pyvista as pv
from ansys.mapdl import reader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-native-fields-search');names=['web-cad-fem-elmer-cooling','web-cad-fem-wheel-rim-fields','web-cad-fem-testbench-fields'];A,W,B=[D/n for n in names];verified=0;archives=[]
for R in [A,W,B]:
 for row in json.loads((R/'download-manifest.json').read_text())['files']:
  b=(R/row['path']).read_bytes();assert len(b)==row['bytes'];assert hashlib.sha256(b).hexdigest()==row['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha1'];verified+=1
 for f in R.glob('*.FCStd'):
  out=R/'extracted-original'/f.stem
  with zipfile.ZipFile(f) as z:
   assert z.testzip() is None
   for i in z.infolist():
    if not i.is_dir():assert (out/i.filename).read_bytes()==z.read(i)
   archives.append({'file':str(f),'members':len(z.infolist()),'CRC_and_extracted_bytes_verified':True})
def render(solids,path,transparent_last=False):
 fig=plt.figure(figsize=(7,3.7));ax=fig.add_axes([0,0,1,1],projection='3d');allv=[]
 for i,s in enumerate(solids):
  v,tr=s.tessellate(.2);v=np.array([[x.x,x.y,x.z] for x in v]);allv.append(v);alpha=.12 if transparent_last and i==len(solids)-1 else 1
  colors=['#b8c9d5','#72b2c5','#d1ab72','#4c6374'];color=('#cbd0d5' if i==2 else '#344553' if i in [7,12,17,22] else '#bc9965') if len(solids)==23 else colors[i%len(colors)];ax.add_collection3d(Poly3DCollection(v[np.array(tr)],facecolors=color,edgecolors='#536473',linewidths=.10,alpha=alpha))
 v=np.concatenate(allv);ax.auto_scale_xyz(*v.T);ax.set_box_aspect(np.maximum(np.ptp(v,axis=0),1),zoom=1.2);ax.view_init(23,-145 if len(solids)==23 else -55);ax.set_axis_off();fig.savefig(path,dpi=190);plt.close(fig)
recs=json.loads((A/'native-CAD-and-field-inspection.json').read_text());boundary=[]
for rec in recs:
 root=A/'extracted-original'/rec['model'];x=E.parse(root/'Document.xml').getroot();s=cq.importers.importBrep(str(root/rec['original_BREP_member'])).val();assert s.isValid();g=pv.read(root/'Data.vtu');z=np.load(A/rec['field_npz']);assert np.array_equal(g.points,z['source_xyz']);assert np.array_equal(g.cells,z['source_cells']);assert np.array_equal(g.celltypes,z['source_cell_types'])
 for k in g.point_data:assert np.array_equal(g.point_data[k],z[k]);assert np.isfinite(z[k]).all()
 if 'radiator' in rec['model']:render(s.Solids()[:-1],T/'elmer-original-radiator-CAD-view.png')
 else:render(s.Solids(),T/'elmer-original-tube-CAD-view.png',True)
 bcs=[];materials=[]
 for o in x.findall('./ObjectData/Object'):
  p={q.attrib['name']:q for q in o.findall('./Properties/Property')};name=o.attrib['name']
  if name.startswith('Material'):
   materials.append({'object':name,'source_card':{it.attrib['key']:it.attrib['value'] for it in p['Material'].findall('./Map/Item')},'source_refs':[it.attrib for it in p['References'].findall('./LinkSubList/Link')]})
  if name.startswith('Constraint'):
   vals={k:[c.attrib for c in q] for k,q in p.items() if k in ['Temperature','initialTemperature','Pressure','DFlux','FilmCoef','AmbientTemp','VelocityX','VelocityY','VelocityZ','ConstraintType']};b={'object':name,'original_properties':vals,'source_refs':[it.attrib for it in p['References'].findall('./LinkSubList/Link')] if 'References' in p else[]}
   if name.startswith('ConstraintHeatflux') and vals['ConstraintType'][0]['value']=='0':
    area=sum(s.Faces()[int(a['sub'][4:])-1].Area() for a in b['source_refs']);flux=float(vals['DFlux'][0]['value']);b.update(cached_face_area_mm2=area,derived_power_W_if_DFlux_SI=flux*area*1e-6)
   bcs.append(b)
  if name=='SolverElmerOutput':assert (root/'original-Elmer-solver-output.txt').read_text()==p['Text'].find('String').attrib['value']
 boundary.append({'model':rec['model'],'materials':materials,'source_boundary_conditions':bcs})
 # Display a native-field section, not a new simulation or a reconstructed geometry.
 xyz=z['source_xyz'];temp=z['temperature'];cut=np.abs(xyz[:,0]-np.median(xyz[:,0]))<1.5 if 'radiator' in rec['model'] else np.abs(xyz[:,1])<1.5
 fig,ax=plt.subplots(figsize=(7,3.7));coords=(xyz[:,2],xyz[:,1]) if 'radiator' in rec['model'] else (xyz[:,0],xyz[:,2]);sc=ax.scatter(coords[0][cut],coords[1][cut],c=temp[cut],s=2,cmap='turbo',vmin=float(temp.min()),vmax=float(temp.max()));ax.set_aspect('equal');ax.set_xlabel('Original coordinate [mm]');ax.set_ylabel('Original coordinate [mm]');fig.colorbar(sc,ax=ax,label='Stored temperature [K]');fig.tight_layout();fig.savefig(T/(rec['model']+'-original-temperature-section.png'),dpi=180);plt.close(fig)
(A/'original-boundary-and-material-inspection.json').write_text(json.dumps(boundary,indent=2)+'\n')
# Frequencies copied exactly; static translations are rejected, not exported as numerical targets.
wheel=json.loads((W/'read-only-field-inventory.json').read_text());hashes=[]
for rec in wheel:
 f=W/rec['raw_RST'];hh=hashlib.sha256(f.read_bytes()).hexdigest();hashes.append(hh);rr=reader.read_binary(str(f),read_mesh=rec['sets']==1);assert np.array_equal(rr.time_values,rec['labels'])
 if rec['sets']==1:
  z=np.load(W/'extracted-original-fields'/(rec['SYS']+'-static-source-arrays.npz'));assert 'source_U' not in z;nn,ss=rr.nodal_stress(0);assert np.array_equal(nn,z['source_node_ids']);assert np.array_equal(ss,z['source_averaged_stress'],equal_nan=True);assert np.array_equal(np.isfinite(ss).all(axis=1),z['finite_stress_mask'])
assert len(set(hashes))==5
# Static source images establish references; no legacy displacement array is accepted.
origframe=D/'web-cad-fem-assemblies/test-bench-frame/Test Frame.FCStd';assert origframe.read_bytes()==(B/'Test Frame.FCStd').read_bytes()
strip=[]
for f in sorted((B/'CCX Files/test_runs').rglob('*.frd')):
 lines=f.read_text().splitlines();coords=[];disp=[];mode='';lab=None
 for l in lines:
  if l.startswith('    2C'):mode='xyz'
  elif l.startswith('    3C'):mode=''
  elif l.startswith(' -4  DISP'):mode='U'
  elif l.startswith(' -3'):mode=''
  elif l.startswith('  100CL'):lab=float(l[12:24])
  elif l.startswith(' -1') and mode in ['xyz','U']:
   row=[int(l[3:13])]+[float(l[13+12*j:25+12*j]) for j in range(3)];(coords if mode=='xyz' else disp).append(row)
 a=np.array(coords);u=np.array(disp);assert len(a)==316 and np.array_equal(a[:,0],u[:,0]);assert np.isfinite(u).all();np.savez_compressed(B/(f.parent.name+'-original-strip-fields.npz'),source_node_ids=a[:,0].astype(int),source_xyz_mm=a[:,1:],source_U_mm=u[:,1:]);rf=re.findall(r'total force .*?set (\w+).*?\n\s*\n\s*([^\n]+)',f.with_suffix('.dat').read_text(),re.S);rf={k:[float(v) for v in row.split()] for k,row in rf};assert len(rf)==2;res=np.sum(list(rf.values()),axis=0)
 strip.append({'stage':f.parent.name,'load_label':lab,'nodes':316,'bounds_mm':[a[:,1:].min(0).tolist(),a[:,1:].max(0).tolist()],'reaction_totals_N':rf,'reaction_residual_N':res.tolist(),'max_total_U_mm':float(np.linalg.norm(u[:,1:],axis=1).max()),'source_FEM':'Sequential linear static restart with imposed displacement, not dynamic digital-twin history'})
(B/'unpaired-strip-field-inspection.json').write_text(json.dumps(strip,indent=2)+'\n')
def save(R,c):
 m=json.loads((R/'download-manifest.json').read_text());c.update(source=m['source'],source_revision=m['pinned_tree_revision'],source_downloads=len(m['files']),generated_CAD=0,new_solver_runs=0,model_calls=0,certified_cases=0);(R/'catalog.json').write_text(json.dumps(c,indent=2,allow_nan=False)+'\n')
save(A,{'collection':'NativeFreeCAD/Elmerconjugatecooling models with full original savedfields','geometry_families':2,'complex_radiator_assembly_families':1,'simple_thermalflow_control_families':1,'raw_field_candidates':2,'records':recs,'source_boundary_metadata':'original-boundary-and-material-inspection.json','units':'VTUcoordinatesmatchcachedCADmillimeters; ElmerfieldsSI:temperatureK,pressurePa,velocitym/s. Nativevelocity50mm/s=.05m/s. FreeCADElmerwriter scalescoordinates.001forSIand revertscoordinatesforoutput.','unit_source':'https://github.com/FreeCAD/FreeCAD/blob/0.21.1/src/Mod/Fem/femsolver/elmer/writer.py','original_dimensioned_drawing_verified':False,'license':'MITrepositorynotice retained. Original material cards retain author/CC-BY notices. Localresearchcollection.','limits':['TwoCADgeometries,not355facesor177kpointsastasks. Fullbridgehas23physicalsolidsplusoneairdomain; tubehassteelandwaterdomains.','Alltemperature/pressure/velocityarraysfinitebutundershoot: tube284.2676Kbelow300Kboundary; radiator285.9547Kbelow298.15Kambient. No clipping/correction;stabilization/convergence/material/bodymappingreviewrequired.','Maximumtube600Kisprescribed,notindependentprediction. Fluidpressurezerosatsolidpointsarenotfluidminimumpressure;VTUnoCellData/bodyIDs,domainmaskmappingpending.','RadiatorREADMEpowers3.04/1.91/4/0Wsum8.95W differfromnative3DFluxvalueson9mm2faces,derived3.4/4.7/2.2Wsum10.3W assumingElmerSIflux. Exactrevision/scopeheld.','Radiationomittedinpublishermodel;resultnotvalidatedexperimentaltemperature. Nativecommadecimalmaterialstringskeptunchanged.','StoredsolverlogsfinishALLDONEbutthatdoesnotestablishconvergence/meshindependence. No sourceProxyPythonobjectdeserializationorFreeCADrecomputeexecuted.','Temperaturesectionplotsinspectoriginalsavedfieldwiththinspatialselection;notnewsolveordimensioneddrawing.']})
save(W,{'collection':'Native wheelrim CAD with5savedstatic/modalANSYSsolutions','geometry_families':1,'raw_solution_candidates':5,'native_CAD':['Rim.SLDPRT','Rim.scdocx'],'native_CAD_independent_import':False,'original_native_thumbnail':'original-native-thumbnail.png','source_solver_version':'ANSYS2026R1','records':wheel,'source_static_plot_references':{'radial':{'force_Y_N':4000,'VM_MPa':20.9,'U_m':.00002616,'safety_factor':13.4},'bending':{'moment_components_Nm':[1525,1296,0],'VM_MPa':131.1,'U_m':.0002443,'safety_factor':2.1}},'source_material':{'E_Pa':71000000000,'density_kg_m3':2770,'poisson':.33,'source_yield_Pa':280000000},'tire_approximation':'Distributedmass10kgand4radialsprings50kN/meach,notfull3Dtirecontact','original_dimensioned_drawing_verified':False,'license':'No explicit data license located; localresearch only.','limits':['FiveanalysiscasesononeCADfamily:two statics,three modalBCvariants;36modesarenot36independentCADtasks.','Legacy2026R1staticUdecodingnonfiniteandvaluesaround1e308 rejected; noUarraysinNPZ. OriginalRSTandpublisherUfiguresremainunchanged.','DerivedaveragedVM20.905141/131.132528MPamatchroundedplots;9378finitestressnodes/49494missing each. Compatibleindependentrecoverypending;NaNmasksretained.','Sourceclaimed116074-nodeconvergedmeshforallcases conflictswithoriginal58870/58882/58872-nodecaseheaders;freefreealone116074.','Freefree6nearrigidmodeskeptincluding0..0.00251Hz;constrainedfrequencyshiftsmustuseactualHz,notreportclaimless.2Hzfor771.8to780.5Hz.','Reportformula4000*.30*1.1*1.5=1980Nmroundsto2000;originalcomponentcards1525/1296Nmretained ratherthanreplacingwithscalar.','Staticbendingisoneinstant,notcertifiedfatiguelifeorreproducedSAEJ328qualification. NativeSolidWorks/SpaceClaimimportandpressure/fixedfacecorrespondencepending.']})
save(B,{'collection':'Duplicate native testframe plus unmatched new striprestart outputs held','new_CAD_geometry_families':0,'new_paired_raw_result_candidates':0,'duplicate_native_CAD':'Test Frame.FCStd','duplicate_of':'cvpr2027/data/web-cad-fem-assemblies/test-bench-frame/Test Frame.FCStd','original_frame_nodes_already_collected':2356,'new_unpaired_strip_geometry_families':1,'unpaired_static_restart_stages':4,'records':strip,'source_material':'OriginalstripdeckStE500,E210000MPa,nu.3;coordinatesmm andforcesN','original_dimensioned_drawing_verified':False,'license':'No explicit data license located;localresearch only.','limits':['Nativeframebyte-identicaltopreviousdataset;doesnotaddnewCAD/FEMfamily.','FourFRDs316nodesbound600x50x10mmstrip,not2000x1500x100mmnativeframe;no matchingstripCADlocated.','FRDsrequestDISPonly,no stress;DATtotalsarereactionforces. ImposededgeUX/UZmaximaareinputs,notindependentpredictiontargets.','Foursequential*Staticrestartstages,notdynamicFEMdigitaltwintrajectory.','GlobalreactiontotalsbalanceinroundedsourceDAT;doesnotestablishCADmapping/convergence.','No missingstripCADcreated;stagesexcludedfrompaired/complexcounts.']})
leads={'heated_Inconel_duct':{'source':'https://github.com/Rohan-Aero/flow-behavior-thermal-effects-multiphysics','status':'ManyCSVexports/decks/reports but no uploadednativeCADorRST/RTH/d3plot; publisher excludesbinaryfilesandgrantsnoopensource licence. Notcounted.'},'hybrid_CubeSat':{'source':'https://github.com/VESTER-AG/HYBRID-CUBESAT-FEASIBILITY-PROJECT','status':'TensiletestXLSXandreports,but nativeCADabsent. ExperimentsnotFEM;notcounted.'},'robot_dog':{'source':'https://github.com/KillerKing2905/Quadrupedal-Robot-Dog-Design-Analysis-and-Simulation','status':'NativecomplexSolidWorksassemblybut noFEMoutputs;notcounted.'},'sector_gate':{'source':'https://github.com/fraisasghar/Design-Analysis-of-Static-Sector-Gate-Storm-Surge-Barrier','status':'Reports/MATLAB/testingvideo;nativeCADabsent,notcounted.'},'NIC_shroud':{'source':'https://github.com/okidoki888/freecad-fem-thermal-analysis','status':'Analyticaltablesandgeneration/solvercode,notuploadednativeCAD/fullfields; sourceprogramsnotrun.'},'other_portfolios':{'source':'https://github.com/Collin259/mechanical-engineering-portfolio','status':'FigureswithoutdownloadablenativeCAD;notcounted.'}}
(T/'crawl-leads-and-exclusions.json').write_text(json.dumps(leads,indent=2)+'\n');v={'original_downloads_verified':verified,'native_FCStd_archives':archives,'Elmer_raw_VTU_NPZ_exact_copies_verified':2,'wheel_distinct_RST_files':5,'wheel_static_invalid_U_arrays_excluded':2,'wheel_static_stress_repeat_copies_checked':2,'original_frame_byte_duplicate_verified':True,'unpaired_strip_FRD_stages':4,'source_programs_executed':0,'generated_CAD':0,'new_solver_runs':0,'model_calls':0,'certified_cases':0};(T/'source-verification.json').write_text(json.dumps(v,indent=2)+'\n')
p=D/'web-complex-fem/selected-dataset.json';j=json.loads(p.read_text());j['native_fields_cooling_wheel_web_extension']={'catalogs':[str(D/n/'catalog.json') for n in names],'pdf':'cvpr2027/output/pdf/web-cad-fem-native-fields.pdf','zip':'cvpr2027/output/datasets/web-cad-fem-native-fields.zip','new_source_repositories':2,'new_geometry_families':3,'complex_geometry_families':2,'simple_thermalflow_controls':1,'saved_analysis_candidates':7,'wheel_native_import_pending':True,'duplicate_testframe_new_family_count':0,'unpaired_strip_stages_held':4,'certified_cases':0,'count_policy':'Fivewheelvariantsonegeometry,twoElmergeometries;modalsets/nodes/restartstages/copiedframeare notnewCADfamilies.'};p.write_text(json.dumps(j,indent=2)+'\n');print(v,flush=True)
