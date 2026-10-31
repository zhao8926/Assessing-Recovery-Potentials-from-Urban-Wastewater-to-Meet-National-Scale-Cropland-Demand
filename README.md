# Assessing-Recovery-Potentials-from-Urban-Wastewater-to-Meet-National-Scale-Cropland-Demand
Recycled phosphorus from wastewater can return croplands efficiently, showing logistics are not the obstacle once assumed.
This repository contains the core code and analytical procedures supporting the research presented in the paper titled "Unlocking Phosphorus Recycling: Simulated Vehicle Transport from Urban Wastewater to Neighboring Croplands." The project focuses on modeling and optimizing phosphorus transport routes from urban wastewater treatment plants to neighboring croplands, thereby contributing to sustainable phosphorus recycling efforts.

Copyright: Guorong Zhao, School of Environmental Science&Engineering, Tianjin University
Contact: zhao_8926@tju.edu.cn, WeChat: lyxq_zhao
Primary version was made in March 24, 2025
Last updated ：October 31, 2026

The key functionalities include:
⦁	Detailed topological processing of the road network data across China
⦁	Spatial matching algorithms between wastewater treatment plants and croplands
⦁	Construction of origin-destination (OD) cost matrix models
⦁	Simulated annealing algorithms to optimize transport routes for different phosphorus products, considering both vehicle combinations and single vehicle load capacity scenarios
⦁	Visualization of transportation routes based on various distance measurement methods
⦁	Generation and rendering of key statistical figures used in the publication

There are three folders under this repository
1.	example_for_SA: Sample inputs and outputs designed for testing and validating the simulated annealing optimization.
2.	Codes_for_Fig: Datasets and code necessary for replicating the statistical visualizations featured in the publication.
3.	Dataset_SI: Supplementary Information tables (Tables S2, S4, S6, and S7) providing comprehensive datasets on WWTP characteristics, vehicle routing optimization results, CO2 emission metrics across baseline and alternative scenarios, and comparisons of spatial distance calculation methods.

Detailed usage instructions and parameter explanations are documented within each script.

Software Requirements:
⦁	ArcGIS Pro 3.4.2
⦁	Python 3.10.11 (ArcGIS Python environment)
⦁	Python 3.11.10 (for some supplementary scripts)
