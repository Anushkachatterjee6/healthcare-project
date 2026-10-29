# Submission report — 29 October 2026

Implemented a connected T1–T15 local laboratory using the existing FastAPI, Python, HTML, CSS and JavaScript stack. T7–T15 share reusable computations between API and notebook. The dashboard provides navigation, per-tutorial readiness/run status, source labels, validated CSV uploads, analysis controls, loading/error states, metrics, expandable tables, real PNG plots and JSON export. The existing MRI matching studio remains available.

## Completion and verification matrix

“Passed” means computations were executed, not that a clinical model was validated. Frontend flows were verified using actual frontend JavaScript with a DOM adapter and live HTTP; visual browser verification was unavailable.

| Tutorial | Implementation | Verification |
|---|---|---|
| T1 | NIfTI case/modality inventory; original volume inspection | Notebook, live API and frontend handler passed |
| T2 | Invalid-intensity cleaning, z-score and min-max normalization | Unit checks, notebook, live API/frontend passed |
| T3 | Missing modalities; original SHA256 duplicate inspection without deletion | Notebook, live inventory API/frontend passed |
| T4 | Original CLAHE/bilateral restoration, same-patient mask overlay, JPEG; dashboard CLAHE/Gaussian/Otsu/JPEG | Notebook and live API/frontend passed |
| T5 | Existing SIFT/RANSAC and 128×128 CNN; compact 32×32 web CNN smoke experiment | Notebook one epoch, original CNN scripts, live matching and CNN HTTP inference passed |
| T6 | Same-patient multimodal display, intensity histogram, overlay; original 3D display | Notebook and live API/frontend passed |
| T7 | Calendar-feature Ridge admission forecasting, chronological 144/36 split, baseline, staffing assumption | Shared-module, API, CSV and frontend flow tests passed |
| T8 | Operational validation, descriptive tables, group/date KPIs, supplied occupancy/cost | Shared-module, API, CSV and frontend flow tests passed |
| T9 | Department comparison, variance, elapsed-time trend, Kruskal test, computed priority | Shared-module, API, CSV and frontend flow tests passed |
| T10 | Training-only TF-IDF/logistic regression, held-out metrics/confusion matrix; K-means and silhouette | Shared-module, API, CSV and frontend flow tests passed |
| T11 | Lexicon/regex mentions, offsets, category, source, extraction method and possible negation | Shared-module, API, CSV and frontend flow tests passed |
| T12 | Cosine document ranking, explicit MS/RA context senses, uncertain/unsupported outputs | Shared-module, API, CSV and frontend flow tests passed |
| T13 | Numeric imputation/scaling, PCA variance/projection, Isomap comparison | Shared-module, API, CSV and frontend flow tests passed |
| T14 | Adult-only selection, valid-unit BMI, missingness/IQR/descriptive/correlation analysis | Shared-module, API, CSV and frontend flow tests passed |
| T15 | Training-only multivariable BMI model, held-out metrics, standardized coefficients, Pearson/Fisher CI | Shared-module, API, CSV and frontend flow tests passed |

All nine new sections were also executed in the complete notebook. The canonical notebook retains its filename and original T1–T6 code, with targeted correctness fixes: portable paths, T1ce recognition, same-patient segmentation overlay and modality comparisons, complete missing-modality columns, and a reproducible CNN seed. Shared CNN mask resizing now uses nearest-neighbor interpolation, and evaluation fixes label order even if one class is absent.

## Files

Created:

- `her_core/analytics.py` — deterministic example factories, validation, statistical/text/model computations and plots.
- `backend/tutorials.py` — metadata, analysis, example CSV, bounded raw CSV upload, MRI tutorial adapters and compact CNN API.
- `frontend/lab.js`, `frontend/lab.css` — dashboard interactions and responsive styling.
- `tests/test_analytics.py`, `tests/frontend_integration.cjs` — automated analysis/API and live frontend-handler coverage.
- `scripts/extend_notebook.py`, `scripts/verify_notebook.py`, `scripts/verify_live.py` — notebook maintenance and executable verification.
- `README.md`, `DATASETS.md`, `IMPLEMENTATION_CHECKLIST.md`, `SUBMISSION_REPORT.md` — startup, data contracts, implementation audit and this report.

Modified:

- Existing notebook, extended in place to 79 cells.
- `backend/main.py` — router integration, same-origin serving, local-origin CORS, restricted dataset-root override and bounded MRI cache.
- `frontend/index.html` — complete dashboard.
- `frontend/image-analysis.js` — visible backend-disconnect error on initial loading.
- `her_core/cnn.py` — discrete mask resizing and robust two-class evaluation.
- `requirements.txt`, `run_server.bat`, `.gitignore` — actual dependencies, single Windows startup, excluded local datasets/models/artifacts.
- `scripts/update_cnn_notebook.py` — replace machine-specific output paths with the project-relative notebook path; legacy maintenance tool, not part of startup.

Preserved: all local MRI volumes and the partial archive, `her_core/io.py`, `her_core/preprocess.py`, `her_core/sift_ransac.py`, existing MRI HTML/CSS, root `index.html` notebook export, existing CNN verification scripts and downloader. No dataset downloads, Git commits, pushes or history changes were made.

## Startup and URLs

In PowerShell, with this project as the working folder:

```powershell
py -3 -m pip install -r requirements.txt
.\run_server.bat
```

Equivalent direct launch:

```powershell
py -3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Frontend and API share http://127.0.0.1:8000. MRI: http://127.0.0.1:8000/image-analysis. OpenAPI: http://127.0.0.1:8000/docs. No second frontend process or JSON server is required. The batch file's uvicorn command was exercised on Windows; double-clicking the batch file was not separately tested.

## Verification commands and actual outcomes

| Command | Outcome |
|---|---|
| `py -3 -m unittest discover -s tests -v` | 13 tests passed, with subtests for each T7–T15 example/API/upload; covers missing columns, empty input, malformed data/files, limits, numerical metrics, preprocessing, patient split and missing MRI |
| `py -3 scripts/verify_notebook.py` | All 79 cells / 41 code cells executed; no cell errors; one 128×128 CNN epoch on real supplied data |
| `py -3 test_cnn_pipeline.py` | Passed; six labeled cases; 121 training and 62 validation slices, four versus two disjoint patients |
| `py -3 test_cnn_model.py` | Passed; 4,287,233-parameter model, one epoch, prediction and evaluation completed |
| `py -3 scripts/verify_live.py` | Passed; real uvicorn HTTP, all T1–T15 routes, health/metadata/static pages, MRI matching, invalid same-slice rejection, compact CNN training/inference |
| `node tests/frontend_integration.cjs` | Passed; 15 navigation→API→render flows, real CSV upload, wrong file extension and backend-disconnect state using DOM adapter |
| `node --check frontend/lab.js` and `node --check frontend/image-analysis.js` | Passed |
| `py -3 -m compileall -q backend her_core scripts tests` | Passed |
| `py -3 -m pip check` | No broken requirements found |

The original CNN script commands were run after `$env:PYTHONIOENCODING='utf-8'` to support their Unicode console output. Notebook kernel launch initially received Windows sandbox access denied; rerunning with approved process permission succeeded. No dependencies needed installing. Non-failing environment warnings concerned Windows GPU unavailability, notebook event-loop compatibility, CPU-core detection and the installed FastAPI/TestClient deprecation.

Recorded artifacts: `artifacts/notebook_verification.json`, `artifacts/executed_notebook.ipynb` and `artifacts/live_verification.json`. The final executed outputs, including inline MRI figures, were retained in the canonical notebook for submission; 79 cells / 41 code cells completed in 22.1 seconds in the final run, with zero cell errors. The artifact copy is a QA record, not a second maintained tutorial notebook. Tests do not save model binaries or uploaded records. Final unit run: 13 tests passed in 8.249 seconds. `git diff --check` also passed.

Representative computed results from the deterministic demonstrations: T7 MAE 3.1599 admissions and RMSE 3.9301, versus training-mean baseline MAE 13.8673; T13 first two PCs explain 0.5015 of standardized variance; T15 holdout MAE 1.5803 BMI units, RMSE 1.9426, R² 0.5469. These are synthetic-data results, not real healthcare evidence. Real local SIFT/RANSAC produced 44 good matches and 35 inliers for the tested central slice pair. CNN validation numbers vary with initialization/training budget and do not establish clinical performance.

Tested Python 3.11 environment: NumPy 2.4.6, pandas 3.0.6, SciPy 1.16.3, scikit-learn 1.9.1, FastAPI 0.136.3, uvicorn 0.27.0, TensorFlow 2.21.0, OpenCV 5.0.0.93, nibabel 5.4.2, matplotlib 3.10.8, nbclient 0.10.4, httpx 0.28.1. The requirements file specifies supported minimums; it is not an exact lockfile.

## Data and limitations

- No operational, clinical-text or adult-behavior data were present; T7–T15 use clearly labeled deterministic synthetic data by default. No download is required. Optional public sources and transformation instructions are in [DATASETS.md](DATASETS.md), including [NHS England](https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/), [MIMIC-IV-Note](https://physionet.org/content/mimic-iv-note/2.2/) and [CDC NHANES](https://wwwn.cdc.gov/nchs/nhanes/). These external import preparations were documented, not downloaded or tested.
- No separate syllabus artifact was supplied; names follow the mission's wording. The original notebook provides the T1–T6 baseline.
- Browser automation was unavailable in the connected toolset. Responsive CSS and handlers exist, but visual layout, actual browser file selection/download behavior and screen-reader behavior remain unverified. No visual-browser pass is claimed.
- Full original CNN defaults to eight epochs; verification used one. The web CNN trains a fresh 32×32 model for three epochs (one full batch per epoch), then returns inference, input/mask previews, measured train/validation curves and classification results; no persisted pretrained model is claimed. This verifies the pipeline, not diagnostic performance. GPU execution was not tested or required. See CNN_FIX_REPORT.md for the subsequent CNN-output regression investigation and checks.
- T10's small template corpus gives optimistic metrics; related wording can occur in train/test. Exact normalized duplicate documents are deduplicated, vectorization fits only training documents, and evaluation labels never enter fitting. Generalization to real clinical language is untested.
- T11 is limited rule-based mention detection; possible-negation flags can be wrong. T12 supports only explicit MS/RA senses. Neither has annotated reference labels; counts/similarities are not accuracy estimates.
- T9 Kruskal comparisons and T15 Pearson confidence intervals require independent observations and the stated statistical assumptions. Synthetic examples illustrate calculations; real repeated or survey data need a study-specific model, sampling design and additional diagnostics. Associations do not establish causation. Staffing calculations are illustrative workload assumptions.
- API work runs in worker threads, with a plot lock and CNN concurrency guard. Uploads are bounded to 2 MB/5,000 rows/50 columns. Results are returned immediately and may be exported; there is no database, persistent history or job queue. This is a local teaching application.

## Five-minute demonstration

1. Run `.\run_server.bat`, open the dashboard and show the connected MRI count and T1–T15 navigation.
2. Run T7, point out the synthetic source label, chronological holdout metrics, actual/predicted plot and the explicit admissions-per-staff assumption.
3. Download its labeled example CSV, select it and run again to demonstrate actual upload validation and computation. Export JSON.
4. Open T10, enter a short diabetes or cardiac text, run and expand prediction, confusion matrix and cluster tables. T11 shows source mentions; T12 shows query ranking and an ambiguous/recognized MS context.
5. Run T13 and compare PCA/Isomap, then T15 to inspect held-out BMI metrics and standardized coefficients with the association caveat.
6. Open MRI matching studio, keep central nearby FLAIR slices and run SIFT/RANSAC. Return to T5 for the compact CNN demonstration if time permits.
7. Show the canonical notebook's T1–T15 sections and this report's test outcomes. Keep the server terminal open during the demonstration.
