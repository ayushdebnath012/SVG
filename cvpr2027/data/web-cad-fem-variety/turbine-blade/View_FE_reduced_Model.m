clear all
close all
clc

load('FE_Reduced_Model.mat')

%% INPUT PARAMETER
%--------------------------------------------------------------------------
index_axialForce=3;
%--------------------------------------------------------------------------

considered_AxialLoad=F_ax(index_axialForce)


figure
subplot(2,4,1),spy(Blade.M(:,:,index_axialForce))
title(['Dummyblade reduced mass',newline,['at axial load F_a_x=',num2str(F_ax(index_axialForce)/1e3,3),'kN']])
subplot(2,4,5),spy(Blade.K(:,:,index_axialForce))
title(['Dummyblade reduced stiffness',newline,['at axial load F_a_x=',num2str(F_ax(index_axialForce)/1e3,3),'kN']])

subplot(2,4,2),spy(SlotXp.M(:,:)),title('slot Xp reduced mass')
subplot(2,4,6),spy(SlotXp.K(:,:)),title('slot Xp reduced stiffness')

subplot(2,4,3),spy(M_GLOB(:,:))
title(['Assembly  mass matrix',newline,' - Unconstrained model -',newline,['at axial load F_a_x=',num2str(F_ax(index_axialForce)/1e3,3),'kN']])
subplot(2,4,7),spy(K_GLOB_SE(:,:,index_axialForce))
title(['Assembly stiffness matrix',newline,' - Unconstrained model -',newline,['at axial load F_a_x=',num2str(F_ax(index_axialForce)/1e3,3),'kN']])


%% connectivity of the Unconstrained model
table((1:size(CONNECTIVITY,1))',CONNECTIVITY(:,1),CONNECTIVITY(:,2),CONNECTIVITY(:,3),...
              CONNECTIVITY(:,4),CONNECTIVITY(:,5),CONNECTIVITY(:,6),ContactRegion,...
              'VariableNames',{'Node couple','x_blade','y_blade','z_blade','x_slot','y_slot','z_slot','ContactRegion'})
          
%% CONSTRAINING BASEMENTS OF THE TWO SLOTS --------------------------------
    %                                                                                      ,ux,uy,uz
    SlotXn.CglobDofs=ConstrainGlobalDOFS(SlotXn.NdofsPreviousBodies,SlotXn.Master.Base.dofs, 1, 1, 1);
    SlotXp.CglobDofs=ConstrainGlobalDOFS(SlotXp.NdofsPreviousBodies,SlotXp.Master.Base.dofs, 1, 1, 1);
    CDOFS=[SlotXn.CglobDofs,SlotXp.CglobDofs];
    [M_GLOB_constrained,FDOFS] = ConstrainMATRIX(M_GLOB,CDOFS);
    [K_GLOB_constrained(:,:,index_axialForce),~] = ConstrainMATRIX(K_GLOB_SE(:,:,index_axialForce),CDOFS);
subplot(2,4,4),spy(M_GLOB_constrained)
title(['Assembly  mass matrix',newline,' - Constrained model -',newline,['at axial load F_a_x=',num2str(F_ax(index_axialForce)/1e3,3),'kN']])
subplot(2,4,8),spy(K_GLOB_constrained(:,:,index_axialForce))
title(['Assembly stiffness matrix',newline,' - Constrained model -',newline,['at axial load F_a_x=',num2str(F_ax(index_axialForce)/1e3,3),'kN']])


% CONNECTIVITY OF CONSTRAINED MODEL----------------------------------------
constr_CONN=zeros(size(CONNECTIVITY));
for el=1:size(constr_CONN,1)
    [~,constr_CONN(el,[1:3]),~]   = intersect(FDOFS,CONNECTIVITY(el,[1:3]),'stable');
    [~,constr_CONN(el,[4:6]),~]   = intersect(FDOFS,CONNECTIVITY(el,[4:6]),'stable');
end
table((1:size(constr_CONN,1))',constr_CONN(:,1),constr_CONN(:,2),constr_CONN(:,3),...
              constr_CONN(:,4),constr_CONN(:,5),constr_CONN(:,6),ContactRegion,...
            'VariableNames',{'Node couple','x_blade','y_blade','z_blade','x_slot','y_slot','z_slot','ContactRegion'})

%% EXAMPLE of MANAGING Dofs Indices ---------------------------------------
X10_localDofIndex                     = Node2Dof(Blade.Master.Mid.Zn.Main.X10.matNODES)
X10_assemblyDofIndex                  = Body2Assembly_Dofs(Blade.NdofsPreviousBodies , X10_localDofIndex)
X10_assemblyDofIndex_constrainedModel = AssemblyDof_ConstrainedModel(X10_assemblyDofIndex ,FDOFS)

return
%%
function  [K_ff,Fdofs] = ConstrainMATRIX(K,Cdofs)
% |K_ff  K_fc | {q_f } = Fe_f + 0
% |K_cf  K_cc | { 0  } = Fe_c + Rv_c
%
% [K_ff] {q_f} = Fe_f
%

AllDofs=1:size(K,1);
Fdofs=setdiff(AllDofs,Cdofs,'stable');

K_ff=K(Fdofs,Fdofs);
% K_cc=K(Cdofs,Cdofs);
% K_fc=K(Fdofs,Cdofs);
% K_cf=K(Cdofs,Fdofs);

end
function CglobDofs=ConstrainGlobalDOFS(NdofsPreviousBodies,DOFS,ux,uy,uz)

idx=[];
if ux
idx = [idx, 1:3:length(DOFS)];
end
if uy
idx = [idx, 2:3:length(DOFS)];
end
if uz
idx = [idx, 3:3:length(DOFS)];
end
idx=sort(idx);

CglobDofs=NdofsPreviousBodies + DOFS(idx);
end

function LocalDofIndex=Node2Dof(LocalNodeIndex)
% - LocalNodeIndex: index of the considered node in the array of nodes of a
%   body (dummyblade or slot). It correspond to the field .matNODES inside
%   each structure Blade or SlotXn or SlotXp
% - LocalDofIndex: set of 3 indices of degrees of freedom along x,y,z
%   corresponding to the node indicated by the index LocalNodeIndex. They
%   are indices in the array of dofs of a body (dummyblade or slot). They
%   correspond to the field .dofs inside each structure Blade or SlotXn or SlotXp
       LocalDofIndex=3*(LocalNodeIndex -1)  +[1,2,3];
end
function AssemblyDofIndex = Body2Assembly_Dofs(NdofsPreviousBodies, LocalDofIndex)
        AssemblyDofIndex = NdofsPreviousBodies + LocalDofIndex;
end
function AssemblyDofIndex_ConstrainedModel = AssemblyDof_ConstrainedModel(AssemblyDofIndex_Unconstrained, FreeDofs_afterConstraining)
[ ~,AssemblyDofIndex_ConstrainedModel  ] = intersect( FreeDofs_afterConstraining,AssemblyDofIndex_Unconstrained,'stable');
end
