# ABAQUS REPORT 

### 1. Executive Summary
This project involved the structural modeling and displacement analysis of a truss system using Abaqus/CAE. The study focused on characterizing deformation under incremental loading and implementing a Python-based automation workflow for high-precision data extraction.
### 2. Technical Setup & Materiality
The truss was modeled as a series of pinned-joint elements with the following mechanical properties:

    Elastic Modulus (E): 6.0 GPa

    Density (ρ): 600 kg/m3

    Element Type: Linear Truss (T2D2)
### 3. Simulation Methodology
The analysis followed a rigorous multi-step loading protocol to observe the progression of structural deflection.

    Incremental Loading: Loads were applied in ten discrete stages, ranging from 0.15 kg to 1.0 kg (0.981 N to 9.81 N).

    Boundary Conditions: Defined fixed and rolling supports to simulate realistic constraints.

    Nodal Indexing: Each joint (node) was individually labeled to ensure systematic tracking throughout the deformation process.
### 4. Data Automation & Results
A significant technical contribution was the development of a Python post-processing script to bridge the gap between simulation and data analysis.

    Automated Extraction: The script interfaced with the Abaqus Output Database (.odb) to capture nodal coordinates for every loading step.

    Data Format: Results were exported into a CSV file, providing a comprehensive log of initial vs. final coordinates.

    Visualization: A simulation recording was produced, providing visual evidence of the truss's bending behavior and identifying high-stress regions.
### 5. Conclusion
The integration of FEA with Python automation successfully demonstrated the linear elastic response of the truss. The resulting dataset provides a reliable foundation for calculating stiffness matrices and validating the structural design against theoretical expectations.
