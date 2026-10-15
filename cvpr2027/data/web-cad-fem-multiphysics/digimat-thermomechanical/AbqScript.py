########################################################
## Run without GUI with following command 
#     abaqus cae noGUI=AbaRun.py
#########################################################

## Default ABAQUS inputs
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
import re
import numpy as np
import shutil

## Model name - Example: Cure-profile '30C14hr_80C10hr'
case= '30C14hr_80C10hr'
NameCAE='Box3D_TE.cae'
NameModelin='Uncon'
NameModel=str(case)+'_'+NameModelin
resin = 'Hexion_RIMR_035c' # Enter resin material name here e.g. 'HEXCEL8552'
Matname = resin

## Set number of CPU's
Ncpus=1

## Import model from other cae-file
mdb.openAuxMdb(pathName=NameCAE)
mdb.copyAuxMdbModel(fromName=NameModelin, toName=NameModel)
mdb.closeAuxMdb()

## Modifications to the model

## Define Material Setup
mdb.models[NameModel].Material(name=Matname)
mdb.models[NameModel].materials[Matname].Density(table=((1150.0, ), ))
mdb.models[NameModel].materials[Matname].Depvar(n=47) # n is dependent on Digimat, for more info see the .aba file. 
mdb.models[NameModel].materials[Matname].UserMaterial(mechanicalConstants=(0.0,))
mdb.models[NameModel].sections['Section-1-SET-2'].setValues(material=Matname, 
    thickness=None)


### Load in Temperature Profile from file
filename = str(case)+'_Tcyc.txt'

    ## Define the temperature data as an array
T = np.loadtxt(filename, delimiter='\t')
    ## Create an tabular amplitude of the temperature profile. 
mdb.models[NameModel].TabularAmplitude(data = T, name='TCYCLE', smooth=SOLVER_DEFAULT, timeSpan=STEP)

### Create Temnperature fields
    ## Initial Temperature
mdb.models[NameModel].Temperature(createStepName='Initial', 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, distributionType=
    UNIFORM, magnitudes=(T[0,1], ), name='Initial', region=
    mdb.models[NameModel].rootAssembly.instances['BOX3D'].sets['BOX'])

    ## Temperature Profile
mdb.models[NameModel].Temperature(amplitude='TCYCLE', createStepName='Cure', 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, distributionType=
    UNIFORM, magnitudes=(1.0, ), name='Cure_profile', region=
    mdb.models[NameModel].rootAssembly.instances['BOX3D'].sets['BOX'])

### Edit Curing Step w. Temperature Cycle
mdb.models[NameModel].steps['Cure'].setValues(initialInc=60.0, maxInc=60.0, minInc=0.65, timePeriod=T[-1,0])
mdb.models[NameModel].steps['Cure'].setValues(maxNumInc=1000000)


### State Variable Inputting

    ## Function: Opens keyword editor and searches in all blocks for the sought blockprefix    
def GetBlockPosition(NameModel, blockPrefix):
    if blockPrefix == '':
        return len(mdb.models[NameModel].keywordBlock.sieBlocks)-1
    pos = 0
    for count, block in enumerate(mdb.models[NameModel].keywordBlock.sieBlocks):
        if block[0:len(blockPrefix)].lower()==blockPrefix.lower():
            return count
            break
            
mdb.models[NameModel].keywordBlock.synchVersions()
mdb.models[NameModel].keywordBlock.insert(GetBlockPosition(NameModel,'*Depvar\n     47,'),
'\n\t1,"001_Cure","Degree of Cure"\n\t2,"002_Tg","Glass transition temperature"\n\t3,"003_ETH11","Thermal strain 11"\n\t4,"004_ETH22","Thermal strain 22"\n\t5,"005_ETH33","Thermal strain 33"\n\t9,"009_ECS11","Chemical shrinkage 11"\n\t10,"010_ECS22","Chemical shrinkage 22"\n\t11,"011_ECS33","Chemical shrinkage 33"')

mdb.models[NameModel].keywordBlock.insert(GetBlockPosition(NameModel,'*Restart, write, frequency=0'),
    '\n** \n** FIELD OUTPUT: SDVs\n**\n*Output, field, frequency=1\n*Element Output,directions=YES\nSDV1,SDV2,SDV3,SDV4,SDV4,SDV5,SDV9,SDV10,SDV11')
mdb.models[NameModel].keywordBlock.insert(GetBlockPosition(NameModel,'*Restart, write, frequency=0'),
'\n** \n** FIELD OUTPUT: Global_Variables\n**\n*Output, field, frequency=1\n*Element Output,directions=YES\nE,EE,S,TEMP')
mdb.models[NameModel].keywordBlock.insert(GetBlockPosition(NameModel,'*Restart, write, frequency=0'),
'\n** \n** FIELD OUTPUT: End_State\n**\n*Output, field\n*node Output\nU,RF')

### Generate job
modelJob=mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
	explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
	memory=90, memoryUnits=PERCENTAGE, model=NameModel, modelPrint=OFF, 
	multiprocessingMode=MPI, name=NameModel, nodalOutputPrecision=SINGLE, 
	numCpus=Ncpus, numDomains=Ncpus, numGPUs=0, queue=None, scratch='',
    type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)

    ## The following lines submit the job, and wait for completion before continue  
modelJob.submit(consistencyChecking=OFF)
modelJob.waitForCompletion()

### Postprocessing ODB

f=open(case+'_FEA_data' + '.csv','w')
d = ',' # Specifies the delimiter i.e. '\t' = tab, '\n' = newline, ';' = semicolon, ',' = comma
f.write('Iterations' + d + 'Time' + d + 'Temperature' + d + 'Etot' + d + 'DoC' + d + 'Tg' + d + 'ETH11' +  d + 'ECH11' + '\n');
odbObj = session.openOdb(name=NameModel+'.odb', readOnly=False)
step1 = odbObj.steps['Cure']
session.viewports['Viewport: 1'].setValues(displayedObject=odbObj)
nIterations = len(step1.frames)
node = odbObj.rootAssembly.nodeSets['X1Y1']
for i in range(0,nIterations+1):
    t = step1.frames[i].frameValue
    T1 = step1.frames[i].fieldOutputs['TEMP'].getSubset(region=node, position = ELEMENT_NODAL).values[0].data
    E11 = step1.frames[i].fieldOutputs['E'].getSubset(region=node, position = ELEMENT_NODAL).values[0].data[0]
    X = step1.frames[i].fieldOutputs['SDV_001_Cure'].getSubset(region=node, position = ELEMENT_NODAL).values[0].data
    Tg = step1.frames[i].fieldOutputs['SDV_002_Tg'].getSubset(region=node, position = ELEMENT_NODAL).values[0].data
    ETH11 = step1.frames[i].fieldOutputs['SDV_003_ETH11'].getSubset(region=node, position = ELEMENT_NODAL).values[0].data
    ECH11 = step1.frames[i].fieldOutputs['SDV_009_ECS11'].getSubset(region=node, position = ELEMENT_NODAL).values[0].data
    f.write(str(i) + d + str(t) + d + str(T1) + d + str(E11) + d + str(X) + d + str(Tg) + d + str(ETH11) +  d + str(ECH11) + '\n');
f.close()
