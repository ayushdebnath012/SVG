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
	
	int numDisp = displacements.size();
	
	for (int im = 0; im <= numFrames-1; im++) {
		
		
		std::ostringstream ss1;
		ss1 << argv[2] << "_Frame" << im << ".txt";
		filename = ss1.str();
		ofile1.open(filename.c_str());
		
		odb_Frame& lastFrame = allFramesInStep[im]; 

		const odb_SequenceFieldValue& coor = lastFrame.fieldOutputs()["COORD"].values();

		const odb_SequenceFieldValue& displacements = lastFrame.fieldOutputs()["U"].values();
		
		const odb_SequenceFieldValue& reactionForce = lastFrame.fieldOutputs()["RF"].values();
		
		const odb_SequenceFieldValue& reactionMoment = lastFrame.fieldOutputs()["RM"].values();

//		const odb_SequenceFieldValue& rotations = lastFrame.fieldOutputs()["UR"].values();

		int numDisp = displacements.size();
//		int numRot = rotations.size();	
		int numCoor = coor.size();
		int numRF = reactionForce.size();
		int numRM = reactionMoment.size();
		
		int numComp1 = 0;
//		int numComp2 = 0;
		int numComp3 = 0;
		int numComp4 = 0;
		int numComp5 = 0;

		cout << "===========" << endl;
		cout << "Current Frame " << im << endl;

		for (int i = 0; i < numCoor; i++) {
			const odb_FieldValue val1 = displacements[i];
//			const odb_FieldValue val2 = rotations[i];
			const odb_FieldValue val3 = coor[i];
			const odb_FieldValue val4 = reactionForce[i];
			const odb_FieldValue val5 = reactionMoment[i];
			
			const float* const data1 = val1.data(numComp1);
//			const float* const data2 = val2.data(numComp2);
			const float* const data3 = val3.data(numComp3);
			const float* const data4 = val4.data(numComp4);
			const float* const data5 = val5.data(numComp5);

			ofile1 << setw(10) << val3.nodeLabel() << "  ";
			
			for (int j = 0; j < numComp3; j++) {
				ofile1 << scientific << setprecision(6) << data3[j] << "  ";
			}
			for (int j = 0; j < numComp1; j++) {
				ofile1 << scientific << setprecision(6) << data1[j] << "  ";
			}
			for (int j = 0; j < numComp4; j++) {
				ofile1 << scientific << setprecision(6) << data4[j] << "  ";
			}
			for (int j = 0; j < numComp5; j++) {
				ofile1 << scientific << setprecision(6) << data5[j] << "  ";
			}

//			for (int j = 0; j < numComp2; j++) {
//				ofile1 << scientific  << setprecision(6) << data2[j] << "  ";
//			}

			ofile1 << endl;
		}
		
		cout << "Frame " << im << " Completed" << endl;
		cout << "===========" << endl;
		
		ofile1.close();
				
//		ofile1.close();

	}
	
	ofile1.close();

	odb.close(); 
	
	return 0;
}
