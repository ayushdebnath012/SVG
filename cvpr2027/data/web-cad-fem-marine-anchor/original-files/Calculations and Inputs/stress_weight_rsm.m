close all; clear; clc

T=importdata('compiled_doe_results.xlsx');

T=T.data;
M=T;
T=array2table(T);

% A = ["medium" "large";"small" "medium"; "large" "small"];
% valueset = ["small" "medium" "large"];
% 
% sizes = categorical(A,valueset,Ordinal=true)

%%


AA=T(:,1:7);
BB=T(:,8);
BB=table2array(BB);
valueset=[8 9 10]
BB = categorical(BB,valueset,Ordinal=true)
% BB=table2array(BB);
% BB=num2str(BB);
BB=table(BB);
CC=T(:,9:end);

T=[AA BB CC];


T.Properties.VariableNames("T1") = "top_thk_inch";
T.Properties.VariableNames("T2") = "skirt_thk_inch";
T.Properties.VariableNames("T3") = "dia_case_inch";
T.Properties.VariableNames("T4") = "length_skirt_inch";
T.Properties.VariableNames("T5") = "dia_anchor_inch";
T.Properties.VariableNames("T6") = "gusset_height_inch";
T.Properties.VariableNames("T7") = "gusset_thk_inch";
T.Properties.VariableNames("BB") = "number_anchors";
T.Properties.VariableNames("T9") = "slot_opening_percent";
T.Properties.VariableNames("T10") = "weight_lbm";
T.Properties.VariableNames("T11") = "peak_stress_psi";

Tweight=[T(:,1:9) T(:,10)];
Tstress=[T(:,1:9) T(:,11)];

mdl_weight=stepwiselm(Tweight,'quadratic');
mdl_stress=stepwiselm(Tstress,'quadratic');

plotSlice(mdl_weight)
plotSlice(mdl_stress)

for j=1:1:9
    Amin(j,1)=min(M(:,j));
    Amax(j,2)=max(M(:,j));
    Adel(j,3)=((max(M(:,j))+min(M(:,j)))/2)-min(M(:,j));
end
Amax=Amax(:,2);
Adel=Adel(:,3);
Adel=1*Adel;

start_stress=predict(mdl_stress,[0.5,0.5,144,111.5,110,8,0.75,9,.3])
start_weight=predict(mdl_weight,[0.5,0.5,144,111.5,110,8,0.75,9,.3])

min_weight=1e5;
max_stress=3e5;
cost_base=1e5;

% for a=Amin(1):Adel(1):Amax(1)
%     for b=Amin(2):Adel(2):Amax(2)
%         for c=Amin(3):Adel(3):Amax(3)
%             for d=Amin(4):Adel(4):Amax(4)
%                 for e=Amin(5):Adel(5):Amax(5)
%                     for f=Amin(6):Adel(6):Amax(6)
%                         for g=Amin(7):Adel(7):Amax(7)
%                             for h=8:1:10
%                                 for i=Amin(9):Adel(9):Amax(9)
%                                     pred_weight=predict(mdl_weight,[a,b,c,d,e,f,g,h,i]);
%                                     pred_stress=predict(mdl_stress,[a,b,c,d,e,f,g,h,i]);
%                                     cost=(pred_weight/start_weight)+(pred_stress/start_stress);
%                                     if pred_weight<=min_weight
%                                         best_weight=[a,b,c,d,e,f,g,h,i];
%                                         min_weight=pred_weight
%                                     end
%                                     if pred_stress<=max_stress
%                                         best_stress=[a,b,c,d,e,f,g,h,i];
%                                         max_stress=pred_stress
%                                     end
%                                     if cost<=cost_base
%                                         best_cost=[a,b,c,d,e,f,g,h,i];
%                                         cost_base=cost
%                                     end
%                                 end
%                             end
%                         end
%                     end
%                 end
%             end
%         end
%     end
% end
% % 




% plotSlice(mdl_weight)
% 
% % test=filz.number_anchors;
% 
% % test=num2str(test);
