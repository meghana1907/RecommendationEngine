# 🚀 Intelligent Test Recommendation System

A comprehensive AI-powered system that combines **BRD Analysis**, **Jira Integration**, **Gap Analysis**, and **Intelligent Test Recommendations** in a unified workflow.

![System Overview](https://img.shields.io/badge/Status-Production_Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![React](https://img.shields.io/badge/React-18.2+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)

## 🌟 Features

### 🔄 **Unified Workflow**
1. **📄 BRD Upload** - Multi-format support (PDF, DOCX, DOC, TXT, MD)
2. **🔗 Jira Integration** - Fetch user stories, epics, and sprints
3. **🤖 AI Gap Analysis** - Powered by Google Gemini AI & LangGraph
4. **🧪 Test Recommendations** - Intelligent, context-aware test suggestions

### 🎯 **Core Capabilities**
- **Smart File Processing**: Extract text from multiple document formats
- **Jira Authentication**: Secure API token-based integration
- **LangGraph Workflows**: State-based BRD analysis and comparison
- **Gemini AI**: Advanced natural language processing for gap analysis
- **Clustering Engine**: Semantic grouping of requirements and features
- **Domain-Aware Testing**: Context-sensitive test recommendation engine
- **Real-time Progress**: Step-by-step workflow with visual indicators

## 🏗️ Architecture

```
Frontend (React)           Backend (FastAPI)              AI Services
     │                         │                             │
┌────┴────┐              ┌─────┴─────┐                ┌─────┴─────┐
│   UI    │   ──────────▶ │   API     │   ──────────▶ │  Gemini   │
│ Workflow│              │ Endpoints │               │    AI     │
└─────────┘              └───────────┘               └───────────┘
     │                         │                             │
┌────┴────┐              ┌─────┴─────┐                ┌─────┴─────┐
│  File   │              │ Document  │               │ LangGraph │
│ Upload  │              │Processor  │               │ Workflows │
└─────────┘              └───────────┘               └───────────┘
     │                         │                             │
┌────┴────┐              ┌─────┴─────┐                ┌─────┴─────┐
│  Jira   │              │   Jira    │               │Embedding  │
│Interface│              │ Service   │               │ Service   │
└─────────┘              └───────────┘               └───────────┘
```

## 🛠️ Quick Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Gemini API Key
- Jira API Token (for Jira integration)

### 🚀 One-Click Setup

**Windows:**
```bash
setup_system.bat
```

**Linux/Mac:**
```bash
chmod +x setup_system.sh
./setup_system.sh
```

### 📋 Manual Setup

1. **Backend Setup**
   ```bash
   cd backend_python
   pip install -r requirements.txt
   pip install langgraph textract  # Additional dependencies
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

3. **Environment Configuration**
   
   Create `.env` in `backend_python/`:
   ```env
   # Required for AI Gap Analysis
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Optional for data storage
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

## 🎮 Usage Guide

### 1. Start the System

**Backend (Terminal 1):**
```bash
cd backend_python
uvicorn main:app --reload
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm start
```

**Access:** http://localhost:3000

### 2. Workflow Steps

#### Step 1: 📄 **Upload BRD**
- Drag & drop or browse for BRD files
- Supports: PDF, DOCX, DOC, TXT, MD
- View saved BRD files from previous uploads
- Preview content before proceeding

#### Step 2: 🔗 **Configure Jira**
- Enter Jira URL, email, and API token
- Select project, sprint, and filters
- Optional: Filter by assignee, epic, issue type

#### Step 3: 🔄 **Process User Stories**
- Fetch issues from Jira based on filters
- View and inspect retrieved issues
- Convert to standardized user story format

#### Step 4: 🤖 **Gap Analysis**
- AI-powered comparison using Gemini AI
- LangGraph workflows for structured analysis
- Identify missing requirements and coverage gaps

#### Step 5: 🧪 **Test Recommendations**
- Intelligent test clustering by feature domains
- Standard and AI-recommended test types
- Detailed rationale and effort estimates
- Source attribution for traceability

### 3. Features Deep Dive

#### 🎯 **Gap Analysis Results**
- **Full Analysis**: Complete BRD vs User Stories comparison
- **Missing Requirements**: Specific gaps with actionable insights
- **BRD Analysis**: Structured requirement extraction
- **User Stories**: Formatted story collection with metadata

#### 🧪 **Test Recommendations**
- **Cluster-based Organization**: Tests grouped by functional areas
- **Priority Levels**: High, Medium, Low priority classification  
- **Effort Estimates**: Time-based planning assistance
- **Source Attribution**: Traceability to original requirements
- **Multi-source Validation**: Cross-referenced recommendations

## 📊 API Endpoints

### BRD Management
- `POST /upload-brd` - Upload BRD files
- `GET /brd-files` - List uploaded files
- `GET /brd-file/{filename}` - Get file content

### Jira Integration
- `POST /api/jira-auth` - Authenticate and fetch issues
- `POST /api/process-jira-issues` - Convert to user stories

### AI Analysis
- `POST /compare` - BRD-Jira gap analysis
- `POST /api/tests/generate-intelligent` - Test recommendations

### Test Engine
- `POST /api/documents/upload-text` - Upload text content
- `POST /api/documents/process/{id}` - Process documents

**Full API Documentation:** http://localhost:8000/docs

## 🔧 Configuration

### Jira Integration Setup
1. Generate Jira API Token: Account Settings → Security → API Tokens
2. Find your Atlassian URL: `https://your-domain.atlassian.net`
3. Configure project keys, sprint names, and filters

### Gemini AI Setup
1. Get API key from Google AI Studio
2. Add to `.env`: `GEMINI_API_KEY=your_key_here`
3. Model used: `gemini-2.0-flash-exp` (configurable)

### File Upload Limits
- Max file size: 50MB (configurable)
- Supported formats: PDF, DOCX, DOC, TXT, MD, CSV, JSON
- Storage: Local filesystem (uploads/ directory)

## 🎨 UI/UX Features

- **📊 Progress Tracking**: Visual step indicator
- **🎯 Smart Navigation**: Step-based workflow prevention
- **📱 Responsive Design**: Mobile and desktop optimized
- **🎨 Modern UI**: Clean, professional interface
- **⚡ Real-time Updates**: Live status and progress feedback
- **📋 Tabbed Results**: Organized analysis presentation
- **🔍 Detailed Views**: Expandable sections and previews

## 🧪 Testing

### Backend Tests
```bash
cd backend_python
python test_integration.py  # Integration tests
python -m pytest            # Unit tests
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Environment
1. Set environment variables in production
2. Configure proper CORS settings
3. Set up file storage (S3, etc.)
4. Configure database (PostgreSQL recommended)
5. Set up monitoring and logging

### Docker Deployment
```bash
# Backend
docker build -t test-engine-backend ./backend_python
docker run -p 8000:8000 test-engine-backend

# Frontend  
docker build -t test-engine-frontend ./frontend
docker run -p 3000:3000 test-engine-frontend
```

## 📈 Performance

- **Gap Analysis**: ~10-30 seconds (depends on content size)
- **Test Generation**: ~15-45 seconds (depends on complexity)
- **File Processing**: ~2-10 seconds (depends on file size)
- **Jira Integration**: ~5-15 seconds (depends on issue count)

## 🛡️ Security

- API token validation for Jira
- Environment-based configuration
- Input sanitization and validation
- CORS protection
- File type validation
- Rate limiting (configurable)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: In-app help and tooltips
- **API Docs**: http://localhost:8000/docs
- **Issues**: GitHub Issues tab
- **Debugging**: Check browser console and server logs

---

**Built with ❤️ using FastAPI, React, Google Gemini AI, and LangGraph**