clc
clear all

%Geometrical parameters
r=10;
n=6;%number of sides
nb=n;
nc=n;
ho=17.5; %initial height
hor=ho/r;

phi_o=pi*(30/180);%initial rotation angle between top and bottom polygons
phi_max=pi-(2*pi/n)-phi_o;%pi-(2*pi/n);
phi_disp=0.1;

% Stiffness
E=10;
A=1;
KS=E*A;%Stretching
KR=0.001;%Rotational
KR_KS=KR/KS;

%Folding lines in planar state- Undeformed
ao=2*r*sin(pi/n);%base length
bo=sqrt(4.*r^2.*(sin(phi_o./2)).^2+(ho).^2);
co=sqrt(4.*r.^2.*(sin((phi_o+(2*pi/n))/2)).^2+(ho).^2);%main diagonal
hmin=real(sqrt(co^2-4*r^2));

dao=atan((ho)/(2*r*sin(phi_o/2+pi/n)*sin(phi_o/2)));
dbo=pi-acos((ho^2*cos(phi_o+2*pi/n)-r^2*(cos(phi_o+pi/n)-cos(pi/n))^2)/(ho^2+r^2*(cos(phi_o+pi/n)-cos(pi/n))^2));
dco=pi-acos((ho^2*cos(phi_o)-r^2*(cos(phi_o+pi/n)-cos(pi/n))^2)/(ho^2+r^2*(cos(phi_o+pi/n)-cos(pi/n))^2));


uo=0;%initial axial displacement
incr=50;
u_max=ho-hmin;
u=linspace(uo,u_max,incr);%axial displacement considering that the tube is fold until hmin
%u=linspace(uo,ho,incr);%axial displacement considering that the tube is totally fold
h=ho-u;%Height deployment / final height

hl=length(h);
%h_r=h./r; 
u_ho=u./ho;
u_r=u./r;

%Rotation angle assessmet for Collapse and Deployed scenarios, with an imposed axial displacement and assuming constant edges length 
%Considering b0 constant
phi_s1=real(acos((-bo.^2+(h).^2+2*r^2)./(2*r^2)));
phi_s1_end=phi_s1(end);

phi_s1_D=rad2deg(phi_s1);

%Twist angle

%phi=linspace(phi_o,phi_s1_end,incr);%(-)start and moves counterclockwise to close
phi=linspace(phi_o,phi_s1_end,incr);
phi_D = rad2deg(phi);

figure(1)
subplot(1,4,1); %Showing a quad plot of the layers
plot(u_r,phi_s1_D,'k','LineWidth',1.15)%figure(7)
xlabel('u/R','fontweight','bold','FontSize',12)
ylabel('Rotation angle in degrees (\phi)','fontweight','bold','FontSize',12)
set(gca,'linewidth',0.85)
axis auto

subplot(1,4,2); %Showing a quad plot of the layers
plot(u_ho,phi_s1_D,'k','LineWidth',1.15)%figure(7)
xlabel('u/ho','fontweight','bold','FontSize',12)
ylabel('Rotation angle in degrees (\phi)','fontweight','bold','FontSize',12)
set(gca,'linewidth',0.85)
axis auto



%Deployment =>Vertical force applied upwards+clockwise torque
    KSB=KS./bo;%Stretching stiffness
    KSC=KS./co;
    KRA=KR.*ao;%Rotational stiffness
    KRB=KR.*bo;
    KRC=KR.*co;

for i=1:length(phi_s1)
    KSB(i)=KS./bo;%Stretching stiffness
    KSC(i)=KS./co;
    KRA(i)=KR.*ao;%Rotational stiffness
    KRB(i)=KR.*bo;
    KRC(i)=KR.*co;
        
    a(i)=ao;
    b(i)=sqrt(4.*r^2.*(sin(phi_s1(i)./2)).^2+(ho-u(i)).^2);
    c(i)=sqrt(4.*r^2.*(sin((phi_s1(i)+(2*pi/n))./2)).^2+(ho-u(i)).^2);

    da(i)=atan((ho-u(i))./(2.*r.*sin((phi_s1(i)./2)+pi/n).*sin((phi_s1(i)./2))));
    db(i)=pi-acos((((ho-u(i)).^2).*cos(phi_s1(i)+2*pi/n)-r.^2.*(cos(phi_s1(i)+pi/n)-cos(pi/n)).^2)./(((ho-u(i)).^2)+r.^2.*(cos(phi_s1(i)+pi/n)-cos(pi/n)).^2));
    dc(i)=pi-acos((((ho-u(i)).^2).*cos(phi_s1(i))-r.^2.*(cos(phi_s1(i)+pi/n)-cos(pi/n)).^2)./(((ho-u(i)).^2)+r.^2.*(cos(phi_s1(i)+pi/n)-cos(pi/n)).^2));

    Ubar=0.5.*nb.*KSB(i).*(b-bo).^2+0.5.*nc.*KSC(i).*(c-co).^2;
    Uspr=0.5.*n.*KRA.*(da-dao).^2+0.5.*nb.*KRB.*(db-dbo).^2+0.5.*nc.*KRC.*(dc-dco).^2;
    Ut=Ubar+Uspr;

    Ukr=Ut./(KS*r^2);
    Ukho=Ut./(KS*ho^2);

    %Derivative of Energy dU_du=0=F
    % dUb_du=... 
    % -(ho-u(i)).*((nb.*KSB(i).*(b-bo))./b)-(ho-u(i)).*((nc.*KSC(i).*(c-co))./c);
    % (nb.*KSB(i).*(b-bo)).*acos((r^2.*(cos(phi_s1(i) + pi/n) - cos(pi/n)).^2 - cos(phi_s1(i) + (2*pi)/n)*(ho - u(i))^2)/(r^2*(cos(phi_s1(i) + pi/n) - cos(pi/n))^2 + (ho - u(i))^2))...
    % +(nc.*KSC(i).*(c-co)).*acos((r^2.*(cos(phi_s1(i) + pi/n) - cos(pi/n)).^2 - cos(phi_s1(i)).*(ho - u(i))^2)/(r^2*(cos(phi_s1(i) + pi/n) - cos(pi/n)).^2 + (ho - u(i)).^2));
   
    % dUs_du=...
    % -((n.*KRA.*(da(i)-dao))./(2.*r.*((tan(da(i)).^2)+1).*sin((phi_s1(i)./2)+pi/n).*sin((phi_s1(i)./2))))...
    % -((2.*nb.*KRB.*(db(i)-dbo).*(ho-u(i)).*(cos(phi_s1(i)+(2*pi)/n)+1).*((r.^2).*(cos(phi_s1(i)+pi/n)-cos(pi/n)).^2))./(((1-(cos(pi-db(i))).^2).^(1/2)).*(((ho-u(i)).^2)+((r.^2).*(cos(phi_s1(i)+pi/n)-cos(pi/n)).^2)).^2))...
    % -((2.*nc.*KRC.*(dc(i)-dco).*(ho-u(i)).*(cos(phi_s1(i))+1).*((r.^2).*(cos(phi_s1(i)+pi/n)-cos(pi/n)).^2))./(((1-(cos(pi-dc(i))).^2).^(1/2)).*(((ho-u(i)).^2)+((r.^2).*(cos(phi_s1(i)+pi/n)-cos(pi/n)).^2)).^2));
    % 
    % dU_du=dUb_du+dUs_du;
    % 
    % dU_du_ho= -dU_du./(KS*ho);

    % 
    % % Example displacement (u) and energy (U)
    % u = linspace(0, 10, 100);       % Displacement
    % U = 0.5 * u.^2;                % Example energy: U = 0.5 * u^2

   


end
   

    minU=islocalmin(Ukr,'FlatSelection','last');%find minimums in the array
    minf=find(minU == 1);%find minimum position in the array U
    u_r_min= u_r(minf);%find minimum position in the array U
    
    maxU=max(Ukr); %max U energy value
    maxf=find(Ukr == maxU);%find maximum position in the array U
    u_r_max= u_r(maxf);%find maximum position in the array U
   
    
    minUho=islocalmin(Ukho,'FlatSelection','last');%find minimums in the array with normalization by ho
    minfho=find(minUho == 1);%find minimum position in the array U
    u_ho_min= u_ho(minfho);%find minimum position in the array U
    
    maxUho=max(Ukho); %max U energy value
    maxfho=find(Ukho == maxUho);%find maximum position in the array U
    u_ho_max= u_ho(maxfho);%find maximum position in the array U

    subplot(1,4,3);
    plot(u_r,Ukr,'b','LineWidth',1.15)
    xlabel('u/r','fontweight','bold','FontSize',12)
    ylabel('U/ KSr^2','fontweight','bold','FontSize',12)
    set(gca,'linewidth',0.85)
    axis auto
    hold on
    if Ukr(length(Ukr))>1e-2
        plot(u_r(length(u_r)),Ukr(length(Ukr)),'o')
     else
        plot(u_r(minf),Ukr(minf),'o')
    end
    plot(u_r(maxf),Ukr(maxf),'o')
    hold off

    subplot(1,4,4);
    plot(u_ho,Ukho,'b','LineWidth',1.15)
    xlabel('u/ho','fontweight','bold','FontSize',12)
    ylabel('U/ KS*ho^2','fontweight','bold','FontSize',12)
    set(gca,'linewidth',0.85)
    axis auto
    hold on
    if Ukho(length(Ukho))>1e-2
        plot(u_ho(length(u_ho)),Ukr(length(Ukho)),'o')
        else
        plot(u_ho(minfho),Ukho(minfho),'o')
    end
    plot(u_ho(maxfho),Ukho(maxfho),'o')


    % figure(3)
    % plot(u_ho,dU_du_ho,'b','LineWidth',1.15)
    % xlabel('u/ho','fontweight','bold','FontSize',12)
    % ylabel('F/ho','fontweight','bold','FontSize',12)
    % set(gca,'linewidth',0.85)
    % axis auto


    %% Force displacement plots u/R

% Compute differences for U and u
du = diff(u_r);               % Differences in displacement
dU = diff(Ukr);               % Differences in energy

% Compute force F(u) = -dU/du
F = -dU ./ du;                 % Element-wise division with negative sign

% Flip the force signs (negative forces become positive and vice versa)
F_flipped = -F;                % Flip the force signs
% Set the first force value to zero
F_flipped = [0; F_flipped(:)];    % Prepend zero to the force vector

% Adjust displacement vector for F
u_mid = u_r(1:end-1) + du/2;  % Midpoints for corresponding F values

% Adjust u_mid to match the length of F_flipped
u_mid = [u_r(1) u_mid];       % Add the first displacement value to u_mid


% Plot Energy vs Displacement
figure(2);
subplot(2,1,1);
plot(u_r, Ukr,'b','LineWidth',2); % Corrected to use u_ho and Ukho
xlabel('u/r','fontweight','bold','FontSize',12);
ylabel('U/ KS*r^2','fontweight','bold','FontSize',12);
hold on
    if Ukr(length(Ukr))>1e-2
        plot(u_r(length(u_r)),Ukr(length(Ukr)),'o')
        else
        plot(u_r(minf),Ukr(minf),'o')
    end
    plot(u_r(maxf),Ukr(maxf),'o')

% Plot Force vs Displacement
subplot(2,1,2);
plot(u_mid, F_flipped, 'b','LineWidth',2);  % Plotting midpoints against force
% Add a horizontal line at y = 0
yline(0, 'k', 'LineWidth', 1);  % 'k--' specifies a dashed black line
xlabel('u/r','fontweight','bold','FontSize',12);
ylabel('F','fontweight','bold','FontSize',12);
hold on
    if F_flipped(length(F))==0
        plot(u_r(length(u_r)),F_flipped(length(F)),'o')
        else
        plot(u_r(minf),F_flipped(minf),'o')
    end
    

    %% Force displacement plots u/ho

% Compute differences for U and u
du = diff(u_ho);               % Differences in displacement
dU = diff(Ukho);               % Differences in energy

% Compute force F(u) = -dU/du
Fho = -dU ./ du;                 % Element-wise division with negative sign

% Flip the force signs (negative forces become positive and vice versa)
F_flipped_ho = -Fho;                % Flip the force signs
% Set the first force value to zero
F_flipped_ho = [0; F_flipped_ho(:)];    % Prepend zero to the force vector

% Adjust displacement vector for F
u_mid = u_ho(1:end-1) + du/2;  % Midpoints for corresponding F values

% Adjust u_mid to match the length of F_flipped
u_mid = [u_ho(1) u_mid];       % Add the first displacement value to u_mid




% Plot Energy vs Displacement
figure(3);
subplot(2,1,1);
plot(u_ho, Ukho,'b','LineWidth',2); % Corrected to use u_ho and Ukho
xlabel('u/ho','fontweight','bold','FontSize',12);
ylabel('U/ KS*ho^2','fontweight','bold','FontSize',12);
hold on
    if Ukho(length(Ukho))>1e-2
        plot(u_ho(length(u_ho)),Ukr(length(Ukho)),'o')
        else
        plot(u_ho(minfho),Ukho(minfho),'o')
    end
    plot(u_ho(maxfho),Ukho(maxfho),'o')

% Plot Force vs Displacement
subplot(2,1,2);
plot(u_mid, F_flipped_ho, 'b','LineWidth',2);  % Plotting midpoints against force
% Add a horizontal line at y = 0
yline(0, 'k', 'LineWidth', 1);  % 'k--' specifies a dashed black line
xlabel('u/ho','fontweight','bold','FontSize',12);
ylabel('F','fontweight','bold','FontSize',12);
hold on
    if F_flipped(length(F))==0
        plot(u_ho(length(u_ho)),F_flipped_ho(length(F)),'o')
        else
        plot(u_ho(minfho),F_flipped_ho(minfho),'o')
    end





  
