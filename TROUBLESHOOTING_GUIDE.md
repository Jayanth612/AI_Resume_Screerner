# Troubleshooting Guide

## Common Issues & Solutions

### Issue 1: "No /Root object! - Is this really a PDF?"

**Symptom:**
```
PDF extraction error: No /Root object! - Is this really a PDF?
Syntax Error: Couldn't find trailer dictionary
```

**Cause:** Corrupted or malformed PDF file

**Solutions:**

1. **Re-save the PDF:**
   - Open in Adobe Acrobat or PDF reader
   - File → Save As → New file
   - Upload the new file

2. **Convert the PDF:**
   - Use online tools: smallpdf.com, ilovepdf.com
   - Convert to PDF again
   - This often fixes corruption

3. **Check file integrity:**
   - Ensure file downloaded completely
   - Check file size (should be > 10 KB)
   - Try opening in multiple PDF readers

**Prevention:**
- The new validation system will catch these early
- Users will get clear error messages
- No wasted processing time

### Issue 2: Quality Gate Failures

**Symptom:**
```
[QG] grammar=0.07 semantic=0.45 section=0.21 discourse=0.22
Resume failed quality gate with score 0.32
```

**Cause:** Resume has poor quality indicators:
- Low grammar score (< 0.20)
- Weak sentence structure (< 0.50)
- Too many fragments (> 0.60)
- Overall quality below threshold (< 0.45)

**This is NOT a bug** - it's working as designed to filter low-quality resumes.

**What it means:**
- Resume has significant grammar issues
- Sentences are poorly structured
- Many incomplete sentences
- Overall unprofessional presentation

**Solutions:**

1. **For legitimate resumes:**
   - May be OCR errors causing grammar issues
   - Try re-scanning at higher quality
   - Or manually type key sections

2. **For actual low-quality resumes:**
   - This is correct behavior
   - System is protecting you from bad candidates
   - Review the error message for specific issues

3. **To adjust thresholds (if needed):**
   Edit `backend/app/pipeline/quality_gate.py`:
   ```python
   # Lower thresholds if too strict
   if grammar_score < 0.15:  # Was 0.20
   if semantic_role_score < 0.40:  # Was 0.50
   ```

### Issue 3: OCR Taking Too Long

**Symptom:**
```
[Ingestion] Running OCR on 5 pages...
(Takes 5+ minutes)
```

**Cause:** Image-based PDF with multiple pages

**Solutions:**

1. **Pre-process PDFs (Recommended):**
   - Use online OCR tools before uploading
   - smallpdf.com → OCR PDF
   - ilovepdf.com → OCR PDF
   - This converts image to text PDF

2. **Reduce batch size:**
   - Upload 5-10 resumes at a time
   - Wait for completion before next batch

3. **Use cloud OCR (Production):**
   ```bash
   pip install google-cloud-vision
   ```
   - 10-100x faster than Tesseract
   - Better accuracy
   - Costs ~$1.50 per 1000 pages

### Issue 4: High Memory Usage

**Symptom:**
- System becomes slow
- Memory at 90%+
- Browser tabs crash

**Cause:** 4 workers processing simultaneously

**Solutions:**

1. **Reduce workers:**
   Edit `backend/app/routers/upload.py`:
   ```python
   max_workers = 2  # Instead of 4
   ```

2. **Close other applications:**
   - Close browser tabs
   - Close other memory-intensive apps

3. **Upgrade RAM:**
   - 8 GB minimum recommended
   - 16 GB ideal for smooth operation

### Issue 5: "Too Many Open Files"

**Symptom:**
```
OSError: [Errno 24] Too many open files
```

**Cause:** System file descriptor limit reached

**Solutions:**

1. **Reduce workers:**
   ```python
   max_workers = 2  # In upload.py
   ```

2. **Increase system limit (Windows):**
   - Usually not an issue on Windows
   - Restart system if occurs

3. **Process in smaller batches:**
   - Upload 5-10 resumes at a time

### Issue 6: Tesseract Not Found

**Symptom:**
```
tesseract is not installed or it's not in your PATH
```

**Cause:** Tesseract OCR not installed or not in PATH

**Solutions:**

1. **Install Tesseract:**
   - Download: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to: `C:\Program Files\Tesseract-OCR`
   - Check "Add to PATH" during installation

2. **Add to PATH manually:**
   - System Properties → Environment Variables
   - Edit "Path" variable
   - Add: `C:\Program Files\Tesseract-OCR`
   - Restart terminal

3. **Verify installation:**
   ```bash
   tesseract --version
   ```

### Issue 7: Processing Stuck

**Symptom:**
- Resume shows "PROCESSING" for 10+ minutes
- No console output

**Possible Causes:**
1. Very large PDF (> 50 pages)
2. OCR on high-resolution images
3. System resource exhaustion

**Solutions:**

1. **Check console logs:**
   - Look for errors or warnings
   - Check which stage is stuck

2. **Restart backend:**
   ```bash
   Ctrl+C
   uvicorn app.main:app --reload
   ```

3. **Delete stuck resume:**
   - Use frontend delete button
   - Or delete from database

4. **Reduce file size:**
   - Compress PDF before uploading
   - Remove unnecessary pages

## Performance Optimization Tips

### For Fastest Processing

1. **Use text-based PDFs:**
   - 10x faster than image PDFs
   - No OCR needed

2. **Batch size:**
   - 10-15 resumes optimal
   - Smaller batches = faster feedback

3. **Pre-process images:**
   - Convert image PDFs to text PDFs
   - Use online OCR tools

4. **Monitor resources:**
   - CPU should be 80-100%
   - Memory should be < 80%

### For Best Quality

1. **High-quality PDFs:**
   - Not corrupted
   - Clear text
   - Proper formatting

2. **Proper resume format:**
   - Clear sections
   - Good grammar
   - Complete sentences

3. **Reasonable file size:**
   - 100 KB - 2 MB ideal
   - < 10 MB maximum

## Getting Help

### Check Logs
```bash
# Backend console shows detailed processing info
[Ingestion] Extracted 2422 chars from text-based PDF
[QG] grammar=0.26 semantic=0.5 section=0.58
```

### Common Log Messages

**Good:**
```
[Info] Resume_123: 2 pages, text-based
Finished processing Resume_123
```

**Warning:**
```
[Ingestion] No text found, attempting OCR...
Resume failed quality gate with score 0.32
```

**Error:**
```
PDF extraction error: No /Root object!
ERROR in Resume_123: Resume contains no extractable text
```

### Documentation

- `PERFORMANCE_RESULTS.md` - Current performance analysis
- `OPTIMIZATION_SUMMARY.md` - What was optimized
- `QUICK_REFERENCE.md` - Quick reference guide

## Summary

Most issues are related to:
1. **Corrupted PDFs** - Re-save or convert
2. **Image PDFs** - Pre-process with OCR
3. **Low quality resumes** - System working correctly
4. **Resource limits** - Reduce workers or batch size

The optimization is working! You're now processing 4 resumes in parallel with 3x faster OCR.
