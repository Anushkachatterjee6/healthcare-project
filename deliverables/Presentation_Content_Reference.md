# Presentation Content Reference

- **44 slides**; **45 actual project figures/notebook outputs** copied into `Presentation_Assets/`.
- `models/model_metadata.json`: brats-flair-slice-cnn-v1; 128×128×1 FLAIR; threshold 0.50.
- `models/evaluation_report.json`: accuracy 0.6286, ROC-AUC 0.9384, confusion matrix [[11,1],[12,11]], one held-out patient.
- `models/training_history.json`: embedded learning curves.
- `HER_Biomedical_Image_Tutorials_T1_T6.ipynb`: extracted original plots for T1–T6.
- `artifacts/visual_T13_0.png`, `visual_T14_2.png`, `visual_T14_3.png`, `forecast_preview.png`: T13–T15 outputs.
- `backend/tutorials.py`, `her_core/*`, `frontend/*`: implementation sources.

All CNN claims are experimental, slice-level and research-only. No clinical validation, diagnosis, predicted segmentation or fabricated metric is asserted.