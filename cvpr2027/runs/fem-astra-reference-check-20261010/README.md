# Astra reference-generation access check

All 50 studies and 82 source reference images are present. Two minimal Astra requests were sent before uploading study content. The configured Experiential Labs gateway rejected Astra with HTTP 429 and model_requires_purchase. The configured official OpenAI API rejected Astra with HTTP 429 and credit_balance_exhausted. No study generation occurred, no candidate was produced, and no FEM capability score can be assigned.

Evidence: access-check.json and result.json. Keys were read in memory and excluded from saved evidence.
