# Document Research & Theme Analyzer

A modern web application for uploading, analyzing and querying documents to extract insights, themes, and relevant information.

## Features

- User-friendly interface with drag-and-drop file uploads
- Document storage and management
- Natural language query processing
- Document passage retrieval and citation
- Theme identification from documents
- Responsive design for desktop and mobile usage

## Prerequisites

- Python 3.8+
- FastAPI
- Uvicorn
- Other dependencies listed in requirements.txt

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/document-analyzer.git
cd document-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
document-analyzer/
│
├── app/
│   ├── main.py                # FastAPI application
│   ├── static/                # Static files (CSS, JS)
│   ├── templates/             # HTML templates
│   │   └── html/
│   │       └── index.html     # Main application page
│   │
│   └── uploads/               # Document upload directory
│   
├── requirements.txt           # Project dependencies
└── README.md                  # This file
```

## Setting Up the Application

1. Create necessary directories:
```bash
mkdir -p app/static app/templates/html app/uploads
```

2. Copy the `index.html` file to the templates directory:
```bash
cp index.html app/templates/html/
```

3. Create a requirements.txt file:
```
fastapi==0.103.1
uvicorn==0.23.2
python-multipart==0.0.6
aiofiles==23.2.1
pydantic==2.3.0
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

## Usage

1. **Upload Documents**:
   - Drag and drop files onto the upload area, or click to select files
   - Supported file types include PDF, TXT, DOCX, and more

2. **Ask Questions**:
   - Type your question in the input box and click "Send" or press Enter
   - The application will analyze your documents and provide relevant answers

3. **View Results**:
   - Answers will appear in the chat box
   - Relevant document passages will be displayed in the document viewer panel
   - If identified, document themes will be shown at the top

## Extending the Application

For a production application, you might want to:

1. **Add Authentication**:
   - Implement user accounts and login functionality
   - Secure document storage per user

2. **Improve Document Processing**:
   - Integrate with NLP libraries for better text analysis
   - Add support for more document formats
   - Implement vector search for more accurate document retrieval

3. **Add Database Integration**:
   - Replace in-memory storage with a database (SQLite, PostgreSQL, etc.)
   - Implement proper document indexing

4. **Add Advanced Features**:
   - Summary generation
   - Document comparison
   - Topic modeling
   - Knowledge graph visualization

## License

[MIT](LICENSE)
