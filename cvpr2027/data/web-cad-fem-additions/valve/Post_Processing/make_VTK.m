clear all; close all; clc;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Define the simulation frame to plot
frame_number_start = 0;
frame_number_end = 4;

for iframe = frame_number_start:frame_number_end
    fprintf('===========================================\n');
    fprintf('===========================================\n');
    fprintf(['Beginning Frame ' num2str(iframe) '\n']);
    
    frame_number = iframe;
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Define the filename & location of the element .inp files
    filename_elem_leaflet = ['../Abaqus_Simulation_Files/02_Model_elem_leaflet.inp'];
    filename_elem_chordae = ['../Abaqus_Simulation_Files/03_Model_elem_chord.inp'];
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Define the filename & location of the .txt files
    filename1 = ['../Text_Files/00_run_Model_node_Frame' num2str(frame_number) '.txt'];
    filename3 = ['../Text_Files/00_run_Model_elem_Frame' num2str(frame_number) '.txt'];
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Define the filename & location of the .vtk file and .mat file
    filename2 = ['../ParaView_Visualization/00_run_Model_Frame' num2str(frame_number) '.vtk'];
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Read & store the element information
    fprintf('Reading element information ...');
    element_info_array = [];
    fid_leaf = fopen(filename_elem_leaflet, 'r');
    fgetl(fid_leaf);
    
    while ~feof(fid_leaf)
        temp = fgetl(fid_leaf);
        temp_split = strsplit(temp, ',');
        temp_gather = [];
        
        for jj = 1:length(temp_split(1,:))
            temp_gather(1,jj) = str2num(temp_split{1,jj}(:)');
        end
        
        element_info_array = [element_info_array; temp_gather];
        
    end
    fclose(fid_leaf);
    
    element_info_array_chordae = [];
    fid_chord = fopen(filename_elem_chordae, 'r');
    fgetl(fid_chord);
    
    while ~feof(fid_chord)
        temp = fgetl(fid_leaf);
        temp_split = strsplit(temp, ',');
        temp_gather = [];
        
        for jj = 1:length(temp_split(1,:))
            temp_gather(1,jj) = str2num(temp_split{1,jj}(:)');
        end
        
        element_info_array_chordae = [element_info_array_chordae; temp_gather];
    end
    fprintf(' Completed\n');
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Read & store the node .txt information
    fprintf('Reading the node .txt file ...');
    
    fid1 = fopen(filename1, 'r');
    counter_line = 0;
    
    while ~feof(fid1)
        fgetl(fid1);
        counter_line = counter_line+1;
        
    end
    
    fclose(fid1);
    fid1 = fopen(filename1, 'r');
    
    for iline = 1:counter_line
        node_info_temp{iline,1} = strsplit(fgetl(fid1));
    end
    
    fclose(fid1);
    
    for ii = 1:counter_line
        for jj = 1:length(node_info_temp{1,1}(1,:))
            node_info(ii,jj) = str2double(node_info_temp{ii,1}(1,jj));
            
        end
    end
    
    node_info = node_info(:,2:end-1);
    num_node = length(node_info(:,1));
    fprintf(' Completed\n');
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Read & store the element .txt information
    fprintf('Reading the element .txt file ...');
    
    fid3 = fopen(filename3, 'r');
    
    counter3 = 0; found_chordae = false;
    
    while ~feof(fid3)
        temp = str2double(strsplit(fgetl(fid3)));
        counter3 = counter3 + 1;
        
        if (temp(1,3) >= 20000) & (found_chordae == false)
            chordae_start_ID = counter3;
            found_chordae = true;
        end
        
    end
    fclose(fid3);
    
    fid3 = fopen(filename3, 'r');
    
    leaflet = true;
    
    counter_leaflet = 1;
    counter_chordae = 1;
    
    %%%%% Modify for stress and strain information
    
    for ii = 1:(chordae_start_ID-1) / 8
        for jj = 1:8
            temp = str2double(strsplit(fgetl(fid3)));
            
            elem_info_leaflet{ii,1}(jj,:) = temp;
            
        end
        
        elem_info_leaflet{counter_leaflet,1} = elem_info_leaflet{ii,1}(:,3:end);
        
        elem_info_stress_leaflet{counter_leaflet,1} = elem_info_leaflet{ii,1}([1 3 5 7], 3:end);
        elem_info_strain_leaflet{counter_leaflet,1} = elem_info_leaflet{ii,1}([2 4 6 8], 3:end-1);
        
        %%%%%%%%%%% Is this the correct calculation for LE --> E?
        
        for jj = 1:4
            for kk = 1:length(elem_info_strain_leaflet{ii,1}(jj,2:end)) %%%%%%%%%%%%%%%%%%%%%%%%%% ??
                elem_info_strain_leaflet{counter_leaflet,1}(jj,1+kk) = (1/2) * ((exp(elem_info_strain_leaflet{ii,1}(jj,1+kk)))^2-1);
            end
        end
        
        elem_info_ID_leaflet(counter_leaflet,1) = elem_info_leaflet{ii,1}(1,1);
        
        elem_results_stress_leaflet(counter_leaflet,:) = [elem_info_leaflet{counter_leaflet,1}(1,1) mean(elem_info_stress_leaflet{counter_leaflet,1}(:,2:end))];
        elem_results_strain_leaflet(counter_leaflet,:) = [elem_info_leaflet{counter_leaflet,1}(1,1) mean(elem_info_strain_leaflet{counter_leaflet,1}(:,2:end))];
        
        counter_leaflet = counter_leaflet + 1;
        
    end
    
    for ii = 1:((counter3 - chordae_start_ID)/2)+1
        for jj = 1:2
            temp = str2double(strsplit(fgetl(fid3)));
            elem_info_chordae{ii,1}(jj,:) = temp;
        end
        
        elem_info_chordae{counter_chordae,1} = elem_info_chordae{ii,1}(:,3:end);
        
        elem_info_stress_chordae{counter_chordae,1} = elem_info_chordae{ii,1}([1], 3:end);
        elem_info_strain_chordae{counter_chordae,1} = elem_info_chordae{ii,1}([2], 3:end-1);
        
        %%%%%%%%%%% Is this the correct calculation for LE --> E?
        
        for jj = 1
            for kk = 1:length(elem_info_strain_chordae{ii,1}(jj,2:end))
                elem_info_strain_chordae{counter_chordae,1}(jj,1+kk) = (1/2) * ((exp(elem_info_strain_chordae{ii,1}(jj,1+kk)))^2-1);
            end
        end
        
        elem_info_ID_chordae(counter_chordae,1) = elem_info_chordae{ii,1}(1,1);
        
        elem_results_stress_chordae(counter_chordae,:) = [elem_info_chordae{counter_chordae,1}(1,1) elem_info_stress_chordae{counter_chordae,1}(:,2:end)];
        elem_results_strain_chordae(counter_chordae,:) = [elem_info_chordae{counter_chordae,1}(1,1) elem_info_strain_chordae{counter_chordae,1}(:,2:end)];
        
        counter_chordae = counter_chordae + 1;
    end
    
    fclose(fid3);
    fprintf(' Completed\n');
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Rearrange the stress and strain information for easier calculations
    fprintf('Rearranging the stress and strain information ...');
    
    [m n] = size(elem_info_leaflet);
    
    for ii = 1:m/2
        temp_ID = find(elem_info_ID_leaflet(:,1) == ii);
        
        temp_array_stress = [elem_info_stress_leaflet{temp_ID(1),1}; elem_info_stress_leaflet{temp_ID(2),1}];
        temp_array_strain = [elem_info_strain_leaflet{temp_ID(1),1}; elem_info_strain_leaflet{temp_ID(2),1}];
        
        for jj = 1:4
            temp_array_2_stress(jj,:) = (temp_array_stress(jj,:) + temp_array_stress(4+jj,:)) / 2;
            temp_array_2_strain(jj,:) = (temp_array_strain(jj,:) + temp_array_strain(4+jj,:)) / 2;
        end
        
        temp_ID = find(elem_results_stress_leaflet == ii);
        
        elem_results_stress_leaflet_final{ii,1} = [elem_results_stress_leaflet(temp_ID,:); ii, mean(temp_array_2_stress(:,2:end))];
        elem_results_strain_leaflet_final{ii,1} = [elem_results_strain_leaflet(temp_ID,:); ii, mean(temp_array_2_strain(:,2:end))];
        
    end
    
    elem_results_stress_chordae_final = elem_results_stress_chordae;
    elem_results_strain_chordae_final = elem_results_strain_chordae;
    fprintf(' Completed\n');
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Write the .vtk file
    fprintf('Writing the .vtk file ...');
    fid100 = fopen(filename2, 'w');
    
    tic
    
    fprintf(fid100, '# vtk DataFile Version 3.0\n');
    fprintf(fid100, 'vtk output\n');
    fprintf(fid100, 'ASCII\n');
    fprintf(fid100, 'DATASET UNSTRUCTURED_GRID\n');
    fprintf(fid100, ['POINTS ' num2str(num_node) ' float\n']);
    
    for inode = 1:num_node
        fprintf(fid100, '%9.4f %9.4f %9.4f', node_info(inode,2), node_info(inode,3), node_info(inode,4));
        if mod(inode,3) == 0
            fprintf(fid100, '\n');
        end
    end
    
    [m n] = size(element_info_array); %%% This array needs to be updated with chordae information
    [m_chordae n_chordae] = size(element_info_array_chordae);
    
    fprintf(fid100, '\n');
    fprintf(fid100, ['Cells ' num2str(m) ' %d\n'], 5*m);
    
    for ielement = 1:m
        fprintf(fid100, '4 %6d %6d %6d %6d\n', element_info_array(ielement, 2)-1, element_info_array(ielement,3)-1, element_info_array(ielement,4)-1, element_info_array(ielement,5)-1);
    end
    
    fprintf(fid100, '\n');
    fprintf(fid100, ['CELL_TYPES ' num2str(m) '\n']);
    
    for ielement = 1:m
        fprintf(fid100, '9\n');   %%%%%%%%%% Need to check if this is the proper definition
    end
    
    fprintf(fid100, '\n');
    fprintf(fid100, 'CELL_DATA %d\n', m);
    fprintf(fid100, 'SCALARS Stress_Mises_atrium float 1\n');
    fprintf(fid100, 'LOOKUP_TABLE default\n');
    
    for ielement = 1:m
        fprintf(fid100, '%9.4f  \n', elem_results_stress_leaflet_final{ielement,1}(2,8));
    end
    
    fprintf(fid100, '\n');
    fprintf(fid100, 'SCALARS Strain_E_atrium float 1\n');
    fprintf(fid100, 'LOOKUP_TABLE default\n');
    
    for ielement = 1:m
        fprintf(fid100, '%9.4f  \n', elem_results_strain_leaflet_final{ielement,1}(2,6));
    end
    
    fprintf(fid100, '\n');
    fprintf(fid100, 'SCALARS Stress_Mises_ventricle float 1\n');
    fprintf(fid100, 'LOOKUP_TABLE default\n');
    
    for ielement = 1:m
        fprintf(fid100, '%9.4f  \n', elem_results_stress_leaflet_final{ielement,1}(1,8));
    end
    
    fprintf(fid100, '\n');
    fprintf(fid100, 'SCALARS Strain_E_ventricle float 1\n');
    fprintf(fid100, 'LOOKUP_TABLE default\n');
    
    for ielement = 1:m
        fprintf(fid100, '%9.4f  \n', elem_results_strain_leaflet_final{ielement,1}(1,6));
    end
    
    fprintf(fid100, '\n');
    fprintf(fid100, 'SCALARS Stress_Mises_average float 1\n');
    fprintf(fid100, 'LOOKUP_TABLE default\n');
    
    for ielement = 1:m
        fprintf(fid100, '%9.4f  \n', elem_results_stress_leaflet_final{ielement,1}(3,8));
    end
    
    fprintf(fid100, '\n');
    fprintf(fid100, 'SCALARS Strain_E_average float 1\n');
    fprintf(fid100, 'LOOKUP_TABLE default\n');
    
    for ielement = 1:m
        fprintf(fid100, '%9.4f  \n', elem_results_strain_leaflet_final{ielement,1}(3,6));
    end
    
    fclose(fid100);
    fprintf(' Completed\n');
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Clear all of the unecessary variables for the next step
    
    clear counter3 counter_line elem_info elem_info_ID elem_results elem_results_final
    clear elem_info_array fid1 fid100 fid3 ID_temp ielement ii iline inode jj leaflet
    clear m n nc nc_temp node_info node_info_temp nr nr_temp num_node temp temp_array temp_array_2 temp_ID
    
    clear elem_info_chordae elem_info_ID_chordae elem_info_ID_leaflet elem_info_leaflet
    clear elem_info_strain_chordae elem_info_strain_leaflet elem_results_strain_chordae elem_results_strain_chordae_final elem_results_strain_leaflet
    clear elem_results_strain_leaflet_atrium elem_results_strain_leaflet_average elem_results_strain_leaflet_final elem_results_strain_leaflet_ventricle
    clear elem_info_stress_chordae elem_info_stress_leaflet elem_results_stress_chordae elem_results_stress_chordae_final elem_results_stress_leaflet
    clear elem_results_stress_leaflet_atrium elem_results_stress_leaflet_average elem_results_stress_leaflet_final elem_results_stress_leaflet_ventricle
    
end
