# Document Research & Theme Identification Bot

An intelligent research assistant powered by LLMs (OpenAI/Groq) that performs document ingestion, semantic search, cross-document Q&A, and theme synthesis with visual citations.

![image](https://github.com/user-attachments/assets/b20bcc5b-afe6-47f3-a7c0-72ebe5af43b3)

## Features

- **Document Upload & Processing**: Upload and process PDF, DOCX, TXT, and image files
- **Text Extraction**: Extract text from documents using OCR when needed
- **Vector Embeddings**: Create and store vector embeddings of document chunks
- **Theme Identification**: Automatically identify key themes across multiple documents
- **AI-Powered Q&A**: Ask questions about your documents and get answers with citations

## Architecture

This system uses:
- **FastAPI**: For the API backend
- **Pinecone**: Vector database for document embeddings  
- **OpenAI/Groq**: LLM providers for AI capabilities
- **SentenceTransformers**: Creating document embeddings
- **PyPDF2, pytesseract, pdf2image**: Document processing and OCR

## Prerequisites

- Python 3.8+
- FastAPI
- Uvicorn
- Other dependencies listed in requirements.txt
## Getting Started

### Prerequisites

- Docker and Docker Compose
- Pinecone account (for vector database)
- OpenAI or Groq API key (for LLM capabilities)

### Installation

1. Clone the repository
```bash
git clone https://github.com/karthiksuki/chatbot_theme_identifier.git
cd chatbot_theme_identifier
```

2. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Build and start the Docker container
```bash
docker-compose up -d
```

4. Access the API at http://localhost:8000
   - API documentation is available at http://localhost:8000/docs

## API Endpoints

### Document Management
- `POST /api/upload/`: Upload documents
- `POST /api/analyze`: Analyze a single document

### Search & Analysis
- `POST /api/query`: Query documents with natural language
- `POST /api/themes/`: Extract themes from documents
- `POST /api/identify-themes`: Identify themes from document chunks

## Deployment

### Deploying to AWS

1. **Set up an EC2 instance**:
   - Launch an EC2 instance (t3.medium or larger recommended)
   - Install Docker and Docker Compose
   - Configure security groups to allow traffic on port 8000

2. **Clone and deploy**:
   ```bash
   git clone https://github.com/yourusername/citation-theme-bot.git
   cd citation-theme-bot
   cp .env.example .env
   # Edit .env file with your API keys
   docker-compose up -d
   ```

3. **Set up a load balancer (optional)**:
   - Create an Application Load Balancer
   - Configure HTTPS with a certificate
   - Point to your EC2 instance

### Deploying to Google Cloud

1. **Set up a VM instance**:
   - Create a VM instance (e2-standard-2 or larger)
   - Install Docker and Docker Compose

2. **Clone and deploy**:
   ```bash
   git clone https://github.com/yourusername/citation-theme-bot.git
   cd citation-theme-bot
   cp .env.example .env
   # Edit .env file with your API keys
   docker-compose up -d
   ```

3. **Configure firewall rules**:
   - Allow traffic on port 8000

### Deploying to Azure

1. **Create an Azure VM**:
   - Deploy a VM (Standard_D2s_v3 or larger)
   - Install Docker and Docker Compose

2. **Clone and deploy**:
   ```bash
   git clone https://github.com/yourusername/citation-theme-bot.git
   cd citation-theme-bot
   cp .env.example .env
   # Edit .env file with your API keys
   docker-compose up -d
   ```

3. **Configure network security group**:
   - Allow traffic on port 8000

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
