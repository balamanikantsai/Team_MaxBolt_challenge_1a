#!/usr/bin/env python3
"""
Adobe India Hackathon 2025 - Challenge 1A
Intelligent PDF Heading Extraction with Enhanced Accuracy

This solution provides an innovative approach to PDF heading extraction by:
1. Using multiple parsing strategies for robust extraction
2. Implementing intelligent page number detection with fallback mechanisms
3. Leveraging both structural and content-based analysis
4. Providing fast, accurate results within the 10-second constraint
"""

import os
import sys
import json
from pathlib import Path
import time
from challenge_1a import convert_pdf_to_html_and_extract_headings

def process_all_pdfs():
    """
    Process all PDFs from /app/input directory and generate JSON outputs in /app/output
    """
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files in input directory
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in /app/input directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        start_time = time.time()
        print(f"\nProcessing: {pdf_file.name}")
        
        try:
            # Extract headings
            headings_data = convert_pdf_to_html_and_extract_headings(
                str(pdf_file), 
                str(output_dir)
            )
            
            if headings_data:
                # Save JSON output with same name as PDF
                output_file = output_dir / f"{pdf_file.stem}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(headings_data, f, indent=2, ensure_ascii=False)
                
                processing_time = time.time() - start_time
                print(f"✓ Successfully processed {pdf_file.name} in {processing_time:.2f} seconds")
                print(f"  Output saved to: {output_file}")
                print(f"  Found {len(headings_data.get('outline', []))} headings")
                
            else:
                print(f"✗ Failed to process {pdf_file.name}")
                
        except Exception as e:
            print(f"✗ Error processing {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("Adobe India Hackathon 2025 - Challenge 1A")
    print("Intelligent PDF Heading Extraction")
    print("=" * 50)
    
    process_all_pdfs()
    
    print("\nProcessing complete!")

