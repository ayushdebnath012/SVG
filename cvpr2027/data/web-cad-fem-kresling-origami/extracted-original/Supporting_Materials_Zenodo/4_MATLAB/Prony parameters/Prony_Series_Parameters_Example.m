%% Prony series parameters calculation by Non-linear sum of squares fitting - Levenberg-Marquardt algorithm
% Calculation for Abaqus inputs for Viscoelastic models
clear all;
%addpath('../lib');
%% 1.-Load Experimental Data Time (s), Stress, Tensile, and Shear Modulus (MPa) 

data= readtable('Relaxation data summary.xlsx','Sheet','Overall','Range','A1:AC8119','VariableNamingRule','preserve');

%% EXAMPLE FOR AG30
time=data{1:7176,1};%Time in sec 
Et=data{1:7176,2};% Tensile Relaxation Modulus E(t)=Stress (t)/strain_o (MPa)
v=0.48;% Poisson ratio AG30=0.49;DM60=0.48;DM70=0.48; DM85=0.47; DM95=0.46
Gt=Et./(2.*(1+v));% Shear Relaxation Modulus G(t)=E (t)/strain_o (MPa)
Kt=Et./(3.*(1-2*v));% Bulk Relaxation Modulus E(t)=Stress (t)/strain_o
%(MPa)

%% 2.- Instantaneus Relaxation Modulus Eo, Go when t=0
Eo=Et(1);%Instantaneus Tensile Relaxation Modulus
Go=Gt(1);%Instantaneus Shear Relaxation Modulus
%Ko=Kt(1);
%% 3.- Normalized Modulus and Master Curves calculation
En=Et./Eo;% Normalized Tensile Relaxation Modulus
Gn=Gt./Go;% Normalized Shear Relaxation Modulus
%Kn=Kt./Ko;
% figure(1)
% sgtitle('Master Curves: Relaxation Modulus vs Time')
% sgt.FontSize = 14;
% subplot(1,2,1)
% plot(time,Et,'bo','MarkerSize',1)
% xlabel('Time (s)');
% ylabel('E(t) (MPa)');
% xlim([0 7000])
% ylim([0 10])
% subplot(1,2,2)
% plot(time,Gt,'bo','MarkerSize',1)
% xlabel('Time (s)');
% ylabel('G(t) (MPa)');
% xlim([0 7000])
% ylim([0 5])
% 
% figure(2)
% sgtitle('Master Curves: Normalized Relaxation Modulus vs Time')
% 
% subplot(1,2,1)
% plot(time,En,'bo','MarkerSize',1)
% xlabel('Time (s)');
% ylabel('E_n');
% xlim([0 8000])
% ylim([0 1])
% 
% subplot(1,2,2)
% plot(time,Gn,'ko','MarkerSize',1)
% xlabel('Time (s)');
% ylabel('G_n');
% 
% xlim([0 8000])
% ylim([0 1])
%% 4.-Prony expansion terms

% Fit the model using the starting points - acc to the N-Prony parameters to
% be estimated
%x0 = [0.01 0.01 0.01 1 1 1];%N=3
x0 = [0.01 0.01 0.01 0.01 1 1 1 1];%N=4
%x0 = [0.01 0.01 0.01 0.01 0.01 1 1 1 1 1];%N=5
options = optimoptions('lsqcurvefit','Algorithm','levenberg-marquardt');
lb = [];
ub = [];
%[x1,resnorm1,residual1,exitflag1,output1] = lsqcurvefit(@prony,x0,time,Gn,lb,ub);
[x,resnorm,residual,exitflag,output] = lsqcurvefit(@prony,x0,time,Gn,lb,ub,options);

%Prony parameters p_i and tau_i
P_p_i=x(1:ceil(length(x)/2));
P_tau_i=x(ceil(length(x)/2)+1:end);
% Goodness of Fit visualization by residual norm display
fprintf('The ''levenberg-marquardt'' algorithm has residual norm %f.\n',resnorm);
fprintf('The ''levenberg-marquardt'' algorithm took %d function evaluations.\n',output.funcCount)
fprintf('Exit flag %f.\n',exitflag);
%Gn fitted (calculated from the resulting Prony terms)
Gn_f=prony(x,time);
%% 5.-Fitting curves plot
gray= [0.7 0.7 0.7];
b1=[0 0.80 1];
b2= [0 0.50 1];
b3= [0 0 1];
figure(3)
plot(time,Gn,'o','Color',gray,'MarkerSize',3)
hold on
plot(time,prony(x,time),'r-','LineWidth',1)
%plot(time,prony(x,time),'Color',b1,'LineWidth',1)
legend('Exp.Data','Fitted Data')
title('Experimental Data and Fitted Curve')
xlabel('Time (s)');
ylabel('G_n');
xlim([0 7000])
ylim([0 1])

figure(4)
semilogx(time,Gn,'o','Color',gray,'MarkerSize',2)
hold on
semilogx(time,prony(x,time),'r-','LineWidth',1)
%semilogx(time,prony(x,time),'Color',b1,'LineWidth',1)
legend('Exp.Data','Fitted Data')
title('Experimental Data and Fitted Curve')
xlabel('Time (s)');
ylabel('G_n');
xlim([0 7000])
ylim([0 1])

% figure(5)
% semilogx(time,Gn,'s','MarkerEdgeColor','[1 0.5 0.5]','MarkerFaceColor','[1 1 1]','MarkerSize',6,"LineWidth",0.1)%AG30
% semilogx(time,Gn,'s','MarkerEdgeColor','[1 0.5 0.5]','MarkerFaceColor','[1 1 1]','MarkerSize',6,"LineWidth",0.1)%DM60
% semilogx(time,Gn,'s','MarkerEdgeColor','[1 0.5 0.5]','MarkerFaceColor','[1 1 1]','MarkerSize',6,"LineWidth",0.1)%DM70
% semilogx(time,Gn,'s','MarkerEdgeColor','[1 0.5 0.5]','MarkerFaceColor','[1 1 1]','MarkerSize',6,"LineWidth",0.1)%DM85
% semilogx(time,Gn,'s','MarkerEdgeColor','[1 0.5 0.5]','MarkerFaceColor','[1 1 1]','MarkerSize',6,"LineWidth",0.1)%DM95
% hold on
% semilogx(time,prony(x,time),'LineWidth',1.5)
% grid on
% ax=gca;
% ax.GridLineStyle = '--';
% ax.GridLineWidth = 1;
% %% settings
% opt = [];
% opt.XLabel = 't (s)'; % xlabel
% opt.YLabel = 'Gn (t) (-)'; %ylabel
% opt.XLim = [0, 7000];
% opt.YLim = [0, 1];
% opt.YTick = [0, 0.2, 0.4, 0.6, 0.8];
% opt.BoxDim = [5, 4]; %[width, height]
% opt.Colors = [ % each colors per each material
%     1,      0.5,     0.5;%AG30
%     1,      0.5,     0.5;%aG30
%     1,      0,       1;%DM60
%     1,      0,       1;%DM60
%     0.4940, 0.1840, 0.5560;%DM70
%     0.4940, 0.1840, 0.5560;%DM70
%     0.3010, 0.7450, 0.9330;%DM85
%     0.3010, 0.7450, 0.9330;%DM85
%     0, 0.4470, 0.7410;%DM95    
%     0, 0.4470, 0.7410;%DM95 
%     ];
% opt.Legend = {'AG30 exp', 'AG30 fit','DM60', 'DM70', 'DM85', 'DM95'}; % legends
% % create the plot
% setPlotProp(opt);


% Extra Plots: Adjusted and single master curves
% figure(5)
% plot(time,Et,'b-','MarkerSize',1.5)
% hold on
% title('Master Curves: Tensile Relaxation Modulus vs Time')
% xlabel('Time (s)');
% ylabel('E(t) (MPa)');
% xlim([0 7000])
% ylim([0 10])
% figure(6)
% plot(time,Gt,'b-','MarkerSize',1.5)
% hold on
% title('Master Curves: Shear Relaxation Modulus vs Time')
% xlabel('Time (s)');
% ylabel('G(t) (MPa)');
% xlim([0 7000])
% ylim([0 3])
% % 
% figure(7)
% semilogx(time,Gt,'b-','MarkerSize',1.5)
% hold on
% title('Master Curves: Shear Relaxation Modulus vs Time')
% xlabel('Time (s)');
% ylabel('G(t) (MPa)');
% xlim([0 7000])
% ylim([0 3])



