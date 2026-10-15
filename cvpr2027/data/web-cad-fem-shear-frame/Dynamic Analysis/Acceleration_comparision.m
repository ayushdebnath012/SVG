clear all;
close all;
clc;
data = xlsread('Abaqus1.xlsx');
time=data(401:480,1);
Actual_acc=data(401:480,3);
Abaqus_acc=data(401:480,4);
 plot(time,Actual_acc,'r','LineWidth',2)
 hold on 
 plot(time,Abaqus_acc,'b','LineWidth',2)
 xlabel('Time (sec)')
 ylabel('Acceleration (g)')
 grid on 
 box on
 legend('Experimental','ABAQUS')
 saveas(gcf,'Acceleration_comparision.png')
 

