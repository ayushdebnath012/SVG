close all; clear; clc

DOE=importdata('doe_test_out.txt');

j=1;
Mout=[];
for i=1:1:130
    k=i*10;
    M=DOE(j:k);
    j=k+1;
    Mout=[Mout; M'];
end

STR=importdata('stress_out.xlsx');

STR=STR.data;

M=[Mout(:,1:end) STR(:,2)];

filz=M(all(M,2),:);

filz=filz(:,2:end);

anchs=filz(:,8);
anchs=num2str(anchs);



filzA=array2table(filz(:,1:7));
filzB=table(anchs);
filzB.Properties.VariableNames("anchs") = "Var8"
filzC=array2table(filz(:,9:end));
filzC.Properties.VariableNames("Var1") = "Var9"
filzC.Properties.VariableNames("Var2") = "Var10"

filz=[filzA filzB filzC];


filz.Properties.VariableNames("Var1") = "top_thk_inch"
filz.Properties.VariableNames("Var2") = "skirt_thk_inch"
filz.Properties.VariableNames("Var3") = "dia_case_inch"
filz.Properties.VariableNames("Var4") = "length_skirt_inch"
filz.Properties.VariableNames("Var5") = "dia_anchor_inch"
filz.Properties.VariableNames("Var6") = "gusset_height_inch"
filz.Properties.VariableNames("Var7") = "gusset_thk_inch"
filz.Properties.VariableNames("Var8") = "number_anchors"
filz.Properties.VariableNames("Var9") = "slot_opening"
filz.Properties.VariableNames("Var10") = "peak_stress_psi"

mdl=stepwiselm(filz,'quadratic')

plotSlice(mdl)

% test=filz.number_anchors;

% test=num2str(test);
