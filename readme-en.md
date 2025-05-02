# PDF Search System

A user-friendly desktop application for quickly and efficiently searching through PDF file contents. Using indexing technology, you can rapidly find the information you need across multiple PDF documents.

## Features

- **Fast Search**: Instantly display search results using indexing
- **Flexible Search Options**: 
  - Fuzzy search (multiple keywords)
  - Exact match search
  - Subfolder search
- **Automatic Indexing**: Automatically detect and index new or updated PDF files
- **Filename Exclusion**: Exclude PDF files with specific text patterns in their filenames from search
- **Context Display**: View the text surrounding your search keywords
- **Save Results**: Export search results as a text file
- **Easy Configuration**: Set up search folders and index DB location via an intuitive UI

## Screenshots

[Insert application screenshots here]

## Requirements

- Python 3.7 or higher
- The following Python libraries:
  - tkinter
  - pdfplumber
  - pypdf

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf_indexer_searcher.git
cd pdf_indexer_searcher

# Install required libraries
pip install -r requirements.txt

# Run the application
python pdf_indexer_searcher.py
```

## Usage

1. **First Launch**:
   - Select the folder containing your PDF files
   - Choose a folder to store the index files
   - Optionally configure filename patterns to exclude from search

2. **Performing a Search**:
   - Enter your search terms
   - Optionally check "Exact Match Search" or "Include Subfolders" as needed
   - Click the "Search" button

3. **Viewing Results**:
   - Select a file from the list on the left
   - View file details and context on the right
   - Double-click or press Enter on a selected file to open the PDF

4. **Saving Results**:
   - Click "Save Results" to save a list of matching filenames to your desktop

## Customizing Settings

- From the **Settings menu**, you can modify:
  - PDF search folder
  - Index DB folder
  - Exclusion patterns
  - Subfolder indexing options

## How It Works

This application:

1. Extracts text from PDF files in the specified folder
2. Stores the extracted text in a SQLite database
3. Executes fast searches against the search query
4. Displays search results in real-time

## License

Released under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions of all kinds are welcome, including bug reports, feature requests, and pull requests.

## Author

[Your Name]

---

*Note: This application has been tested with Japanese and English PDF files, but may work with documents in other languages as well.*
