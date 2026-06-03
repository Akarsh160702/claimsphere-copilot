import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.tools.blob_storage import BlobStorageClient
from backend.models.document import DocumentUploadResponse, DocumentType

router = APIRouter(prefix="/documents", tags=["Documents"])
blob_client = BlobStorageClient()

ALLOWED_TYPES = {
    "application/pdf", "image/jpeg", "image/jpg",
    "image/png", "application/octet-stream",
}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    claim_id: str = Form(...),
    doc_type: DocumentType = Form(DocumentType.UNKNOWN),
    file: UploadFile = File(...),
):
    """Upload a document for a claim to Azure Blob Storage."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, JPEG, PNG"
        )

    max_size = 10 * 1024 * 1024  # 10MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    doc_id = str(uuid.uuid4())
    blob_url = await blob_client.upload_document(
        file_bytes=contents,
        filename=file.filename,
        claim_id=claim_id,
        content_type=file.content_type,
    )

    return DocumentUploadResponse(
        doc_id=doc_id,
        blob_url=blob_url,
        message=f"Document uploaded successfully. Type: {doc_type.value}",
    )


@router.get("/{claim_id}", response_model=list)
async def list_documents(claim_id: str):
    """List all documents for a claim."""
    from backend.api.claims import _processing_contexts
    ctx = _processing_contexts.get(claim_id)
    if ctx:
        return ctx.extracted_documents
    return []
