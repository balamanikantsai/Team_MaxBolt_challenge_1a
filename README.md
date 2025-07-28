# Adobe India Hackathon 2025 - Challenge 1A

## Intelligent PDF Heading Extraction with Enhanced Accuracy

### Overview

This solution provides an innovative approach to PDF heading extraction that goes beyond simple font-size analysis. It combines multiple parsing strategies to achieve high accuracy in heading detection and page number identification.

### Key Features

1. **Multi-Strategy Parsing**: Uses Docling for initial HTML conversion, then applies multiple fallback strategies for robust heading detection.

2. **Intelligent Page Number Detection**: Implements a sophisticated search algorithm that:
   - Searches for heading text within actual PDF content
   - Uses occurrence counting to handle duplicate headings
   - Provides intelligent fallback mechanisms for edge cases

3. **Content-Based Verification**: Cross-references extracted headings with actual PDF content to ensure accuracy.

4. **Performance Optimized**: Designed to process 50-page PDFs within the 10-second constraint.

### Libraries Used

- **docling**: Primary PDF to HTML conversion
- **beautifulsoup4**: HTML parsing and heading extraction
- **langchain-community**: PDF content extraction for verification
- **pypdf**: Fallback PDF processing

### Architecture

```
PDF Input → Docling Conversion → HTML Parsing → Content Verification → JSON Output
```

1. **PDF Conversion**: Convert PDF to structured HTML using Docling
2. **Heading Extraction**: Parse HTML to identify H1-H6 tags
3. **Page Number Detection**: Search for heading text in original PDF content
4. **Verification**: Apply multiple strategies to ensure accuracy
5. **Output Generation**: Create structured JSON with title and outline

### Innovation Points

- **Smart Search Strategy**: Skips first occurrence of headings to handle table of contents vs. actual content
- **Multiple Fallback Mechanisms**: Ensures robust operation across different PDF formats
- **Content-Based Validation**: Verifies extracted headings against actual PDF content
- **Modular Design**: Easy to extend and maintain

### How to Build and Run

```bash
# Build the Docker image
docker build --platform linux/amd64 -t challenge1a:latest .

# Run the solution
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none challenge1a:latest
```

### Input/Output Format

**Input**: PDF files in `/app/input/` directory

**Output**: JSON files in `/app/output/` directory with format:
```json
{
  "title": "Document Title",
  "outline": [
    {"level": "H1", "text": "Introduction", "page": 1},
    {"level": "H2", "text": "Background", "page": 2}
  ]
}
```

### Performance Characteristics

- **Speed**: Processes 50-page PDFs in under 10 seconds
- **Accuracy**: High precision and recall for heading detection
- **Memory**: Optimized for 16GB RAM constraint
- **CPU**: Efficient single-threaded processing for AMD64 architecture

### Edge Case Handling

- Handles PDFs with inconsistent font sizing
- Manages duplicate headings across different sections
- Processes multilingual content (bonus feature)
- Deals with complex document structures and layouts

