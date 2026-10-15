# -*- coding: mbcs -*-
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
import os, shutil
import numpy as np

#b = 20e-3
#alpha = np.pi/2
#r = b/alpha
#L = 200e-3


os.chdir('/homes/jac287/Desktop/working directory/tapered spring/results/')

pi = np.pi


bo = 20e-3

Ro = 1*bo  #outer radius
Ri = 0.7*Ro    #inner radius


L = 10*bo



alpha = bo/Ro    #angle subtended (this is constant along the tape spring)

bi = alpha*Ri


dH = Ri-Ro

t = 0.15e-3   #thickness
v = 0.34

total_rotation = 3*np.pi




overall_job_name = 'tapered_vary_b_t15'
model_name = 'Model-1'

mdb.models[model_name].ConstrainedSketch(name='__profile__', sheetSize=0.2)
mdb.models[model_name].sketches['__profile__'].sketchOptions.setValues(
    decimalPlaces=3)

mdb.models[model_name].sketches['__profile__'].ArcByCenterEnds(center=(0.0, dH), direction=CLOCKWISE, point1=(-Ro*np.sin(alpha/2), Ro*np.cos(alpha/2) + dH), point2=(Ro*np.sin(alpha/2),Ro*np.cos(alpha/2) + dH))
f = 1
mdb.models[model_name].sketches['__profile__'].ArcByCenterEnds(center=(0.0, 0.0 ), direction=CLOCKWISE, point1=(-Ri*np.sin(f*alpha/2), Ri*np.cos(f*alpha/2)), point2=(Ri*np.sin(f*alpha/2),Ri*np.cos(f*alpha/2)))
    
 
mdb.models[model_name].Part(dimensionality=THREE_D, name='Part-1', type=
    DEFORMABLE_BODY)
    
mdb.models[model_name].parts['Part-1'].BaseShellExtrude(depth=L, sketch=
    mdb.models[model_name].sketches['__profile__'])
del mdb.models[model_name].sketches['__profile__']


 
mdb.models[model_name].parts['Part-1'].ShellLoft(endCondition=NONE, 
    loftsections=((mdb.models[model_name].parts['Part-1'].edges[3], 
    mdb.models[model_name].parts['Part-1'].edges[4]), (
    mdb.models[model_name].parts['Part-1'].edges[7], 
    mdb.models[model_name].parts['Part-1'].edges[12])), startCondition=NONE)
    
  
mdb.models[model_name].parts['Part-1'].RemoveFaces(deleteCells=False, faceList=
    mdb.models[model_name].parts['Part-1'].faces.getSequenceFromMask(mask=(
    '[#30 ]', ), ))
mdb.models[model_name].parts['Part-1'].RemoveFaces(deleteCells=False, faceList=
    mdb.models[model_name].parts['Part-1'].faces.getSequenceFromMask(mask=(
    '[#8 ]', ), ))
mdb.models[model_name].parts['Part-1'].RemoveFaces(deleteCells=False, faceList=
    mdb.models[model_name].parts['Part-1'].faces.getSequenceFromMask(mask=(
    '[#4 ]', ), ))

   

mdb.models[model_name].Material(name='CuBe')
mdb.models[model_name].materials['CuBe'].Density(table=((7850.0, ), ))
mdb.models[model_name].materials['CuBe'].Elastic(table=((120000000000.0, v), 
    ))
mdb.models[model_name].HomogeneousShellSection(idealization=NO_IDEALIZATION, 
    integrationRule=SIMPSON, material='CuBe', name='tape spring section', 
    numIntPts=5, poissonDefinition=DEFAULT, preIntegrate=OFF, temperature=
    GRADIENT, thickness=t, thicknessField='', thicknessModulus=None, 
    thicknessType=UNIFORM, useDensity=OFF)
    
mdb.models[model_name].parts['Part-1'].Set(faces=
    mdb.models[model_name].parts['Part-1'].faces.getSequenceFromMask(('[#3 ]', 
    ), ), name='surface')
mdb.models[model_name].parts['Part-1'].SectionAssignment(offset=0.0, 
    offsetField='', offsetType=MIDDLE_SURFACE, region=
    mdb.models[model_name].parts['Part-1'].sets['surface'], sectionName=
    'tape spring section', thicknessAssignment=FROM_SECTION)
mdb.models[model_name].rootAssembly.DatumCsysByDefault(CARTESIAN)
mdb.models[model_name].rootAssembly.Instance(dependent=ON, name='Part-1-1', 
    part=mdb.models[model_name].parts['Part-1'])
    
mdb.models[model_name].parts['Part-1'].setElementType(elemTypes=(ElemType(
		elemCode=S4R, elemLibrary=STANDARD, secondOrderAccuracy=OFF, 
		hourglassControl=DEFAULT), ElemType(elemCode=S3, elemLibrary=STANDARD)), 
		regions=(mdb.models[model_name].parts['Part-1'].faces.getSequenceFromMask((
		'[#3 ]', ), ), ))

	
		    
#mdb.models[model_name].StaticStep(adaptiveDampingRatio=None, 
#		continueDampingFactors=False, name='Step-1', nlgeom=ON, previous='Initial', 
#		stabilizationMagnitude=1e-08, stabilizationMethod=DAMPING_FACTOR)
		
		
mdb.models[model_name].StaticStep(adaptiveDampingRatio=None, 
		continueDampingFactors=False, name='Step-1', nlgeom=ON, previous='Initial', 
		stabilizationMagnitude=0.05, stabilizationMethod=DISSIPATED_ENERGY_FRACTION)		
				
mdb.models[model_name].steps['Step-1'].setValues(timePeriod = 1,adaptiveDampingRatio=0.05, maxNumInc=20000, minInc=1e-30)
			
#mdb.models[model_name].StaticStep(adaptiveDampingRatio=None, 
#    continueDampingFactors=False, name='Step-1', nlgeom=ON, previous='Initial', 
#    stabilizationMagnitude=0.0002, stabilizationMethod=DAMPING_FACTOR, maxNumInc=20000, minInc=1e-30)			  #these are the default values, but does not converge!
			
			
#mdb.models[model_name].steps['Step-1'].setValues(timePeriod = 1,adaptiveDampingRatio=0.01, 
#	continueDampingFactors=False, maxNumInc=20000, minInc=1e-20, 
#	stabilizationMagnitude=0.1, stabilizationMethod=
#	DISSIPATED_ENERGY_FRACTION)


  
mdb.models[model_name].parts['Part-1'].RemoveFaces(deleteCells=False, faceList=
    mdb.models[model_name].parts['Part-1'].faces.getSequenceFromMask(mask=(
    '[#1 ]', ), ))
    
    
seed_size = bi/40
mdb.models[model_name].parts['Part-1'].seedPart(deviationFactor=0.1, 
	minSizeFactor=0.1, size=seed_size)
mdb.models[model_name].parts['Part-1'].generateMesh()	

mdb.models[model_name].rootAssembly.regenerate()

#reference point x = 0, y = to centroid, z = L
mdb.models[model_name].rootAssembly.ReferencePoint(point=(0.0, Ro*np.cos(alpha/4) + dH, L))
mdb.models[model_name].rootAssembly.Set(edges=
    mdb.models[model_name].rootAssembly.instances['Part-1-1'].edges.getSequenceFromMask(
    ('[#1 ]', ), ), name='t_Set-1')
mdb.models[model_name].RigidBody(name='Constraint-1', refPointAtCOM=ON, 
    refPointRegion=Region(referencePoints=(
    mdb.models[model_name].rootAssembly.referencePoints[4], )), tieRegion=
    mdb.models[model_name].rootAssembly.sets['t_Set-1'])
mdb.models[model_name].rootAssembly.Set(edges=
    mdb.models[model_name].rootAssembly.instances['Part-1-1'].edges.getSequenceFromMask(
    ('[#8 ]', ), ), name='Set-3')
mdb.models[model_name].XsymmBC(createStepName='Initial', localCsys=None, name=
    'long_edge_symmetry', region=
    mdb.models[model_name].rootAssembly.sets['Set-3'])
mdb.models[model_name].rootAssembly.Set(edges=
    mdb.models[model_name].rootAssembly.instances['Part-1-1'].edges.getSequenceFromMask(
    ('[#4 ]', ), ), name='Set-4')
mdb.models[model_name].ZsymmBC(createStepName='Initial', localCsys=None, name=
    'short_edge_symmetry', region=
    mdb.models[model_name].rootAssembly.sets['Set-4'])
mdb.models[model_name].rootAssembly.Set(name='Set-5', referencePoints=(
    mdb.models[model_name].rootAssembly.referencePoints[4], ))
    
mdb.models[model_name].DisplacementBC(amplitude=UNSET, createStepName='Step-1', 
    distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=None, name=
    'BC-1', region=mdb.models[model_name].rootAssembly.sets['Set-5'], u1=0.0, 
    u2=UNSET, u3=UNSET, ur1=total_rotation, ur2=0.0, ur3=0.0)


mdb.models[model_name].fieldOutputRequests['F-Output-1'].setValues(variables=(
	'S', 'LE', 'U', 'RM', 'COORD','SE'))

mdb.models[model_name].fieldOutputRequests['F-Output-1'].setValues(numIntervals=200)


job_1_name = overall_job_name +'_same'

mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
	explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
	memory=90, memoryUnits=PERCENTAGE, model=model_name, modelPrint=OFF, 
	multiprocessingMode=DEFAULT, name=job_1_name, nodalOutputPrecision=SINGLE, 
	numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', type=
	ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
job_1 = mdb.jobs[job_1_name]
job_1.submit(consistencyChecking=OFF)
#job_1.waitForCompletion()


		

mdb.models[model_name].boundaryConditions['BC-1'].setValues(ur1=-total_rotation)




job_2_name = overall_job_name +'_opp'

mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
	explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
	memory=90, memoryUnits=PERCENTAGE, model=model_name, modelPrint=OFF, 
	multiprocessingMode=DEFAULT, name=job_2_name, nodalOutputPrecision=SINGLE, 
	numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', type=
	ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
job_2 = mdb.jobs[job_2_name]
job_2.submit(consistencyChecking=OFF)
#job_2.waitForCompletion()










