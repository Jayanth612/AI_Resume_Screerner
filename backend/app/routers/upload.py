from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from typing import List
import uuid
import os

from sqlalchemy.orm import Session
from fastapi import Form
from app.database import get_db
from app.models.resume import Resume
from app.workers.resume_worker import process_resume_async
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

# Use ThreadPoolExecutor with more workers for I/O and CPU-bound tasks
# ThreadPoolExecutor works better with SQLAlchemy sessions
max_workers = min(multiprocessing.cpu_count(), 8)  # Use CPU cores but cap at 8
executor = ThreadPoolExecutor(max_workers=max_workers)



router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

os.makedirs(UPLOAD_DIR, exist_ok=True)


def is_allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


@router.post("/resumes/upload")
async def upload_resumes(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    responses = []

    for file in files:

        # ---------- File type validation ----------
        if not file.filename or not is_allowed_file(file.filename):
            responses.append({
                "filename": file.filename,
                "status": "REJECTED",
                "reason": "Unsupported file type"
            })
            continue

        resume_id = f"RES_{uuid.uuid4().hex[:8].upper()}"
        file_path = os.path.join(UPLOAD_DIR, f"{resume_id}_{file.filename}")

        # ---------- Save file safely ----------
        try:
            content = await file.read()
            file.file.seek(0)

            if not content:
                raise ValueError("Empty file")
            
            # ---------- File size validation ----------
            if len(content) > MAX_FILE_SIZE:
                responses.append({
                    "filename": file.filename,
                    "status": "REJECTED",
                    "reason": f"File too large (max 10MB, got {len(content) / 1024 / 1024:.2f}MB)"
                })
                continue

            with open(file_path, "wb") as f:
                f.write(content)

        except Exception:
            responses.append({
                "filename": file.filename,
                "status": "REJECTED",
                "reason": "Corrupt or unreadable file"
            })
            continue

        # ---------- DB entry ----------
        try:
            resume = Resume(
                resume_id=resume_id,
                status="PROCESSING"  # MUST MATCH ENUM EXACTLY
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)  # 🔥 VERY IMPORTANT
        except Exception as db_error:
            db.rollback()
            responses.append({
                "filename": file.filename,
                "status": "ERROR",
                "reason": "Database error"
            })
            continue

        # ---------- Trigger async pipeline ----------
        try:
            executor.submit(
                process_resume_async,
                resume_id,
                file_path
            )
            
            responses.append({
                "resume_id": resume_id,
                "status": "ACCEPTED"
            })
        except Exception:
            resume.status = "ERROR"
            db.commit()
            responses.append({
                "filename": file.filename,
                "status": "ERROR",
                "reason": "Failed to start processing"
            })

    return {
        "message": "UPLOAD_COMPLETE",
        "results": responses
    }


@router.post("/analyze")
async def analyze_resumes(
    files: List[UploadFile] = File(...),
    jd_text: str = Form(...),
    db: Session = Depends(get_db)
):
    results = []
    
    # Generate hash of JD for grouping
    import hashlib
    jd_hash = hashlib.md5(jd_text.encode()).hexdigest()[:16]

    for file in files:
        # Validate file type
        if not file.filename or not is_allowed_file(file.filename):
            results.append({
                "filename": file.filename,
                "status": "REJECTED",
                "reason": "Unsupported file type"
            })
            continue

        try:
            content = await file.read()
            
            # Validate file size
            if len(content) > MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "status": "REJECTED",
                    "reason": f"File too large (max 10MB, got {len(content) / 1024 / 1024:.2f}MB)"
                })
                continue
            
            if not content:
                results.append({
                    "filename": file.filename,
                    "status": "REJECTED",
                    "reason": "Empty file"
                })
                continue

            # Quick name extraction for ID generation
            from app.utils.name_extractor import extract_candidate_name, generate_resume_id
            from app.pipeline.ingestion import extract_text_from_pdf
            
            # Save temp file to extract name
            temp_path = os.path.join(UPLOAD_DIR, f"temp_{uuid.uuid4().hex[:8]}.pdf")
            with open(temp_path, "wb") as f:
                f.write(content)
            
            try:
                # Extract text and name
                text = extract_text_from_pdf(temp_path)
                candidate_name = extract_candidate_name(text) if text else "Unknown"
                resume_id = generate_resume_id(candidate_name)
            except Exception:
                # Fallback to old format if extraction fails
                candidate_name = "Unknown"
                resume_id = f"RES_{uuid.uuid4().hex[:8].upper()}"
            
            # Rename to final path
            file_path = os.path.join(UPLOAD_DIR, f"{resume_id}.pdf")
            os.rename(temp_path, file_path)

            resume = Resume(
                resume_id=resume_id,
                candidate_name=candidate_name,
                jd_hash=jd_hash,
                status="PROCESSING"
            )
            db.add(resume)
            db.commit()

            # Background processing
            executor.submit(process_resume_background, resume_id, file_path, jd_text)

            results.append({
                "resume_id": resume_id,
                "candidate_name": candidate_name,
                "jd_hash": jd_hash,
                "status": "PROCESSING"
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "ERROR",
                "reason": str(e)
            })

    return {
        "message": "Processing started",
        "resumes": results
    }

def process_resume_background(resume_id, file_path, jd_text):
    from app.database import SessionLocal
    from app.utils.pdf_validator import validate_pdf_file, get_pdf_info
    
    db = SessionLocal()
    print(f"Started processing {resume_id}")

    try:
        # Validate PDF before processing
        is_valid, error_msg = validate_pdf_file(file_path)
        if not is_valid:
            print(f"[Validation] {resume_id} failed: {error_msg}")
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if resume:
                resume.status = "ERROR"
                resume.error_message = f"Invalid PDF: {error_msg}"
                db.commit()
            return
        
        # Get PDF info for logging
        pdf_info = get_pdf_info(file_path)
        print(f"[Info] {resume_id}: {pdf_info['page_count']} pages, "
              f"{'text-based' if pdf_info['has_text'] else 'image-based (OCR needed)'}")
        
        if not pdf_info['has_text'] and pdf_info['estimated_ocr_time'] > 0:
            print(f"[Info] Estimated OCR time: ~{pdf_info['estimated_ocr_time']}s")
        
        from app.pipeline.jd_intelligence import jd_stage
        jd_data = jd_stage(jd_text)

        process_resume_async(resume_id, file_path, jd_data)

    except Exception as e:
        print(f"ERROR in background processing {resume_id}: {e}")
        resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
        if resume:
            resume.status = "ERROR"
            resume.error_message = str(e)
            db.commit()
        
        # Clean up file on error
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
    finally:
        print(f"Finished processing {resume_id}")
        db.close()
