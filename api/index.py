import requests
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from fuzzywuzzy import fuzz
import re
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SRMIST Syllabus Extractor Portal")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache for PDF to avoid redownloading
pdf_cache = {}

def download_pdf(url):
    """Load PDF from local file with caching - INSTANT LOADING!"""
    if url in pdf_cache:
        logger.info("Using cached PDF")
        return pdf_cache[url]
    
    # Use local PDF file instead of downloading
    local_pdf_path = os.path.join(os.path.dirname(__file__), "main pdf", "computing-programmes-syllabus-2021.pdf")
    
    logger.info(f"Checking local PDF path: {local_pdf_path}")
    if os.path.exists(local_pdf_path):
        logger.info("✅ Loading PDF from local file - INSTANT!")
        with open(local_pdf_path, 'rb') as f:
            pdf_buffer = BytesIO(f.read())
        pdf_cache[url] = pdf_buffer
        return pdf_buffer
    else:
        # Fallback to download if local file not found
        logger.info(f"Local PDF not found, downloading from {url}")
        response = requests.get(url, timeout=30)
        pdf_buffer = BytesIO(response.content)
        pdf_cache[url] = pdf_buffer
        return pdf_buffer

def parse_table_of_contents(pdf_buffer):
    """Parse the table of contents to find course codes and page numbers - ENHANCED FOR ALL PREFIXES"""
    pdf_buffer.seek(0)
    reader = PdfReader(pdf_buffer)
    toc_entries = []
    
    logger.info("Parsing table of contents for ALL course prefixes...")
    
    # Check first 15 pages for TOC (extended range for comprehensive syllabus)
    for page_num in range(min(15, len(reader.pages))):
        try:
            page = reader.pages[page_num]
            text = page.extract_text() or ""
            
            # Split into lines for easier parsing
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                # Look for ALL course code patterns: 21CSC, 21CSE, 21CSS, 21AIE, etc.
                # Pattern: 21 + 3 letters + 3 digits + optional letter
                if re.search(r'21[A-Z]{3}\d{3}[A-Z]?', line, re.IGNORECASE):
                    # Extract course code, subject name, and page number
                    course_match = re.search(r'(21[A-Z]{3}\d{3}[A-Z]?)', line, re.IGNORECASE)
                    page_match = re.search(r'\b(\d{1,3})\s*$', line)  # Page number at end
                    
                    if course_match and page_match:
                        course_code = course_match.group(1).upper()
                        page_number = int(page_match.group(1))
                        
                        # Extract subject name (text between course code and page number)
                        subject_part = line[course_match.end():page_match.start()].strip()
                        # Clean subject name: remove all types of dots and extra spaces
                        subject_name = re.sub(r'[.…·•]+', '', subject_part)  # Remove regular dots, ellipsis, and other dot chars
                        subject_name = re.sub(r'\s+', ' ', subject_name).strip()  # Clean spaces
                        
                        if subject_name:
                            toc_entries.append({
                                'course_code': course_code,
                                'subject_name': subject_name,
                                'page_number': page_number - 1  # Convert to 0-indexed
                            })
                            logger.info(f"Found: {course_code} - {subject_name} (Page {page_number})")
                            
        except Exception as e:
            logger.warning(f"Error parsing TOC page {page_num + 1}: {e}")
            continue
    
    # MANUAL OVERRIDE: Add missing courses that aren't in TOC but exist in the syllabus
    manual_entries = [
        {
            'course_code': '21CSE499T',
            'subject_name': 'Neural Network Models of Cognition',
            'page_number': 529  # Page 530 in 1-indexed, 529 in 0-indexed
        }
    ]
    
    for entry in manual_entries:
        # Check if not already found in TOC
        if not any(toc['course_code'] == entry['course_code'] for toc in toc_entries):
            toc_entries.append(entry)
            logger.info(f"MANUAL OVERRIDE: {entry['course_code']} - {entry['subject_name']} (Page {entry['page_number'] + 1})")
    
    return toc_entries

def find_actual_subject_start(pdf_buffer, toc_page, course_code):
    """Find the actual start page of the subject content - ENHANCED DETECTION"""
    pdf_buffer.seek(0)
    reader = PdfReader(pdf_buffer)
    
    logger.info(f"Finding actual start for {course_code} from TOC page {toc_page + 1}")
    
    # Check the TOC page and next few pages to find where the subject actually starts
    search_range = range(max(0, toc_page - 1), min(toc_page + 4, len(reader.pages)))
    
    for page_num in search_range:
        try:
            text = reader.pages[page_num].extract_text() or ""
            
            # Look for the course code with more specific template indicators
            if re.search(rf'{re.escape(course_code)}', text, re.IGNORECASE):
                # More specific checks for actual syllabus content
                syllabus_indicators = [
                    r'Course\s+Code.*Course\s+Name.*Course\s+Category',  # Full template header
                    r'Prerequisites.*Corequisites',  # Syllabus structure
                    r'Course\s+Objectives.*Course\s+Outcomes',  # Learning objectives
                    r'Unit\s+I.*Unit\s+II',  # Unit structure
                    rf'{re.escape(course_code)}.*Course\s+Name',  # Course code with name
                ]
                
                # Check for multiple indicators to ensure it's the actual syllabus
                matches = sum(1 for pattern in syllabus_indicators if re.search(pattern, text, re.IGNORECASE))
                
                if matches >= 2:  # At least 2 indicators for confidence
                    logger.info(f"Found actual subject start at page {page_num + 1} (confidence: {matches} indicators)")
                    return page_num
                elif matches >= 1:
                    # Single match - check if it's not a general page
                    if not re.search(r'Academic\s+Curricula|Regulations\s+\d{4}|General\s+Information', text, re.IGNORECASE):
                        logger.info(f"Found likely subject start at page {page_num + 1} (confidence: {matches} indicator)")
                        return page_num
                    
        except Exception as e:
            logger.warning(f"Error checking page {page_num + 1}: {e}")
            continue
    
    # Enhanced fallback: try to skip obvious general pages
    for page_num in search_range:
        try:
            text = reader.pages[page_num].extract_text() or ""
            if re.search(rf'{re.escape(course_code)}', text, re.IGNORECASE):
                # Skip if it's clearly a general/cover page
                if re.search(r'Academic\s+Curricula|Regulations\s+\d{4}|SRM\s+Institute|General\s+Information', text, re.IGNORECASE):
                    logger.info(f"Skipping general page at {page_num + 1}")
                    continue
                else:
                    logger.info(f"Using page {page_num + 1} as enhanced fallback")
                    return page_num
        except Exception as e:
            continue
    
    # Final fallback: use TOC page
    logger.info(f"Using TOC page {toc_page + 1} as final fallback")
    return toc_page

def find_exact_template_boundary(pdf_buffer, start_page, current_course_code):
    """Find the exact template boundary - SIMPLIFIED FOR CONSISTENCY"""
    pdf_buffer.seek(0)
    reader = PdfReader(pdf_buffer)
    
    logger.info(f"Looking for template boundary starting from page {start_page + 1}")
    logger.info(f"Current course code: {current_course_code}")
    
    # Use the SAME logic that worked for DSA - be very conservative
    # Most subjects are 2-3 pages, so let's use a fixed approach
    
    # Check next few pages for a different course code
    max_search_pages = min(start_page + 5, len(reader.pages))
    
    for page_num in range(start_page + 1, max_search_pages):
        try:
            text = reader.pages[page_num].extract_text() or ""
            
            # Look for ANY course code pattern (ALL prefixes: CSC, CSE, CSS, AIE, etc.)
            course_code_match = re.search(r'21[A-Z]{3}\d{3}[A-Z]?', text)
            
            if course_code_match:
                found_course_code = course_code_match.group(0)
                
                # If we find a DIFFERENT course code, stop here
                if found_course_code != current_course_code:
                    logger.info(f"Found different course {found_course_code} at page {page_num + 1}")
                    return page_num - 1  # Stop before the new course
            
            # Also look for clear template indicators
            if re.search(r'Course\s+Code.*Course\s+Name.*Course\s+Category', text, re.IGNORECASE):
                # Check if this has a different course code
                if course_code_match and course_code_match.group(0) != current_course_code:
                    logger.info(f"Found new course template at page {page_num + 1}")
                    return page_num - 1
                    
        except Exception as e:
            logger.warning(f"Error checking page {page_num + 1}: {e}")
            continue
    
    # DEFAULT: Use same conservative approach that worked for DSA
    # Most subjects are 2-3 pages, so add 2 pages max
    conservative_end = min(start_page + 2, len(reader.pages) - 1)
    logger.info(f"Using conservative boundary: page {conservative_end + 1} (same as DSA approach)")
    return conservative_end

def find_subject_pages_smart(pdf_buffer, subject, threshold=70):
    """Smart subject finding using table of contents and template recognition"""
    logger.info(f"Smart search for subject: {subject}")
    
    # Step 1: Parse table of contents
    toc_entries = parse_table_of_contents(pdf_buffer)
    
    if not toc_entries:
        logger.warning("No TOC entries found, falling back to fuzzy search")
        return find_subject_pages_fallback(pdf_buffer, subject, threshold)
    
    # Step 2: Find best matching subject in TOC
    best_match = None
    best_score = 0
    subject_lower = subject.lower()
    
    for entry in toc_entries:
        # Calculate similarity score
        name_score = fuzz.ratio(subject_lower, entry['subject_name'].lower())
        partial_score = fuzz.partial_ratio(subject_lower, entry['subject_name'].lower())
        score = max(name_score, partial_score)
        
        # Boost score for exact word matches
        subject_words = subject_lower.split()
        entry_words = entry['subject_name'].lower().split()
        word_matches = sum(1 for word in subject_words if word in entry_words)
        if word_matches > 0:
            score += (word_matches / len(subject_words)) * 30
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = entry
    
    if not best_match:
        logger.warning("No good match in TOC, falling back to fuzzy search")
        return find_subject_pages_fallback(pdf_buffer, subject, threshold)
    
    logger.info(f"Best match: {best_match['course_code']} - {best_match['subject_name']} (Score: {best_score})")
    
    # Step 3: Find the ACTUAL start of the subject (not just TOC page)
    toc_page = best_match['page_number']
    actual_start_page = find_actual_subject_start(pdf_buffer, toc_page, best_match['course_code'])
    
    # Step 4: Find the end boundary using EXACT template recognition
    end_page = find_exact_template_boundary(pdf_buffer, actual_start_page, best_match['course_code'])
    
    # Step 5: Return the range of pages
    matching_pages = list(range(actual_start_page, end_page + 1))
    logger.info(f"Extracted pages {actual_start_page + 1} to {end_page + 1} ({len(matching_pages)} pages)")
    logger.info(f"Using exact template boundary detection for course: {best_match['course_code']}")
    
    return matching_pages, best_match

def find_subject_pages_fallback(pdf_buffer, subject, threshold=70):
    """Fallback fuzzy search method"""
    logger.info(f"Fallback search for subject: {subject}")
    pdf_buffer.seek(0)
    reader = PdfReader(pdf_buffer)
    matching_pages = []
    subject_lower = subject.lower()
    
    for i in range(len(reader.pages)):
        try:
            text = reader.pages[i].extract_text().lower() or ""
            score = fuzz.partial_ratio(subject_lower, text)
            
            if re.search(r'21cs[ce]\d+[a-z]?', text, re.IGNORECASE):
                score += 25
            if any(keyword in text for keyword in ['syllabus', 'course', 'curriculum']):
                score += 15
            if subject_lower in text:
                score = max(score, 90)
            
            if score >= threshold:
                matching_pages.append(i)
                        
        except Exception as e:
            logger.warning(f"Error processing page {i+1}: {e}")
            continue
    
    return sorted(set(matching_pages)), None

def create_mini_pdf(pdf_buffer, page_indices, output_filename):
    """Extract original PDF pages - EXACT SAME METHOD THAT WORKED FOR DSA"""
    try:
        logger.info(f"Using DSA-successful method for pages: {[p+1 for p in sorted(page_indices)]}")
        
        # Use the EXACT same approach that worked for DSA
        pdf_buffer.seek(0)
        reader = PdfReader(pdf_buffer)
        writer = PdfWriter()
        
        logger.info(f"Source PDF has {len(reader.pages)} total pages")
        
        # Add pages exactly like DSA
        pages_added = 0
        for page_idx in sorted(page_indices):
            if page_idx < len(reader.pages):
                try:
                    page = reader.pages[page_idx]
                    writer.add_page(page)
                    pages_added += 1
                    logger.info(f"Added page {page_idx + 1}")
                except Exception as e:
                    logger.error(f"Error adding page {page_idx + 1}: {e}")
                    continue
        
        if pages_added == 0:
            raise Exception("No pages were added")
        
        logger.info(f"Total pages added: {pages_added}")
        
        # Write exactly like DSA
        with open(output_filename, 'wb') as output_file:
            writer.write(output_file)
        
        # Verify file
        if not os.path.exists(output_filename):
            raise Exception("PDF file was not created")
        
        file_size = os.path.getsize(output_filename)
        logger.info(f"PDF created: {file_size} bytes")
        
        if file_size < 1000:
            raise Exception(f"PDF too small: {file_size} bytes")
        
        # Quick validation
        try:
            with open(output_filename, 'rb') as test_file:
                test_reader = PdfReader(test_file)
                test_pages = len(test_reader.pages)
                logger.info(f"Validation: {test_pages} pages readable")
        except Exception as validation_error:
            logger.error(f"Validation failed: {validation_error}")
            raise Exception(f"PDF corrupted: {validation_error}")
        
        return output_filename
        
    except Exception as e:
        logger.error(f"PDF creation failed: {e}")
        
        # Clean up failed file
        if os.path.exists(output_filename):
            try:
                os.remove(output_filename)
            except:
                pass
        
        raise Exception(f"Failed to create PDF: {e}")

def create_simple_pdf_alternative(pdf_buffer, page_indices, output_filename):
    """Alternative PDF creation method using reportlab as backup"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        logger.info(f"Using alternative PDF creation method")
        
        # Extract text from the original pages
        pdf_buffer.seek(0)
        reader = PdfReader(pdf_buffer)
        
        # Create new PDF with reportlab
        c = canvas.Canvas(output_filename, pagesize=letter)
        width, height = letter
        
        for idx in sorted(page_indices):
            if idx < len(reader.pages):
                try:
                    # Extract text from the page
                    page = reader.pages[idx]
                    text = page.extract_text() or f"Page {idx + 1} content could not be extracted"
                    
                    # Add a new page
                    c.drawString(50, height - 50, f"Page {idx + 1} from SRMIST Syllabus")
                    
                    # Add the text (simplified)
                    y_position = height - 100
                    lines = text.split('\n')[:50]  # Limit to first 50 lines
                    
                    for line in lines:
                        if y_position < 50:  # Start new page if needed
                            c.showPage()
                            y_position = height - 50
                        
                        # Clean the line and limit length
                        clean_line = line.strip()[:80]  # Limit line length
                        if clean_line:
                            c.drawString(50, y_position, clean_line)
                            y_position -= 15
                    
                    c.showPage()  # New page for next content
                    
                except Exception as e:
                    logger.error(f"Error processing page {idx + 1}: {e}")
                    continue
        
        c.save()
        
        # Verify the file
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            logger.info(f"Alternative PDF created successfully: {output_filename}")
            return output_filename
        else:
            raise Exception("Alternative PDF creation failed")
            
    except Exception as e:
        logger.error(f"Alternative PDF creation failed: {e}")
        raise e

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.post("/api/search")
async def search_syllabus(request: Request):
    """Search for a subject in the SRMIST syllabus PDF"""
    try:
        data = await request.json()
        subject = data.get('subject', '').strip()
        
        if not subject:
            return JSONResponse({
                "success": False, 
                "message": "Please enter a subject name."
            })
        
        # SRMIST Computing Programmes Syllabus 2021 URL
        pdf_url = "https://webstor.srmist.edu.in/web_assets/downloads/2023/computing-programmes-syllabus-2021.pdf"
        
        # Download and search PDF using smart algorithm
        pdf_buffer = download_pdf(pdf_url)
        result = find_subject_pages_smart(pdf_buffer, subject)
        
        # Handle both smart and fallback results
        if isinstance(result, tuple) and len(result) == 2:
            matching_pages, matched_subject = result
        else:
            matching_pages, matched_subject = result, None
        
        if not matching_pages:
            return JSONResponse({
                "success": False, 
                "message": f"No pages found for '{subject}'. Try different keywords or check spelling."
            })
        
        # Create mini PDF - FIXED filename generation
        temp_dir = tempfile.gettempdir()
        unique_id = str(uuid.uuid4())
        
        # Clean the subject name properly - remove special characters
        clean_subject = re.sub(r'[^\w\s-]', '', subject)  # Remove special chars
        clean_subject = re.sub(r'\s+', '_', clean_subject)  # Replace spaces with underscores
        clean_subject = clean_subject[:20]  # Limit length
        
        output_filename = f"srmist_{clean_subject}_{unique_id}.pdf"
        output_path = os.path.join(temp_dir, output_filename)
        
        logger.info(f"Creating PDF with clean filename: {output_filename}")
        
        # Extract original PDF pages only
        create_mini_pdf(pdf_buffer, matching_pages, output_path)
        
        # Prepare response with additional info if smart match was found
        response_data = {
            "success": True,
            "subject": subject,
            "pages": [p + 1 for p in matching_pages],  # Convert to 1-based indexing
            "page_count": len(matching_pages),
            "download_url": f"/api/download/{output_filename}",
            "filename": output_filename
        }
        
        # Add matched subject info if found via smart search
        if matched_subject:
            response_data.update({
                "matched_course_code": matched_subject['course_code'],
                "matched_subject_name": matched_subject['subject_name'],
                "extraction_method": "smart_toc"
            })
        else:
            response_data["extraction_method"] = "fuzzy_search"
        
        return JSONResponse(response_data)
        
    except requests.RequestException as e:
        logger.error(f"Error downloading PDF: {e}")
        return JSONResponse({
            "success": False,
            "message": "Error downloading the syllabus PDF. Please try again later."
        })
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse({
            "success": False,
            "message": "An unexpected error occurred. Please try again."
        })

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download the generated mini PDF - IMPROVED VERSION"""
    try:
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        logger.info(f"Download request for: {filename}")
        logger.info(f"Looking for file at: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return JSONResponse({
                "success": False,
                "message": "File not found or expired."
            })
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.error(f"File is empty: {file_path}")
            return JSONResponse({
                "success": False,
                "message": "Generated PDF is empty."
            })
        
        logger.info(f"Serving file: {filename} ({file_size} bytes)")
        
        # Return file with proper headers
        response = FileResponse(
            file_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(file_size)
            }
        )
        
        # Don't delete immediately - let the file be served first
        # Clean up will happen later or on next request
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error downloading file: {str(e)}"
        })

@app.get("/api/subjects")
async def get_subjects():
    """Get all subjects from the PDF table of contents"""
    try:
        pdf_url = "https://webstor.srmist.edu.in/web_assets/downloads/2023/computing-programmes-syllabus-2021.pdf"
        pdf_buffer = download_pdf(pdf_url)
        toc_entries = parse_table_of_contents(pdf_buffer)
        
        # Format subjects for dropdown
        subjects = []
        for entry in toc_entries:
            subjects.append({
                "code": entry['course_code'],
                "name": entry['subject_name'],
                "display": f"{entry['course_code']} - {entry['subject_name']}",
                "page": entry['page_number'] + 1  # Convert to 1-based
            })
        
        return JSONResponse({
            "success": True,
            "subjects": subjects,
            "count": len(subjects)
        })
        
    except Exception as e:
        logger.error(f"Error getting subjects: {e}")
        return JSONResponse({
            "success": False,
            "message": "Error loading subjects from PDF"
        })

@app.get("/api/test-pdf")
async def test_pdf_creation():
    """Test PDF creation with a simple document"""
    try:
        from pypdf import PdfWriter
        import tempfile
        
        # Create a simple test PDF
        writer = PdfWriter()
        
        # Create a simple page (this might not work without content, but let's try)
        temp_dir = tempfile.gettempdir()
        test_filename = f"test_pdf_{uuid.uuid4()}.pdf"
        test_path = os.path.join(temp_dir, test_filename)
        
        # Try to create an empty PDF
        with open(test_path, 'wb') as f:
            writer.write(f)
        
        if os.path.exists(test_path):
            file_size = os.path.getsize(test_path)
            os.remove(test_path)  # Clean up
            return {"status": "success", "message": f"Test PDF created successfully ({file_size} bytes)"}
        else:
            return {"status": "error", "message": "Test PDF was not created"}
            
    except Exception as e:
        return {"status": "error", "message": f"Test PDF creation failed: {e}"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SRMIST Syllabus Extractor"}

# Export the FastAPI app for Vercel
handler = app

if __name__ == "__main__":
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    
    print("Starting SRMIST Syllabus Extractor Portal...")
    print("Ready to search the 587-page Computing Programmes Syllabus 2021")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
