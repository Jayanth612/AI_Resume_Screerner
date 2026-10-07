"""
Simple script to test resume processing performance
"""
import time
import requests
from pathlib import Path

API_URL = "http://localhost:8000/api"

def test_batch_upload():
    """Test uploading multiple resumes"""
    
    # Find all PDF files in uploads directory
    upload_dir = Path("uploads")
    pdf_files = list(upload_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in uploads directory")
        return
    
    # Take first 5 files for testing
    test_files = pdf_files[:5]
    
    print(f"Testing with {len(test_files)} resumes...")
    print("Files:", [f.name for f in test_files])
    
    # Prepare files for upload
    files = []
    for pdf_file in test_files:
        files.append(('files', (pdf_file.name, open(pdf_file, 'rb'), 'application/pdf')))
    
    # Job description
    jd_text = """
    We are looking for a Software Engineer with:
    - Bachelor's degree in Computer Science
    - 3+ years of Python experience
    - Experience with SQL databases
    - Strong problem-solving skills
    """
    
    data = {'jd_text': jd_text}
    
    print("\nStarting upload...")
    start_time = time.time()
    
    try:
        response = requests.post(f"{API_URL}/analyze", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nUpload successful!")
            print(f"Resumes submitted: {len(result.get('resumes', []))}")
            
            # Close file handles
            for _, (_, file_obj, _) in files:
                file_obj.close()
            
            # Wait for processing
            print("\nWaiting for processing to complete...")
            resume_ids = [r['resume_id'] for r in result.get('resumes', [])]
            
            completed = set()
            while len(completed) < len(resume_ids):
                time.sleep(2)
                
                # Check status of each resume
                for resume_id in resume_ids:
                    if resume_id not in completed:
                        status_response = requests.get(f"{API_URL}/resumes/status/{resume_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status')
                            
                            if status in ['PROCESSED', 'ERROR', 'INVALID_RESUME']:
                                completed.add(resume_id)
                                elapsed = time.time() - start_time
                                print(f"  {resume_id}: {status} (after {elapsed:.1f}s)")
            
            total_time = time.time() - start_time
            print(f"\n✓ All resumes processed in {total_time:.1f} seconds")
            print(f"  Average: {total_time / len(resume_ids):.1f}s per resume")
            
        else:
            print(f"Upload failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Make sure to close all file handles
        for _, (_, file_obj, _) in files:
            try:
                file_obj.close()
            except:
                pass

if __name__ == "__main__":
    print("Resume Processing Performance Test")
    print("=" * 50)
    test_batch_upload()
