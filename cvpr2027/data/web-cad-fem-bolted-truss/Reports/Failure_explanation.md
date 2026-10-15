# Detailed Description of Failure
In this document, we shall discuss the failure of the truss we have constructed, the assumptions that proved us invalid during the experiment, and why the Abaqus simulation becomes irrelevant after some time.

The truss that was built was not exactly planar. It had 3d characteristics that caused the truss to deform in 3-dimensional space. Some joints had 4 members attached, while some joints had only 2, which added depth characteristics. So when the load on the truss got more than 0.5 kg, a reasonable torque was generated on the overall structure, which created bending moments across the members (showing an application of eccentric load).

<img src="../Results/Detailed_node_wise_analysis.png" alt="Detailed node-wise analysis">

 So in the above image we can see that there is a higher change in displacement from the 0.5kg load compared to the loads less than 0.5kg. 

Let’s discuss various characteristics to avoid significant deviation from ideal conditions in the experimental setup. Joint imperfections across each member; each member would have been attached to the same level as other members, causing more or less rotation compared to other members, which leads to deviation from simulated results. Fabrication errors such as imperfect lengths of members, slight deviation in the drilling of holes, further accounted for errors. Variation in physical properties such as non-uniform Young’s modulus, reduction of structural stability of members after drilling, has caused further deviation during the experiment.

In conclusion, this experiment really highlights how important it is to get manufacturing and assembly as accurate as possible when you are engineering structures. It is not the software that is failing, but rather how much real structures can change when they are not exactly as they were designed.