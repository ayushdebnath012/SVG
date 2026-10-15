# Published FEM reference assets

Crawled the original download listings for all 50 existing studies. All exact tutorial versions match. Public download streams and MPH archive directories were inspected; no simulations, field values or grading tolerances were generated.

**50/50 studies have public solver models with binary mesh and solution entries.** These entries are existing source solution data; reading their physical fields requires COMSOL. Their presence does not certify mesh convergence or numerical accuracy.

Saved 80 existing small/supporting files and selected models (about 159 MB). The full set of solver models is approximately 19.6 GB; larger models are linked and their archive directories were checked using HTTP range requests instead of downloading them in full. The dataset PDF was not changed.

## Standalone numerical references

| Study | Published file | Rows | Description |
|---|---|---:|---|
| FEMCAD-ADV-005 | [perforated_muffler_exp_data.txt](/Users/ayushdebnath/SVG/cvpr2027/tmp/femcad-reference-assets/FEMCAD-ADV-005/perforated_muffler_exp_data.txt) | 296 | Frequency and measured transmission loss; source tutorial Figure 7. |
| FEMCAD-ADV-021 | [sheet_metal_forming.txt](/Users/ayushdebnath/SVG/cvpr2027/tmp/femcad-reference-assets/FEMCAD-ADV-021/sheet_metal_forming.txt) | 28 | Measured punch force versus punch displacement; source tutorial Figure 7. |
| FEMCAD-ADV-026 | [composite_dome_tweeter_freq_Lp_data.txt](/Users/ayushdebnath/SVG/cvpr2027/tmp/femcad-reference-assets/FEMCAD-ADV-026/composite_dome_tweeter_freq_Lp_data.txt) | 160 | Frequency and sound-pressure-level response columns imported by the published model; preserve source column definitions. |
| FEMCAD-ADV-026 | [composite_dome_tweeter_freq_Z_data.txt](/Users/ayushdebnath/SVG/cvpr2027/tmp/femcad-reference-assets/FEMCAD-ADV-026/composite_dome_tweeter_freq_Z_data.txt) | 160 | Frequency and impedance response columns imported by the published model; preserve source column definitions. |

Sheet forming also publishes experimental angle intervals in Table 1: forming angle 19.6–21.0 degrees; release angle 53.4–55.8 degrees. These are published measurements, not automatically assigned grading thresholds.

Input tables for materials, prescribed displacement, CAD profiles and evaluation expressions are catalogued separately as supporting assets. They are not mislabeled as output reference values.

## Per-study solver inventory

| Study | Source model | Solution entries | Mesh entries | Stored locally |
|---|---|---:|---:|---|
| FEMCAD-ADV-001 | [rubber_boot_seal.mph](https://www.comsol.com/model/download/1388221/rubber_boot_seal.mph) | 11 | 3 | Yes |
| FEMCAD-ADV-002 | [piezoelectric_valve.mph](https://www.comsol.com/model/download/1379031/piezoelectric_valve.mph) | 4 | 2 | Remote directory verified |
| FEMCAD-ADV-003 | [turbine_stator_creep.mph](https://www.comsol.com/model/download/1387101/turbine_stator_creep.mph) | 9 | 3 | Remote directory verified |
| FEMCAD-ADV-004 | [gear_train.mph](https://www.comsol.com/model/download/1559241/gear_train.mph) | 19 | 4 | Remote directory verified |
| FEMCAD-ADV-005 | [perforated_muffler.mph](https://www.comsol.com/model/download/1332081/perforated_muffler.mph) | 7 | 3 | Remote directory verified |
| FEMCAD-ADV-006 | [golf_ball_impact.mph](https://www.comsol.com/model/download/1562871/golf_ball_impact.mph) | 43 | 2 | Remote directory verified |
| FEMCAD-ADV-007 | [tire_inflation.mph](https://www.comsol.com/model/download/1561281/tire_inflation.mph) | 7 | 4 | Remote directory verified |
| FEMCAD-ADV-008 | [viscoplastic_solder_joints.mph](https://www.comsol.com/model/download/1562991/viscoplastic_solder_joints.mph) | 31 | 3 | Remote directory verified |
| FEMCAD-ADV-009 | [composite_multiscale.mph](https://www.comsol.com/model/download/1530401/composite_multiscale.mph) | 43 | 19 | Remote directory verified |
| FEMCAD-ADV-010 | [temperature_dependent_plasticity.mph](https://www.comsol.com/model/download/1562391/temperature_dependent_plasticity.mph) | 15 | 4 | Remote directory verified |
| FEMCAD-ADV-011 | [hyperelastic_seal.mph](https://www.comsol.com/model/download/1560821/hyperelastic_seal.mph) | 6 | 2 | Remote directory verified |
| FEMCAD-ADV-012 | [snap_hook.mph](https://www.comsol.com/model/download/1562271/snap_hook.mph) | 20 | 2 | Remote directory verified |
| FEMCAD-ADV-013 | [cable_crimping.mph](https://www.comsol.com/model/download/1561581/cable_crimping.mph) | 24 | 2 | Remote directory verified |
| FEMCAD-ADV-014 | [biomedical_stent.mph](https://www.comsol.com/model/download/1561521/biomedical_stent.mph) | 29 | 2 | Remote directory verified |
| FEMCAD-ADV-015 | [sma_stent.mph](https://www.comsol.com/model/download/1562671/sma_stent.mph) | 8 | 2 | Remote directory verified |
| FEMCAD-ADV-016 | [buckling_hdpe_liner.mph](https://www.comsol.com/model/download/1563131/buckling_hdpe_liner.mph) | 17 | 6 | Remote directory verified |
| FEMCAD-ADV-017 | [compaction_of_a_rotational_flange.mph](https://www.comsol.com/model/download/1562511/compaction_of_a_rotational_flange.mph) | 4 | 2 | Yes |
| FEMCAD-ADV-018 | [comb_drive_tuning_fork_gyroscope_manufacturing_variation.mph](https://www.comsol.com/model/download/1552021/comb_drive_tuning_fork_gyroscope_manufacturing_variation.mph) | 41 | 14 | Remote directory verified |
| FEMCAD-ADV-019 | [phone_drop_test.mph](https://www.comsol.com/model/download/1483701/phone_drop_test.mph) | 13 | 2 | Remote directory verified |
| FEMCAD-ADV-020 | [diaphragm_accumulator.mph](https://www.comsol.com/model/download/1560611/diaphragm_accumulator.mph) | 9 | 3 | Remote directory verified |
| FEMCAD-ADV-021 | [sheet_metal_forming.mph](https://www.comsol.com/model/download/1562191/sheet_metal_forming.mph) | 23 | 6 | Remote directory verified |
| FEMCAD-ADV-022 | [die_forming.mph](https://www.comsol.com/model/download/1561781/die_forming.mph) | 11 | 2 | Remote directory verified |
| FEMCAD-ADV-023 | [composite_wheel_rim.mph](https://www.comsol.com/model/download/1529661/composite_wheel_rim.mph) | 12 | 6 | Remote directory verified |
| FEMCAD-ADV-024 | [wind_turbine_composite_blade.mph](https://www.comsol.com/model/download/1529801/wind_turbine_composite_blade.mph) | 42 | 12 | Remote directory verified |
| FEMCAD-ADV-025 | [progressive_delamination_in_a_laminated_shell.mph](https://www.comsol.com/model/download/1529561/progressive_delamination_in_a_laminated_shell.mph) | 13 | 3 | Remote directory verified |
| FEMCAD-ADV-026 | [composite_dome_tweeter_freq.mph](https://www.comsol.com/model/download/1529891/composite_dome_tweeter_freq.mph) | 75 | 8 | Remote directory verified |
| FEMCAD-ADV-027 | [ply_drop_off_in_a_composite_panel.mph](https://www.comsol.com/model/download/1530581/ply_drop_off_in_a_composite_panel.mph) | 3 | 8 | Remote directory verified |
| FEMCAD-ADV-028 | [composite_blade_multiple_model_method.mph](https://www.comsol.com/model/download/1530301/composite_blade_multiple_model_method.mph) | 23 | 8 | Remote directory verified |
| FEMCAD-ADV-029 | [mixed_mode_delamination.mph](https://www.comsol.com/model/download/1529521/mixed_mode_delamination.mph) | 9 | 5 | Remote directory verified |
| FEMCAD-ADV-030 | [sports_car_fsi.mph](https://www.comsol.com/model/download/1519041/sports_car_fsi.mph) | 212 | 7 | Remote directory verified |
| FEMCAD-ADV-031 | [motherboard_random_vibration.mph](https://www.comsol.com/model/download/1589551/motherboard_random_vibration.mph) | 42 | 4 | Remote directory verified |
| FEMCAD-ADV-032 | [piezoelectric_micropump.mph](https://www.comsol.com/model/download/1550941/piezoelectric_micropump.mph) | 32 | 2 | Remote directory verified |
| FEMCAD-ADV-033 | [solidly_mounted_resonator_3d.mph](https://www.comsol.com/model/download/1551561/solidly_mounted_resonator_3d.mph) | 20 | 5 | Remote directory verified |
| FEMCAD-ADV-034 | [rf_mems_switch.mph](https://www.comsol.com/model/download/1550421/rf_mems_switch.mph) | 11 | 3 | Remote directory verified |
| FEMCAD-ADV-035 | [gyroscope_mixed_formulation.mph](https://www.comsol.com/model/download/1552061/gyroscope_mixed_formulation.mph) | 21 | 6 | Remote directory verified |
| FEMCAD-ADV-036 | [piezoelectric_rate_gyroscope.mph](https://www.comsol.com/model/download/1551171/piezoelectric_rate_gyroscope.mph) | 46 | 4 | Remote directory verified |
| FEMCAD-ADV-037 | [aln_lamb_wave_resonator_3d.mph](https://www.comsol.com/model/download/1550981/aln_lamb_wave_resonator_3d.mph) | 16 | 3 | Remote directory verified |
| FEMCAD-ADV-038 | [twophase_flow_fsi.mph](https://www.comsol.com/model/download/1591141/twophase_flow_fsi.mph) | 56 | 3 | Remote directory verified |
| FEMCAD-ADV-039 | [loudspeaker_driver.mph](https://www.comsol.com/model/download/1506481/loudspeaker_driver.mph) | 41 | 8 | Remote directory verified |
| FEMCAD-ADV-040 | [vented_loudspeaker_enclosure.mph](https://www.comsol.com/model/download/1507941/vented_loudspeaker_enclosure.mph) | 18 | 3 | Remote directory verified |
| FEMCAD-ADV-041 | [electric_motor_noise_pmsm.mph](https://www.comsol.com/model/download/1503541/electric_motor_noise_pmsm.mph) | 88 | 16 | Remote directory verified |
| FEMCAD-ADV-042 | [piezo_mems_speaker.mph](https://www.comsol.com/model/download/1507861/piezo_mems_speaker.mph) | 15 | 3 | Remote directory verified |
| FEMCAD-ADV-043 | [helmholtz_resonator_with_flow.mph](https://www.comsol.com/model/download/1502561/helmholtz_resonator_with_flow.mph) | 38 | 7 | Remote directory verified |
| FEMCAD-ADV-044 | [gearbox_vibration_noise_bearing.mph](https://www.comsol.com/model/download/1557351/gearbox_vibration_noise_bearing.mph) | 259 | 5 | Remote directory verified |
| FEMCAD-ADV-045 | [tonpilz_transducer_prestressed.mph](https://www.comsol.com/model/download/1509401/tonpilz_transducer_prestressed.mph) | 27 | 5 | Remote directory verified |
| FEMCAD-ADV-046 | [aluminum_extrusion_fsi.mph](https://www.comsol.com/model/download/1547131/aluminum_extrusion_fsi.mph) | 6 | 4 | Remote directory verified |
| FEMCAD-ADV-047 | [interior_pm_motor_stress_analysis.mph](https://www.comsol.com/model/download/1496811/interior_pm_motor_stress_analysis.mph) | 37 | 3 | Remote directory verified |
| FEMCAD-ADV-048 | [nonlinear_magnetostriction.mph](https://www.comsol.com/model/download/1498431/nonlinear_magnetostriction.mph) | 18 | 6 | Remote directory verified |
| FEMCAD-ADV-049 | [contactor_shading_coil.mph](https://www.comsol.com/model/download/1498331/contactor_shading_coil.mph) | 18 | 9 | Remote directory verified |
| FEMCAD-ADV-050 | [fuselage_buckling.mph](https://www.comsol.com/model/download/1588211/fuselage_buckling.mph) | 15 | 2 | Remote directory verified |

## Evidence and limits

The structured catalog is `reference-assets.json`, linked from each entry in `advanced-source-studies.json`. Original download listings, SHA-256 hashes for stored files and archive entry sizes are in `tmp/femcad-reference-assets/`.

No standalone nodal displacement/stress array exports were identified in the checked download listings. Those fields may be exported from the published solved models using COMSOL; they have not been converted here. No complete set of published grading tolerances or mesh-convergence certifications was established.

COMSOL format documentation distinguishes solved models with meshes/solutions from compact models without them: https://doc.comsol.com/6.3/doc/com.comsol.help.comsol/comsol_ref_environment.18.15.html
