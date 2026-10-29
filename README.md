# HER Healthcare Analytics Laboratory

An offline Windows laboratory for T1–T15: MRI processing, healthcare operations, clinical text and adult behavioral research. The existing MRI notebook and BraTS files remain the foundation. T7–T15 examples are explicitly synthetic demonstrations; all results are computed by shared Python modules.

From PowerShell in this project folder:

```powershell
py -3 -m pip install -r requirements.txt
.\run_server.bat
```

Python 3.11 was verified in the supplied environment. It already has the required packages; no dependency installation was needed during implementation. The script uses one process for both the frontend and backend:

- Dashboard: http://127.0.0.1:8000/
- MRI matching studio: http://127.0.0.1:8000/image-analysis
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/health

Keep the server terminal open. Stop with Ctrl+C. If port 8000 is occupied, stop the other server or use `py -3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8001` and open that port; same-origin frontend requests still work. Open the served URL, not an HTML file or the IDE JSON server.

Select a tutorial, inspect its dataset requirements and click **Run analysis**. Expand tables, inspect plots and export result JSON. Download a labeled example CSV to demonstrate uploads. T10–T12 support entered text, T12 a ranking query, T10 cluster count, and T7 an explicit workload assumption. T5 also has a compact CNN training/inference button; it is a smoke experiment, not a pretrained diagnostic model. That button trains a fresh 32×32 model for three epochs and shows input/mask/prediction previews, train/validation accuracy and loss curves, a confusion matrix and complete predictions/classification-report tables. Scores are model outputs, not calibrated clinical confidence. The ordinary T5 **Run analysis** button still runs SIFT/RANSAC.

The canonical notebook is `HER_Biomedical_Image_Tutorials_T1_T6.ipynb`; its name is retained to preserve references, but it contains T1–T15. Open it in VS Code, select Python 3.11 and Run All. Its original CNN experiment defaults to 8 epochs; set `HER_CNN_EPOCHS=1` before launching the kernel for a shorter verification. Every T7–T15 section imports the same computations as the API.

Verification commands:

```powershell
py -3 -m unittest discover -s tests -v
py -3 scripts/verify_notebook.py
$env:PYTHONIOENCODING='utf-8'
py -3 test_cnn_pipeline.py
py -3 test_cnn_model.py
# With run_server.bat running in another terminal:
py -3 scripts/verify_live.py
node tests/frontend_integration.cjs
```

Node is only needed for the frontend integration test, not for running the application. This test uses a minimal DOM adapter and actual HTTP calls; it does not replace visual browser verification. Notebook verification launches a Jupyter kernel; a restrictive Windows sandbox may require permission to launch that child process. QA artifacts are saved under ignored `artifacts/`.

See [SUBMISSION_REPORT.md](SUBMISSION_REPORT.md) for actual outcomes, a completion matrix, file changes, limitations and a demonstration sequence. See [DATASETS.md](DATASETS.md) for CSV schemas, units and optional public-source preparation. No additional data downloads are required to demonstrate the supplied project. Do not run the legacy notebook-replacement script as part of normal startup; `scripts/extend_notebook.py` maintains the new sections idempotently.
