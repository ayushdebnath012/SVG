#include <iostream>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <ctime>
#include <string>
#include <sstream>

#include <odb_API.h>

using namespace std;

int number_inside(char *ip, char ctest){
 for(int p = 1;p < strlen(ip);p++){
  if(ip[p] == ctest){return 1;} 
 }
 return 0;
}

int ABQmain(int argc, char **argv)
{	

	clock_t time_start, time_end;

	ofstream ofile1;
	ofstream ofile4;	
        
	string filename;

	odb_String odbName(argv[1]);	

	// Insert user code below 
	odb_Odb& odb = openOdb(odbName);
	
	odb_Step& step = odb.steps()["Step-1"]; 
	odb_SequenceFrame& allFramesInStep = step.frames(); 
	int numFrames = allFramesInStep.size();
	
	odb_Frame& lastFrame = allFramesInStep[0]; 
	
	odb_FieldOutputRepository& fieldOutputRep = lastFrame.fieldOutputs();
	odb_FieldOutputRepositoryIT fieldIter( fieldOutputRep );

	const odb_SequenceFieldValue& displacements = lastFrame.fieldOutputs()["U"].values();
	const odb_SequenceFieldValue& rotations = lastFrame.fieldOutputs()["UR"].values();
	const odb_SequenceFieldValue& stress = lastFrame.fieldOutputs()["S"].values();
	const odb_SequenceFieldValue& misesStress = lastFrame.fieldOutputs()["MISESMAX"].values();
	const odb_SequenceFieldValue& strain = lastFrame.fieldOutputs()["LE"].values();
	const odb_SequenceFieldValue& sdv1 = lastFrame.fieldOutputs()["SDV1"].values();
	const odb_SequenceFieldValue& sdv2 = lastFrame.fieldOutputs()["SDV2"].values();

	int numDisp = displacements.size();
	int numRot = rotations.size();
	int numS = stress.size();
	int numMises = misesStress.size();
	int numE = strain.size();
	int numSDV1 = sdv1.size();
	int numSDV2 = sdv2.size();
	
	for (int im = 0; im <= numFrames-1; im++) {
		
		std::ostringstream ss1;
		ss1 << argv[2] << "_Frame" << im << ".txt";
		filename = ss1.str();
		ofile1.open(filename.c_str());
		
		odb_Frame& lastFrame = allFramesInStep[im]; 

		const odb_SequenceFieldValue& stress = lastFrame.fieldOutputs()["S"].values();
		const odb_SequenceFieldValue& strain = lastFrame.fieldOutputs()["LE"].values();
		const odb_SequenceFieldValue& misesStress = lastFrame.fieldOutputs()["MISESMAX"].values();

		int numS = stress.size();
		int numE = strain.size();
		int numMises = misesStress.size();

		int numCompS = 0;
		int numCompE = 0;
		int numSDV1  = 0;
		int numSDV2  = 0;
		int numCompMises = 0;

		int numDisp = displacements.size();
		int numRot = rotations.size();	
		
		cout << "===========" << endl;
		cout << "Current Frame " << im << endl;
		
		for (int i = 0; i < numS; i++) {

			const odb_FieldValue val01 = stress[i];
			const odb_FieldValue val02 = strain[i];
			
			const float* const data01 = val01.data(numCompS);
			const float* const data02 = val02.data(numCompE);
			
			ofile1 << setw(10) << " Stress " << val01.elementLabel() << "  " << val01.integrationPoint() << "  " << numCompS << "  ";
			
			for (int j = 0; j < numCompS; j++) {
				ofile1 << scientific << setprecision(6) << data01[j] << "  ";
			}
			ofile1 << scientific << setprecision(6)  << val01.maxInPlanePrincipal() << "  " << val01.minInPlanePrincipal() << "  " << val01.mises();
			
			ofile1 << endl;
			
			ofile1 << setw(10) << " Strain " <<val02.elementLabel() << "  " << val02.integrationPoint() << "  " << numCompE << "  ";
			
			for (int j = 0; j < numCompE; j++) {
				ofile1 << scientific << setprecision(6) << data02[j] << "  ";
			}
			
			ofile1 << scientific << setprecision(6)  << val02.maxInPlanePrincipal() << "  " << val02.minInPlanePrincipal() << "  ";
			
			ofile1 << endl;
			
		}
		
		cout << "Frame " << im << " Completed" << endl;
		cout << "===========" << endl;
		
		ofile1.close();
		
	}
	
	ofile1.close();

	odb.close(); 
	
	return 0;
}
