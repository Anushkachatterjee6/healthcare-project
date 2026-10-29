"""
HER Biomedical Image Tutorials — FastAPI backend.

Serves the existing tutorial UI and the T5 Image Analysis (SIFT + RANSAC) API.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from her_core.io import (  # noqa: E402
    default_data_root,
    discover_cases,
    get_slice,
    list_modalities,
    load_case_modality,
)
from her_core.sift_ransac import analyze_mri_sift_ransac  # noqa: E402

FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title="HER Biomedical Image Analysis",
    description="T1–T6 biomedical MRI tutorials with SIFT + RANSAC image analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory volume cache so repeated analysis clicks stay responsive.
_VOLUME_CACHE: dict[tuple[str, str], Any] = {}


class SiftRansacRequest(BaseModel):
    case_id: str = Field(..., description="Patient/case folder name")
    modality: str = Field("flair", description="MRI modality, e.g. flair, t1, t2")
    slice1: int = Field(..., ge=0, description="Index of first axial slice")
    slice2: int = Field(..., ge=0, description="Index of second axial slice")
    data_root: str | None = Field(
        None, description="Optional override for BraTS-style dataset root"
    )


def _get_case(case_id: str, data_root: str | None = None) -> dict:
    cases = discover_cases(data_root or default_data_root())
    for case in cases:
        if case["case_id"] == case_id:
            return case
    raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")


def _load_volume_cached(case: dict, modality: str):
    key = (case["case_id"], modality.lower())
    if key not in _VOLUME_CACHE:
        volume, _, path = load_case_modality(case, modality.lower())
        _VOLUME_CACHE[key] = {"volume": volume, "path": str(path)}
    return _VOLUME_CACHE[key]


@app.get("/api/health")
def health():
    root = default_data_root()
    cases = discover_cases(root)
    return {
        "status": "ok",
        "data_root": str(root),
        "cases_found": len(cases),
    }


@app.get("/api/cases")
def api_cases(data_root: str | None = None):
    cases = discover_cases(data_root or default_data_root())
    payload = []
    for case in cases:
        modalities = list_modalities(case)
        depth = None
        # Prefer flair for default depth metadata.
        preferred = "flair" if "flair" in modalities else (modalities[0] if modalities else None)
        if preferred:
            try:
                cached = _load_volume_cached(case, preferred)
                depth = int(cached["volume"].shape[2])
            except Exception:
                depth = None
        payload.append(
            {
                "case_id": case["case_id"],
                "modalities": modalities,
                "default_modality": preferred,
                "num_slices": depth,
            }
        )
    return {"cases": payload, "data_root": str(data_root or default_data_root())}


@app.get("/api/cases/{case_id}/meta")
def api_case_meta(case_id: str, modality: str = "flair", data_root: str | None = None):
    case = _get_case(case_id, data_root)
    modalities = list_modalities(case)
    if modality not in modalities:
        raise HTTPException(
            status_code=404,
            detail=f"Modality '{modality}' not available. Options: {modalities}",
        )
    cached = _load_volume_cached(case, modality)
    vol = cached["volume"]
    return {
        "case_id": case_id,
        "modality": modality,
        "shape": list(vol.shape),
        "num_slices": int(vol.shape[2]),
        "modalities": modalities,
        "path": cached["path"],
    }


@app.post("/api/image-analysis/sift-ransac")
def api_sift_ransac(body: SiftRansacRequest):
    case = _get_case(body.case_id, body.data_root)
    modalities = list_modalities(case)
    modality = body.modality.lower()
    if modality not in modalities:
        raise HTTPException(
            status_code=404,
            detail=f"Modality '{modality}' not available for {body.case_id}. Options: {modalities}",
        )

    cached = _load_volume_cached(case, modality)
    volume = cached["volume"]
    n_slices = int(volume.shape[2])

    if body.slice1 >= n_slices or body.slice2 >= n_slices:
        raise HTTPException(
            status_code=400,
            detail=f"Slice indices out of range. Valid range: 0–{n_slices - 1}",
        )

    if body.slice1 == body.slice2:
        raise HTTPException(
            status_code=400,
            detail="Slice 1 and Slice 2 must be different for meaningful matching.",
        )

    slice_a = get_slice(volume, body.slice1)
    slice_b = get_slice(volume, body.slice2)

    analysis = analyze_mri_sift_ransac(slice_a, slice_b, return_base64=True)

    return {
        "case_id": body.case_id,
        "modality": modality,
        "slice1": body.slice1,
        "slice2": body.slice2,
        "num_slices": n_slices,
        "keypoints_image1": analysis["keypoints_image1"],
        "keypoints_image2": analysis["keypoints_image2"],
        "good_matches": analysis["good_matches"],
        "ransac_inliers": analysis["ransac_inliers"],
        "ransac_outliers": analysis["ransac_outliers"],
        "inlier_ratio": analysis["inlier_ratio"],
        "homography_found": analysis["homography_found"],
        "success": analysis["success"],
        "message": analysis["message"],
        "original_image1": analysis["original_image1"],
        "original_image2": analysis["original_image2"],
        "sift_visualization_1": analysis["sift_visualization_1"],
        "sift_visualization_2": analysis["sift_visualization_2"],
        "matches_visualization": analysis["matches_visualization"],
        "ransac_visualization": analysis["ransac_visualization"],
    }


@app.get("/")
def serve_home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/image-analysis")
def serve_image_analysis():
    return FileResponse(FRONTEND_DIR / "image-analysis.html")


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
