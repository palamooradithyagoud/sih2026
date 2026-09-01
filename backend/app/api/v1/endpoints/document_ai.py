import os
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.groq_extractor import (
    groq_extractor,
    extract_text_from_file,
    SAMPLE_INVESTIGATION_DOCUMENTS,
)
from app.services.investigation_service import investigation_service
from app.db.postgres import check_postgres_connection
from app.db.neo4j import check_neo4j_connection

router = APIRouter()


class DocumentTextExtractRequest(BaseModel):
    document_text: str = Field(..., description="Raw text of the FIR, charge sheet, or interrogation report")
    document_name: str = Field("Investigation_Docket.txt", description="Name of the document")
    document_type: str = Field("FIR", description="Document type: FIR, Charge Sheet, Interrogation, CDR, Bank Statement")
    case_id: Optional[str] = Field(None, description="Optional target case ID. If omitted, will link or create case.")
    groq_api_key: Optional[str] = Field(None, description="Optional user-provided Groq API Key")


@router.get("/integrations/status", summary="Get status of Groq API, Supabase Postgres, and Neo4j")
def get_integrations_status() -> Dict[str, Any]:
    """Returns connectivity and configuration status of all database and AI integrations."""
    pg_status = check_postgres_connection()
    neo_status = check_neo4j_connection()
    
    groq_configured = bool(settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY"))

    return {
        "groq": {
            "configured": groq_configured,
            "model": settings.GROQ_MODEL or "llama-3.3-70b-versatile",
            "provider": "Groq Cloud Llama-3.3 High-Speed Inference",
            "ready": True,
        },
        "postgres_supabase": {
            "connected": pg_status.get("connected", False),
            "is_supabase": pg_status.get("is_supabase", False),
            "target": pg_status.get("url", "localhost:5432"),
            "details": pg_status,
        },
        "neo4j": {
            "connected": neo_status,
            "uri": settings.NEO4J_URI,
        },
    }


@router.get("/documents/samples", summary="List available realistic sample investigation dockets")
def list_sample_documents() -> List[Dict[str, Any]]:
    """Returns metadata for pre-loaded realistic crime dockets for instant 1-click AI extraction."""
    samples = []
    for key, doc in SAMPLE_INVESTIGATION_DOCUMENTS.items():
        samples.append({
            "id": doc["id"],
            "title": doc["title"],
            "category": doc["category"],
            "station": doc["station"],
            "preview": doc["text"][:280] + "...",
        })
    return samples


@router.post("/documents/upload-and-extract", summary="Upload document file (PDF/DOCX/TXT) and synthesize Knowledge Graph with Groq")
async def upload_and_extract_document(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    document_name: Optional[str] = Form(None),
    document_type: str = Form("FIR"),
    case_id: Optional[str] = Form(None),
    groq_api_key: Optional[str] = Form(None),
):
    """
    Extracts criminal entities and creates connected knowledge graph from an uploaded document
    (PDF, DOCX, TXT) or raw text using Groq LLM (Llama-3.3-70B).
    """
    doc_text = ""
    actual_filename = document_name or "Uploaded_Investigation_Docket.txt"

    if file:
        actual_filename = file.filename or actual_filename
        file_bytes = await file.read()
        doc_text = extract_text_from_file(file_bytes, actual_filename)
    elif raw_text:
        doc_text = raw_text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either a document file (PDF/DOCX/TXT) or raw_text string.",
        )

    if not doc_text or len(doc_text.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract readable text from document. Ensure file is not empty.",
        )

    clean_case_id = case_id.strip() if case_id and case_id.strip() and case_id.strip() != "undefined" else None

    # 1. Run Groq NER & Knowledge Graph Synthesis
    extraction = groq_extractor.extract_document_intelligence(
        document_text=doc_text,
        document_name=actual_filename,
        api_key=groq_api_key,
    )

    # 2. Ingest into InvestigationService (Neo4j + PostgreSQL)
    return investigation_service.ingest_extracted_document(
        case_id=clean_case_id,
        extraction_data=extraction,
        document_name=actual_filename,
        document_type=document_type,
        raw_text=doc_text,
    )


@router.post("/documents/extract-text", summary="Extract entities and synthesize Knowledge Graph from raw text")
def extract_from_text(payload: DocumentTextExtractRequest):
    """Extracts entities and Knowledge Graph topology from raw document text string."""
    clean_case_id = payload.case_id.strip() if payload.case_id and payload.case_id.strip() and payload.case_id.strip() != "undefined" else None

    extraction = groq_extractor.extract_document_intelligence(
        document_text=payload.document_text,
        document_name=payload.document_name,
        api_key=payload.groq_api_key,
    )

    return investigation_service.ingest_extracted_document(
        case_id=clean_case_id,
        extraction_data=extraction,
        document_name=payload.document_name,
        document_type=payload.document_type,
        raw_text=payload.document_text,
    )


@router.post("/documents/sample-extract/{sample_id}", summary="1-Click Extract sample realistic investigation docket")
def extract_sample_document(
    sample_id: str,
    case_id: Optional[str] = None,
    groq_api_key: Optional[str] = None,
):
    """Extracts and graphs a pre-loaded realistic crime docket."""
    if sample_id not in SAMPLE_INVESTIGATION_DOCUMENTS:
        raise HTTPException(status_code=404, detail="Sample document not found")

    clean_case_id = case_id.strip() if case_id and case_id.strip() and case_id.strip() != "undefined" else None

    sample = SAMPLE_INVESTIGATION_DOCUMENTS[sample_id]
    extraction = groq_extractor.extract_document_intelligence(
        document_text=sample["text"],
        document_name=f"{sample['title']}.pdf",
        api_key=groq_api_key,
    )

    return investigation_service.ingest_extracted_document(
        case_id=clean_case_id,
        extraction_data=extraction,
        document_name=f"{sample['title']}.pdf",
        document_type=sample["category"],
        raw_text=sample["text"],
    )
