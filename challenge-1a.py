import os
import json
import re
from pathlib import Path
from docling.document_converter import DocumentConverter
from bs4 import BeautifulSoup

def convert_pdf_to_html_and_extract_headings(pdf_path: str, output_dir: str = "output"):
    """
    Converts PDF to HTML using Docling and extracts H1-H6 headings with page numbers.
    
    Args:
        pdf_path (str): Path to the input PDF file.
        output_dir (str): Directory where output files will be saved.
    Returns:
        dict: Extracted headings data in the same format as file02.json
    """
    if not Path(pdf_path).is_file():
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"Converting '{pdf_path}' to HTML using Docling...")
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        # Get HTML content
        html_content = result.document.export_to_html()
        
        # Save HTML to file
        html_file_path = Path(output_dir) / f"{Path(pdf_path).stem}.html"
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML saved to: {html_file_path}")
        
        # Extract headings from HTML
        headings_data = extract_headings_from_html(html_content, pdf_path)
        
        # Save headings as JSON
        json_file_path = Path(output_dir) / f"{Path(pdf_path).stem}.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(headings_data, f, indent=4, ensure_ascii=False)
        print(f"Headings JSON saved to: {json_file_path}")
        
        return headings_data

    except Exception as e:
        print(f"Error during conversion: {e}")
        return None

def extract_headings_from_html(html_content: str, pdf_path: str):
    """
    Extract H1-H6 headings from HTML content and verify page numbers by searching in PDF content
    
    Args:
        html_content (str): HTML content from PDF conversion
        pdf_path (str): Original PDF file path for title extraction and content search
    Returns:
        dict: Formatted headings data with accurate page numbers
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract document title (try multiple methods)
    title = extract_document_title(soup, pdf_path)
    
    # Extract PDF content page by page for searching
    print("Extracting PDF content for heading verification...")
    pdf_content_by_page = extract_pdf_content_by_pages(pdf_path)
    
    # Find all heading tags (H1-H6)
    heading_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    outline = []
    last_found_page = 0  # Track the last successfully found page
    
    for heading in heading_tags:
        # Get heading level (H1, H2, etc.)
        level = heading.name.upper()
        
        # Get heading text (clean up whitespace)
        text = heading.get_text(strip=True)
        
        if text and len(text) > 2:  # Only process meaningful text
            # Search for the heading text in PDF content to get accurate page number
            page_number = search_heading_in_pdf_content(text, pdf_content_by_page, last_found_page)
            
            # If not found, try fallback methods
            if page_number is None:
                page_number = estimate_page_from_surrounding_headings(text, outline, pdf_content_by_page, last_found_page)
            
            # Update last found page if we got a valid result
            if page_number and page_number > last_found_page:
                last_found_page = page_number
            
            outline.append({
                "level": level,
                "text": text,
                "page": page_number
            })
            
            # Log the result
            if page_number:
                print(f"✓ Found '{text[:50]}...' on page {page_number}")
            else:
                print(f"⚠ Could not locate '{text[:50]}...' - using fallback")
    
    # Create the final structure matching file02.json format
    headings_data = {
        "title": title,
        "outline": outline
    }
    
    return headings_data

def extract_pdf_content_by_pages(pdf_path: str):
    """
    Extract PDF content page by page using LangChain PyPDF loader
    
    Returns:
        dict: {page_number: content_text}
    """
    try:
        from langchain_community.document_loaders import PyPDFLoader
        
        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        
        pdf_content_by_page = {}
        
        for i, doc in enumerate(documents):
            page_num = i + 1
            page_content = doc.page_content
            pdf_content_by_page[page_num] = page_content
        
        print(f"Extracted content from {len(documents)} pages for search")
        return pdf_content_by_page
        
    except ImportError:
        print("LangChain not available, falling back to basic page estimation")
        return {}
    except Exception as e:
        print(f"Error extracting PDF content: {e}")
        return {}

def search_heading_in_pdf_content(heading_text: str, pdf_content_by_page: dict, last_found_page: int = 0):
    """
    Search for heading text in PDF content to find the correct page number
    Uses smart search strategy: skip first occurrence, start from last found page + 1
    
    Args:
        heading_text: The heading text to search for
        pdf_content_by_page: Dictionary of PDF content by page number
        last_found_page: Page number of the last found heading (to start search after)
    Returns:
        int: Page number where heading is found, or None if not found
    """
    if not pdf_content_by_page:
        return None
    
    # Clean and prepare the heading text for search
    clean_heading = clean_text_for_search(heading_text)
    
    # Remove numbers and special characters from heading for better matching
    clean_heading_no_numbers = remove_numbers_and_special_chars(clean_heading)
    heading_words = clean_heading_no_numbers.split()
    
    # Determine starting page for search
    start_page = last_found_page + 1 if last_found_page > 0 else 1
    
    # Get pages to search (from start_page onwards)
    pages_to_search = [p for p in sorted(pdf_content_by_page.keys()) if p >= start_page]
    
    print(f"  Searching '{heading_text[:30]}...' -> '{clean_heading_no_numbers[:30]}...' starting from page {start_page}")
    
    # Strategy 1: Exact text match with occurrence counting (using cleaned text)
    exact_matches = []
    for page_num in pages_to_search:
        content = pdf_content_by_page[page_num]
        clean_content = clean_text_for_search(content)
        if clean_heading_no_numbers in clean_content:
            exact_matches.append(page_num)
    
    if exact_matches:
        # If only one occurrence found, return it immediately
        if len(exact_matches) == 1:
            selected_page = exact_matches[0]
            print(f"    Found single exact match on page {selected_page}")
        # If multiple occurrences and this is first search, skip first occurrence
        elif last_found_page == 0 and len(exact_matches) > 1:
            selected_page = exact_matches[1]  # Pick second occurrence
            print(f"    Found exact matches on pages {exact_matches}, picking second: {selected_page}")
        else:
            selected_page = exact_matches[0]  # Pick first available
            print(f"    Found exact match on page {selected_page}")
        return selected_page
    
    # Strategy 2: Partial match with most words (with occurrence logic)
    if len(heading_words) >= 2:
        partial_matches = []
        for page_num in pages_to_search:
            content = pdf_content_by_page[page_num]
            clean_content = clean_text_for_search(content)
            
            # Check if majority of words appear in the content
            word_matches = sum(1 for word in heading_words if word in clean_content)
            match_ratio = word_matches / len(heading_words)
            
            if match_ratio >= 0.7:  # At least 70% of words match
                partial_matches.append((page_num, match_ratio))
        
        if partial_matches:
            # Sort by match ratio (best first)
            partial_matches.sort(key=lambda x: x[1], reverse=True)
            
            # If only one match found, return it immediately
            if len(partial_matches) == 1:
                selected_page = partial_matches[0][0]
                print(f"    Found single partial match on page {selected_page}")
            # If multiple matches and this is first search, skip first occurrence
            elif last_found_page == 0 and len(partial_matches) > 1:
                selected_page = partial_matches[1][0]  # Pick second best
                print(f"    Found partial matches, picking second best: page {selected_page}")
            else:
                selected_page = partial_matches[0][0]  # Pick best
                print(f"    Found partial match on page {selected_page}")
            return selected_page
    
    # Strategy 3: Sequential word matching for multi-word headings
    if len(heading_words) >= 3:
        sequence_matches = []
        for page_num in pages_to_search:
            content = pdf_content_by_page[page_num]
            clean_content = clean_text_for_search(content)
            
            # Check for consecutive word sequences (using cleaned heading words)
            for i in range(len(heading_words) - 2):
                phrase = " ".join(heading_words[i:i+3])
                if phrase in clean_content:
                    sequence_matches.append(page_num)
                    break  # Only count once per page
        
        if sequence_matches:
            # If only one match found, return it immediately
            if len(sequence_matches) == 1:
                selected_page = sequence_matches[0]
                print(f"    Found single sequence match on page {selected_page}")
            # If multiple matches and this is first search, skip first occurrence
            elif last_found_page == 0 and len(sequence_matches) > 1:
                selected_page = sequence_matches[1]  # Pick second occurrence
                print(f"    Found sequence matches on pages {sequence_matches}, picking second: {selected_page}")
            else:
                selected_page = sequence_matches[0]  # Pick first available
                print(f"    Found sequence match on page {selected_page}")
            return selected_page
    
    print(f"    No matches found for '{heading_text[:30]}...'")
    return None

def estimate_page_from_surrounding_headings(heading_text: str, existing_outline: list, pdf_content_by_page: dict, last_found_page: int = 0):
    """
    Estimate page number based on surrounding headings that were successfully found
    
    Args:
        heading_text: The heading text that couldn't be found
        existing_outline: List of already processed headings
        pdf_content_by_page: PDF content by page
        last_found_page: The last successfully found page number
    Returns:
        int: Estimated page number
    """
    if not existing_outline:
        return 1
    
    # Use the last found page as reference if available
    if last_found_page > 0:
        # Try next page after the last found heading
        max_page = max(pdf_content_by_page.keys()) if pdf_content_by_page else 6
        next_page = min(last_found_page + 1, max_page)
        print(f"    Estimating page {next_page} based on last found page {last_found_page}")
        return next_page
    
    # Fallback: Get the last successfully found heading's page number from outline
    last_outline_page = None
    for heading in reversed(existing_outline):
        if heading.get("page"):
            last_outline_page = heading["page"]
            break
    
    if last_outline_page:
        # Try next page after the last found heading
        max_page = max(pdf_content_by_page.keys()) if pdf_content_by_page else 6
        next_page = min(last_outline_page + 1, max_page)
        print(f"    Estimating page {next_page} based on outline")
        return next_page
    
    # Final fallback to page 1
    return 1

def remove_numbers_and_special_chars(text: str):
    """
    Remove numbers and special characters from text, keeping only letters and spaces
    """
    # Remove numbers (digits)
    text = re.sub(r'\d+', '', text)
    
    # Remove special characters except spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def clean_text_for_search(text: str):
    """
    Clean text for better search matching
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common punctuation but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove extra spaces again
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_document_title(soup, pdf_path):
    """
    Extract document title using multiple strategies
    """
    # Strategy 1: Look for HTML title tag
    title_tag = soup.find('title')
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)
    
    # Strategy 2: Look for first H1 tag
    first_h1 = soup.find('h1')
    if first_h1 and first_h1.get_text(strip=True):
        return first_h1.get_text(strip=True)
    
    # Strategy 3: Look for document header/title patterns
    for tag in soup.find_all(['div', 'p', 'span']):
        text = tag.get_text(strip=True)
        if len(text) > 10 and len(text) < 100:
            # Check if it looks like a title (has title-case or important keywords)
            if (text.istitle() or 
                any(word in text.lower() for word in ['overview', 'guide', 'manual', 'document', 'report'])):
                return text
    
    # Strategy 4: Use filename as fallback
    return Path(pdf_path).stem.replace('_', ' ').replace('-', ' ').title()

def extract_page_number(heading_element, soup):
    """
    Extract page number for a heading using multiple strategies
    """
    # Strategy 1: Look for page attributes or data attributes
    if heading_element.get('data-page'):
        try:
            return int(heading_element.get('data-page'))
        except:
            pass
    
    # Strategy 2: Look for page information in parent elements
    parent = heading_element.parent
    for _ in range(3):  # Check up to 3 parent levels
        if parent:
            if parent.get('data-page'):
                try:
                    return int(parent.get('data-page'))
                except:
                    pass
            parent = parent.parent
    
    # Strategy 3: Look for page markers in nearby text
    # Check siblings and nearby elements for page indicators
    for sibling in heading_element.find_next_siblings():
        text = sibling.get_text()
        page_match = re.search(r'page\s+(\d+)|p\.?\s*(\d+)', text.lower())
        if page_match:
            try:
                return int(page_match.group(1) or page_match.group(2))
            except:
                pass
    
    # Strategy 4: Look for page div/section containers
    page_container = heading_element.find_parent(['div', 'section'], class_=re.compile(r'page'))
    if page_container:
        page_text = page_container.get('class', [])
        for class_name in page_text:
            page_match = re.search(r'page[-_]?(\d+)', str(class_name))
            if page_match:
                try:
                    return int(page_match.group(1))
                except:
                    pass
    
    # Strategy 5: Sequential numbering (fallback)
    # Count position of heading in document and estimate page
    all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    heading_index = all_headings.index(heading_element) if heading_element in all_headings else 0
    
    # Rough estimate: assume ~3-5 headings per page
    estimated_page = max(1, (heading_index // 4) + 1)
    
    return estimated_page

def display_extracted_headings(headings_data):
    """
    Display extracted headings in a nice format
    """
    if not headings_data:
        print("No headings data to display")
        return
    
    print("\n" + "="*60)
    print(f"DOCUMENT TITLE: {headings_data['title']}")
    print("="*60)
    print(f"EXTRACTED HEADINGS ({len(headings_data['outline'])} found):")
    print("-"*60)
    
    for item in headings_data['outline']:
        level = item['level']
        text = item['text']
        page = item['page']
        
        # Add indentation based on heading level
        indent = "  " * (int(level[1]) - 1) if len(level) > 1 else ""
        level_symbol = "■" if level == "H1" else "▪" if level == "H2" else "•"
        
        print(f"{indent}{level_symbol} [{level}] {text} (Page {page})")

if __name__ == "__main__":
    # Configuration
    pdf_file = "file02.pdf"  # Change this to your PDF file
    output_directory = "extracted_headings"
    
    # Check if PDF exists
    if not Path(pdf_file).exists():
        print(f"Error: {pdf_file} not found")
        print("Available PDF files:")
        for pdf in Path(".").glob("*.pdf"):
            print(f"  - {pdf.name}")
        exit(1)
    
    # Convert PDF and extract headings
    print("Starting PDF to HTML conversion and heading extraction...")
    headings_data = convert_pdf_to_html_and_extract_headings(pdf_file, output_directory)
    
    # Display results
    if headings_data:
        display_extracted_headings(headings_data)
        
        print(f"\n✅ Process completed!")
        print(f"📁 Check output files in: {output_directory}/")
        print(f"📄 HTML file: {pdf_file.replace('.pdf', '.html')}")
        print(f"📋 JSON file: {pdf_file.replace('.pdf', '.json')}")
    else:
        print("❌ Failed to extract headings")