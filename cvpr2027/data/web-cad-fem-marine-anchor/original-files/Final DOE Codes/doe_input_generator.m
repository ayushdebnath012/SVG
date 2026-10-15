close all; 
clear all; 
clc


inputs=[0.5 1.25;...
        0.5 1.25;...
        120 200;...
        100 200;...
        80 100;...
        8 16;...
        0.5 1.25;...
        8 10;...
        7 9]

design=bbdesign(length(inputs));

[m n]=size(design)

outputs=[];
for j=1:1:m
    for i=1:1:n
        k=design(j,i);
        if k == -1
            outputs(j,i)=min(inputs(i,:));
        elseif k == 1
            outputs(j,i)=max(inputs(i,:));
        else
            outputs(j,i)=mean(inputs(i,:));
        end
    end
end

cc=1:1:length(outputs);
outputs=[cc' outputs];


output2=[];
for k=1:1:max(cc)
     output2=[output2, outputs(k,:)];
end

output2=output2';

% %  fid = fopen('doe_test_out.txt','at')
% 
% durr=[];
% for i=1:1:m
%     a=outputs(i,:);
%     doe_pick=[sprintf('%d,', a(1:end-1)), sprintf('%d', a(end))];
%     durr = strvcat(durr,doe_pick);
% %     fprintf(fid, '%d %d %d\n', doe_pick);
% end
% 
% durr
output2=array2table(output2);
writetable(output2,'doe_test_out.txt');
% 
% 
