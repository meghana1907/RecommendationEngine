# 🧠 Dynamic Test Recommendation Engine

An AI-powered full-stack application that generates comprehensive test recommendations from Business Requirements Documents (BRD) and User Stories using React, Supabase, and Gemini 2.0.

![Dynamic Test Recommendation Engine](https://img.shields.io/badge/AI-Powered-blue) ![React](https://img.shields.io/badge/React-18.2-blue) ![Supabase](https://img.shields.io/badge/Supabase-2.0-green) ![Gemini](https://img.shields.io/badge/Gemini-2.0-purple)

## 🎯 Overview

This application takes BRD or User Stories documents, processes them through an AI pipeline, and generates dynamic test recommendations that are not limited to predefined categories. The system uses semantic analysis, clustering, and advanced AI to create both **Standard (Must-have)** and **Recommended (Advanced)** test types.

### ✨ Key Features

- **📁 Smart Document Processing**: Intelligent chunking and semantic analysis
- **🧠 AI Embedding**: Gemini 2.0 generates semantic vectors for deep understanding
- **🎯 Feature Clustering**: Groups related requirements using k-means clustering
- **⚡ Dynamic Test Generation**: Creates any relevant test types (functional, security, performance, etc.)
- **📊 Multiple View Modes**: By clusters, aggregated, or by category
- **🔄 Regeneration**: Dynamically update test recommendations
- **📤 Export Options**: JSON, CSV, and Markdown formats
- **🔍 Debug Mode**: Comprehensive logging for transparency

## 🏗️ Architecture

```
Frontend (React + Tailwind)
    ↓
Backend (Express.js + Node.js)
    ↓
Services Layer
    ├── Supabase (Database + Storage)
    ├── Gemini 2.0 (AI Embeddings + Recommendations)
    ├── Clustering Service (K-means)
    └── Debug Logging
```

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm
- Supabase account and project
- Gemini 2.0 API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd RecommendationEngine
```

### 2. Backend Setup

```bash
cd backend
npm install

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your credentials:
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_anon_key
# SUPABASE_SERVICE_ROLE=your_service_role_key
# GEMINI_API_KEY=your_gemini_api_key

# Start the backend server
npm run dev
```

Backend will run on `http://localhost:5000`

### 3. Frontend Setup

```bash
cd ../frontend
npm install

# Start the React development server
npm start
```

Frontend will run on `http://localhost:3000`

### 4. Database Setup

The backend automatically creates the required database tables on first run:
- `documents` - Stores uploaded documents
- `embeddings` - Stores text chunks and their embeddings
- `tests` - Stores test recommendations
- `cluster_summaries` - Stores cluster information

## 📋 Usage Workflow

### 1. Document Upload
- Upload a BRD/User Stories file (txt, doc, docx, pdf)
- Or paste content directly into the text area
- Minimum 100 characters required

### 2. AI Processing Pipeline
1. **Document Analysis**: Gemini analyzes document type and complexity
2. **Smart Chunking**: Text is broken into semantic segments
3. **Embedding Generation**: Each chunk gets a semantic vector
4. **Clustering**: Related chunks are grouped using k-means
5. **Summary Generation**: Each cluster gets an AI-generated summary
6. **Test Recommendation**: Gemini generates tailored test types

### 3. Results Dashboard
- **Clusters View**: See tests organized by feature groups
- **Aggregated View**: All tests combined and deduplicated
- **Categories View**: Tests organized by type (functional, security, etc.)
- **Export Options**: Download as JSON, CSV, or Markdown

## 🔧 API Endpoints

### Document Management
- `POST /api/documents/upload` - Upload file
- `POST /api/documents/upload-text` - Upload text content
- `GET /api/documents/status/:id` - Check processing status
- `GET /api/documents/list` - List all documents
- `DELETE /api/documents/:id` - Delete document

### Test Recommendations
- `GET /api/tests/recommendations/:documentId` - Get test recommendations
- `POST /api/tests/regenerate/:documentId/:clusterId` - Regenerate cluster tests
- `GET /api/tests/aggregated/:documentId` - Get aggregated tests
- `GET /api/tests/by-category/:documentId` - Get tests by category
- `GET /api/tests/export/:documentId/:format` - Export tests

## 🛠️ Development

### Project Structure

```
RecommendationEngine/
├── backend/
│   ├── services/
│   │   ├── supabaseClient.js      # Database operations
│   │   ├── GeminiService.js       # AI integration
│   │   ├── EmbedService.js        # Text processing & embedding
│   │   ├── ClusterService.js      # Clustering algorithms
│   │   └── DebugLogger.js         # Comprehensive logging
│   ├── routes/
│   │   ├── documentRoutes.js      # Document management
│   │   └── testRoutes.js          # Test recommendations
│   └── server.js                  # Express server
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DocumentUpload.js  # File/text upload
│   │   │   ├── ProgressTracker.js # Processing status
│   │   │   └── TestRecommendation.js # Results display
│   │   ├── services/
│   │   │   └── ApiService.js      # API client
│   │   └── App.js                 # Main application
│   └── public/
└── README.md
```

### Debug Mode

Enable debug mode in the UI to see:
- Detailed processing logs
- API request/response data
- Clustering information
- LLM prompt and response details
- Database operation confirmations

### Environment Variables

#### Backend (.env)
```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE=your_service_role_key
GEMINI_API_KEY=your_gemini_api_key
PORT=5000
NODE_ENV=development
FRONTEND_URL=http://localhost:3000
DEBUG_MODE=true
LOG_LEVEL=debug
```

#### Frontend (.env.local)
```bash
REACT_APP_API_URL=http://localhost:5000/api
```

## 🔍 Key Technologies

### Backend
- **Express.js**: Web framework
- **Supabase**: Database and storage
- **Google Generative AI**: Gemini 2.0 integration
- **ml-kmeans**: Clustering algorithms
- **Winston**: Logging
- **Multer**: File upload handling

### Frontend
- **React 18**: UI framework
- **Tailwind CSS**: Styling
- **Lucide React**: Icons
- **React Hot Toast**: Notifications
- **Axios**: HTTP client

## 📊 Test Recommendation Types

The system can generate any relevant test types including:

### Standard Tests (Must-have)
- Functional testing
- Input validation
- Error handling
- Basic user flows

### Recommended Tests (Advanced)
- Performance testing
- Security testing
- Accessibility testing
- API testing
- Integration testing
- Chaos engineering
- AI-driven testing
- Predictive analytics

## 🚨 Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Check if backend is running on port 5000
   - Verify environment variables are set correctly
   - Check Supabase credentials

2. **Gemini API Errors**
   - Verify API key is valid
   - Check rate limits
   - Ensure proper internet connection

3. **Database Errors**
   - Check Supabase project is active
   - Verify service role permissions
   - Check table creation logs

4. **Upload Errors**
   - File size must be under 10MB
   - Supported formats: txt, doc, docx, pdf
   - Content must be at least 100 characters

### Debug Tips

1. Enable debug mode in the UI
2. Check browser console for detailed logs
3. Monitor backend logs in terminal
4. Use Supabase dashboard to inspect database

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔮 Future Enhancements

- [ ] User authentication and project management
- [ ] Template-based test generation
- [ ] Integration with test management tools
- [ ] Collaborative features
- [ ] Advanced analytics and reporting
- [ ] Custom AI model training
- [ ] Real-time collaboration
- [ ] Test execution integration

---

**Built with ❤️ using React, Supabase, and Gemini 2.0**