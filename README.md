# PageWisePDF

PageWisePDF is a powerful desktop application that uses AI to process PDF files, providing advanced OCR (Optical Character Recognition) and text summarization capabilities. It leverages OpenAI's Vision API to accurately extract text while preserving formatting, tables, and document structure.

## Features

- **AI-Powered OCR**: Uses state-of-the-art vision models to extract text from PDFs
- **Smart Summarization**: Generate concise summaries of PDF documents
- **Format Preservation**: Maintains original document structure, including tables and formatting
- **Batch Processing**: Process multiple pages concurrently for increased efficiency
- **Bilingual Support**: Supports both English and Chinese interfaces and output
- **Clean Interface**: Modern, user-friendly GUI built with PyQt5
- **Flexible Output**: Results saved in markdown format for maximum compatibility

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Franklyc/PageWisePDF.git
cd PageWisePDF
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Launch the application:
```bash
python run.py
```

2. In the application:
   - Select your PDF file using the "Browse" button
   - Choose your output directory
   - Configure processing options:
     - Full Text Extraction: Preserves all text and formatting
     - Summary Mode: Generates concise summaries
   - Select your preferred output language (English/Chinese)
   - Configure page range (optional)
   - Configure API settings (requires OpenAI API key)
   - Click "Start Processing"

## Configuration

Before using PageWisePDF, you need to configure your OpenAI API settings:

1. Click the "API Settings" button
2. Enter your OpenAI API key
3. (Optional) Customize:
   - API endpoint
   - Model selection
   - Concurrent API calls
   - Pages per API call
   - API call interval

## Requirements

- Python 3.6+
- PyQt5
- PyMuPDF
- OpenAI API access
- Other dependencies listed in requirements.txt

## Output

The application generates:
- Individual markdown files for each processed page
- A consolidated markdown file containing all processed content
- Preserved images in PNG format

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## Acknowledgments

- Built with OpenAI's Vision API
- Uses PyQt5 for the GUI interface
- Uses PyMuPDF for PDF processing

