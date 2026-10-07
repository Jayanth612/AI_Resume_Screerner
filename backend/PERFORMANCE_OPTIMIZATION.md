# Performance Optimization Guide

## Changes Made

### 1. Increased Parallel Processing (upload.py)
- Changed from 2 workers to CPU-based workers (up to 8)
- Now processes multiple resumes simultaneously

### 2. Optimized OCR Processing (ingestion.py)
- Reduced DPI from 300 to 200 (3x faster, still readable)
- Added parallel page processing for multi-page PDFs
- Uses optimized Tesseract config (PSM 6 mode)
- Changed image format to JPEG for faster conversion

## Expected Performance Improvements

### Before:
- 2 resumes at a time
- 300 DPI OCR (slow)
- Sequential page processing
- ~5-10 minutes per resume with OCR

### After:
- 4-8 resumes at a time (depending on CPU cores)
- 200 DPI OCR (3x faster)
- Parallel page processing
- ~2-4 minutes per resume with OCR

### For 20 resumes:
- Before: 100-200 minutes (1.5-3 hours)
- After: 25-50 minutes (0.5-1 hour)

## Additional Optimization Options

### Option 1: Use ProcessPoolExecutor for CPU-Bound Tasks
Replace ThreadPoolExecutor with ProcessPoolExecutor in upload.py:

```python
from concurrent.futures import ProcessPoolExecutor
executor = ProcessPoolExecutor(max_workers=min(multiprocessing.cpu_count(), 6))
```

Benefits: Better for CPU-intensive tasks (OCR, NLP)
Drawback: Higher memory usage

### Option 2: Add OCR Caching
Cache OCR results to avoid re-processing same files:

```python
import hashlib
import json

def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def extract_text_with_ocr_cached(file_path: str) -> str:
    cache_dir = "ocr_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    file_hash = get_file_hash(file_path)
    cache_file = os.path.join(cache_dir, f"{file_hash}.txt")
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    text = extract_text_with_ocr(file_path)
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return text
```

### Option 3: Skip OCR for Large Batches
Add a flag to skip OCR and only process text-based PDFs:

```python
ENABLE_OCR = os.getenv("ENABLE_OCR", "true").lower() == "true"

def extract_text_from_pdf(file_path: str, allow_ocr: bool = True) -> str:
    # ... existing code ...
    
    if not allow_ocr or not ENABLE_OCR:
        return text.strip() if text.strip() else ""
    
    # OCR fallback
    return extract_text_with_ocr(file_path)
```

### Option 4: Use Faster OCR Engine
Consider using EasyOCR or PaddleOCR (faster alternatives):

```bash
pip install easyocr
```

```python
def extract_text_with_easyocr(file_path: str) -> str:
    import easyocr
    from pdf2image import convert_from_path
    
    reader = easyocr.Reader(['en'], gpu=False)
    images = convert_from_path(file_path, dpi=200)
    
    text = ""
    for image in images:
        result = reader.readtext(image, detail=0)
        text += " ".join(result) + "\n"
    
    return text.strip()
```

### Option 5: Batch Processing with Queue
Implement a proper job queue system:

```bash
pip install celery redis
```

This allows:
- Better resource management
- Retry failed jobs
- Monitor progress
- Distribute across multiple machines

## Monitoring Performance

Add timing logs to track bottlenecks:

```python
import time

def process_resume_async(resume_id: str, file_path: str, jd_data: dict = None):
    start_time = time.time()
    stage_times = {}
    
    # ... existing code ...
    
    stage_start = time.time()
    data = ingestion_stage(file_path)
    stage_times['ingestion'] = time.time() - stage_start
    
    # ... repeat for each stage ...
    
    total_time = time.time() - start_time
    print(f"[TIMING] {resume_id} completed in {total_time:.2f}s")
    print(f"[TIMING] Stage breakdown: {stage_times}")
```

## Recommended Next Steps

1. Test current changes with 5-10 resumes
2. Monitor CPU and memory usage
3. If still slow, implement Option 1 (ProcessPoolExecutor)
4. If processing same files repeatedly, add Option 2 (caching)
5. For production, consider Option 5 (Celery queue)
