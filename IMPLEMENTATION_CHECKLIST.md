# Submission implementation checklist

- [x] Audit tracked files and uncommitted datasets; preserve MRI assets and original notebook content.
- [x] Inspect all 58 original notebook cells and existing API/core/frontend code.
- [x] Add shared, validated T7–T15 computations and deterministic, labeled example datasets.
- [x] Extend notebook in place with portable paths and reproducible tutorial sections.
- [x] Connect dashboard, uploads, tables, plots and MRI workflows to backend.
- [x] Verify automated analysis/API tests, real MRI pipeline, CNN and notebook execution.
- [x] Record startup commands, completion matrix and remaining limitations.

Audit: no separate syllabus or non-MRI datasets found. Use mission syllabus wording. Eight MRI cases, six labeled. Original notebook has repeated T5 headings for complementary SIFT and CNN sections, not duplicate implementations. Existing root index.html is a notebook export and will be preserved. Untracked BraTS2020 and partial archive must remain untouched. Highest risks: TensorFlow availability, original absolute paths, CPU CNN training cost, sparse or malformed uploaded datasets.

Final verification: 13 automated tests passed; all 79 notebook cells (41 code) executed with one CNN epoch and no cell errors. All 15 live HTTP tutorial routes, original CNN scripts, compact CNN HTTP inference and JavaScript frontend flows passed. Executed notebook outputs retained in the canonical notebook. Visual browser checks were unavailable and remain explicitly unverified; see SUBMISSION_REPORT.md.
