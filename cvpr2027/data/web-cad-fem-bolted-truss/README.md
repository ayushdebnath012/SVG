# README

This repository contains the CAD model, Abaqus simulation data, video tracking, and MATLAB/Octave analysis used to study truss deformation under increasing load. It includes raw and processed tracking data, polynomial fits, and comparison plots between the physical experiment and the simulation.

## If you are evaluating
- Start with the conclusions in [Reports/Displacement_vs_load_justification.md](Reports/Displacement_vs_load_justification.md) and [Reports/Failure_explanation.md](Reports/Failure_explanation.md)
- Read the Abaqus summary in [Reports/Abaqus _Report.md](Reports/Abaqus%20_Report.md)
- Browse the key plots in [Results/truss_node_displacement.png](Results/truss_node_displacement.png) and [Results/Detailed_node_wise_analysis.png](Results/Detailed_node_wise_analysis.png)
- Review how the results were generated in [Data_analysis/](Data_analysis/) and the datasets in [Image_processing_data/](Image_processing_data/) and [Abaqus simulation data/](Abaqus%20simulation%20data/)

## Repository map
- CAD model (Solid Edge): main assembly at [3D_Model/INTRO TO ME/FINAL TRUSS ASSEMBLY.asm](3D_Model/INTRO%20TO%20ME/FINAL%20TRUSS%20ASSEMBLY.asm) with parts in [3D_Model/INTRO TO ME/](3D_Model/INTRO%20TO%20ME/)
- Abaqus simulation: model file at [Abaqus simulation data/final_intro_to_mae.cae](Abaqus%20simulation%20data/final_intro_to_mae.cae), nodal displacement export at [Abaqus simulation data/Abaqus_node_displacement_data.csv](Abaqus%20simulation%20data/Abaqus_node_displacement_data.csv), polynomial fit output at [Abaqus simulation data/Poly_Fit_Results.csv](Abaqus%20simulation%20data/Poly_Fit_Results.csv), and screen recording at [Abaqus simulation data/Simulation_recording.mp4](Abaqus%20simulation%20data/Simulation_recording.mp4)
- Tracker project: [Video_analysis.trk](Video_analysis.trk)
- Image processing data: raw tracking at [Image_processing_data/Raw_image_processing data.csv](Image_processing_data/Raw_image_processing%20data.csv), processed load-step data at [Image_processing_data/Processed_data.csv](Image_processing_data/Processed_data.csv), and polynomial fit output at [Image_processing_data/Poly_Fit_Results.csv](Image_processing_data/Poly_Fit_Results.csv)
- Reports: [Reports/Abaqus _Report.md](Reports/Abaqus%20_Report.md), [Reports/Displacement_vs_load_justification.md](Reports/Displacement_vs_load_justification.md), [Reports/Failure_explanation.md](Reports/Failure_explanation.md)
- MATLAB/Octave analysis scripts:
  - [Data_analysis/Image_processing_polyfit.m](Data_analysis/Image_processing_polyfit.m)
  - [Data_analysis/Abaqus_data_polyfit.m](Data_analysis/Abaqus_data_polyfit.m)
  - [Data_analysis/Node_displacement_analysis.m](Data_analysis/Node_displacement_analysis.m)
  - [Data_analysis/Per_node_detailed_analysis.m](Data_analysis/Per_node_detailed_analysis.m)
- Results and media: [Results/](Results/), [Results/CAD_design screenshots/](Results/CAD_design%20screenshots/), [Photos/](Photos/), [Video recordings/](Video%20recordings/)
- License: [LICENSE](LICENSE) (MIT)

## Analysis detailed workflow
1. Track node positions in Tracker using [Video_analysis.trk](Video_analysis.trk), then export the raw tracking data to [Image_processing_data/Raw_image_processing data.csv](Image_processing_data/Raw_image_processing%20data.csv)
2. Manually select the required frames and extract load-step positions into [Image_processing_data/Processed_data.csv](Image_processing_data/Processed_data.csv)
3. Fit polynomials to experimental data with [Data_analysis/Image_processing_polyfit.m](Data_analysis/Image_processing_polyfit.m)
4. Fit polynomials to Abaqus outputs with [Data_analysis/Abaqus_data_polyfit.m](Data_analysis/Abaqus_data_polyfit.m)
5. Generate comparison plots with [Data_analysis/Node_displacement_analysis.m](Data_analysis/Node_displacement_analysis.m) and [Data_analysis/Per_node_detailed_analysis.m](Data_analysis/Per_node_detailed_analysis.m)

## Software requirements
- MATLAB or GNU Octave (for analysis scripts)
- Solid Edge 2025 or newer (for CAD model files)
- Tracker (Open Source Physics) for video tracking
- Abaqus/CAE (optional, to open or regenerate the simulation)

## How to run the MATLAB/Octave analysis
- Open the repository as your working directory
- Run [Data_analysis/Image_processing_polyfit.m](Data_analysis/Image_processing_polyfit.m)
- Run [Data_analysis/Abaqus_data_polyfit.m](Data_analysis/Abaqus_data_polyfit.m)
- Run [Data_analysis/Node_displacement_analysis.m](Data_analysis/Node_displacement_analysis.m) for node trajectory plots
- Run [Data_analysis/Per_node_detailed_analysis.m](Data_analysis/Per_node_detailed_analysis.m) for per-node load-step displacement comparisons

Note: The polyfit scripts write Poly_Fit_Results.csv to the current working directory. If you keep the script defaults, run them with the working directory set to the target data folder or copy the outputs into [Image_processing_data/](Image_processing_data/) and [Abaqus simulation data/](Abaqus%20simulation%20data/) so [Data_analysis/Per_node_detailed_analysis.m](Data_analysis/Per_node_detailed_analysis.m) can read them.

## Results and outputs
- Summary plots: [Results/truss_node_displacement.png](Results/truss_node_displacement.png), [Results/Detailed_node_wise_analysis.png](Results/Detailed_node_wise_analysis.png)
- Processed tracking video: [Results/Processed_video_output.mp4](Results/Processed_video_output.mp4)
- Abaqus simulation recording: [Abaqus simulation data/Simulation_recording.mp4](Abaqus%20simulation%20data/Simulation_recording.mp4)
- CAD design screenshots: [Results/CAD_design screenshots/](Results/CAD_design%20screenshots/)
- Experiment photos: [Photos/Final_Assembled truss.JPG](Photos/Final_Assembled%20truss.JPG), [Photos/Before.HEIC](Photos/Before.HEIC), [Photos/After.HEIC](Photos/After.HEIC)

## Authors
- [Shass27](https://github.com/Shass27) (Shaswath S)
- [pabitrakumar1607-a11y](https://github.com/pabitrakumar1607-a11y) (Pabitra Kumar)
- [Si-kon](https://github.com/Si-kon) (Sibasis Panda)
- [me25btech11015-max](https://github.com/me25btech11015-max) (Brijesh Pullakesh)
- [thor12loki34-star](https://github.com/thor12loki34-star) (Ridam Bagul)

## License
MIT License. See [LICENSE](LICENSE).

