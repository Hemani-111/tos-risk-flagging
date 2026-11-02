import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.core.config import settings
from app.ml.model_loader import model_loader
from app.services.clause_segmenter import ClauseSegmenter
from app.services.document_parser import (
    DocumentLimitError,
    DocumentParsingError,
    UnsupportedScannedPDFError,
    get_parser,
)
from app.services.predictor import Predictor
from app.services.risk_aggregator import RiskAggregator

logger = logging.getLogger(__name__)

router = APIRouter()
segmenter = ClauseSegmenter()
predictor = Predictor()
aggregator = RiskAggregator()
analysis_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSES)


class ClauseResponse(BaseModel):
    id: str
    text: str
    label: str
    section: str | None = None
    startOffset: int
    endOffset: int


class AnalysisResponse(BaseModel):
    id: str
    filename: str
    totalClauses: int
    safeCount: int
    neutralCount: int
    riskyCount: int
    safePercentage: float
    neutralPercentage: float
    riskyPercentage: float
    overallAssessment: str
    modelVersion: str
    schemaVersion: str
    warnings: List[str]
    clauses: List[ClauseResponse]
    riskyClauses: List[ClauseResponse]


class TextAnalysisRequest(BaseModel):
    text: str = Field(max_length=2_000_000)
    filename: Optional[str] = Field(default="pasted-text.txt", max_length=255)


def _run_analysis(text: str, filename: str) -> AnalysisResponse:
    if not text.strip():
        raise HTTPException(status_code=422, detail="The document contains no extractable text.")
    if len(text) > settings.MAX_EXTRACTED_CHARS:
        raise HTTPException(status_code=413, detail="Extracted text exceeds the configured limit.")
    clauses = segmenter.segment(text)
    if not clauses:
        raise HTTPException(status_code=422, detail="No analyzable clauses were found in the document.")
    if len(clauses) > settings.MAX_CLAUSES:
        raise HTTPException(status_code=413, detail="Document exceeds the configured clause limit.")

    clause_results = predictor.predict(clauses)
    summary = aggregator.aggregate(clause_results)
    package = model_loader.package_info()
    return AnalysisResponse(
        id=str(uuid.uuid4()),
        filename=filename,
        totalClauses=summary["totalClauses"],
        safeCount=summary["safeCount"],
        neutralCount=summary["neutralCount"],
        riskyCount=summary["riskyCount"],
        safePercentage=summary["safePercentage"],
        neutralPercentage=summary["neutralPercentage"],
        riskyPercentage=summary["riskyPercentage"],
        overallAssessment=summary["overallAssessment"],
        modelVersion=package["modelVersion"],
        schemaVersion=package["schemaVersion"],
        warnings=package["warnings"],
        clauses=[ClauseResponse(**item) for item in clause_results],
        riskyClauses=[ClauseResponse(**item) for item in clause_results if item["label"] == "Risky"],
    )


@router.post("/documents/analyze", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")
    ext = Path(file.filename).suffix.lower()
    allowed = {e.strip().lower() for e in settings.UPLOAD_ALLOWED_EXTENSIONS_STR.split(",")}
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext or '(none)'}. Allowed: {', '.join(sorted(allowed))}",
        )

    temp_path = None
    total_bytes = 0
    try:
        with tempfile.NamedTemporaryFile(prefix="tos-review-", suffix=ext, delete=False) as temp_file:
            temp_path = temp_file.name
            while chunk := await file.read(settings.UPLOAD_READ_CHUNK_BYTES):
                total_bytes += len(chunk)
                if total_bytes > settings.UPLOAD_MAX_SIZE:
                    raise HTTPException(status_code=413, detail="File exceeds the upload size limit.")
                temp_file.write(chunk)

        async with analysis_semaphore:
            try:
                parser = get_parser(ext)
                extracted_text = await run_in_threadpool(parser.parse, temp_path)
            except UnsupportedScannedPDFError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            except DocumentLimitError as exc:
                raise HTTPException(status_code=413, detail=str(exc)) from exc
            except DocumentParsingError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            return await run_in_threadpool(_run_analysis, extracted_text, Path(file.filename).name)
    except HTTPException:
        raise
    except Exception as exc:
        # Do not include uploaded text, extracted text, or file contents in logs.
        logger.exception("Document analysis failed")
        raise HTTPException(status_code=500, detail="Document analysis failed. Please try another file.") from exc
    finally:
        await file.close()
        if temp_path:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
            except OSError:
                logger.warning("Temporary upload cleanup failed")


@router.post("/documents/analyze-text", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    cleaned = request.text.replace("\r\n", "\n").replace("\r", "\n")
    async with analysis_semaphore:
        return await run_in_threadpool(_run_analysis, cleaned, request.filename or "pasted-text.txt")
