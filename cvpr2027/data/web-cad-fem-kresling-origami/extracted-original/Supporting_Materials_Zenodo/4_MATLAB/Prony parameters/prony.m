% function P = prony(x,y,time)
function P = prony(x,time)
% % N=3
% p1 = x(1);
% p2 = x(2);
% p3 = x(3);
% tau1 = x(4);
% tau2 = x(5);
% tau3 = x(6);
% P = 1-(p1.*(1-exp(-time./tau1))+p2.*(1-exp(-time./tau2))+p3.*(1-exp(-time./tau3)));


%% N=4
p1 = x(1);
p2 = x(2);
p3 = x(3);
p4 = x(4);
tau1 = x(5);
tau2 = x(6);
tau3 = x(7);
tau4 = x(8);
P = 1-(p1.*(1-exp(-time./tau1))+p2.*(1-exp(-time./tau2))+p3.*(1-exp(-time./tau3))+p4.*(1-exp(-time./tau4)));

%% N=5
% p1 = x(1);
% p2 = x(2);
% p3 = x(3);
% p4 = x(4);
% p5 = x(5);
% tau1 = x(6);
% tau2 = x(7);
% tau3 = x(8);
% tau4 = x(9);
% tau5 = x(10);
% P = 1-(p1.*(1-exp(-time./tau1))+p2.*(1-exp(-time./tau2))+p3.*(1-exp(-time./tau3))+p4.*(1-exp(-time./tau4))+p5.*(1-exp(-time./tau5)));

% N=3;
% 
%     for i=1:N
%     p(i)=x(i);
%     tau(i)=x(i);
%     P(i) = 1-p(i).*(1-exp(-time(i)./tau(i)));
%     end
end