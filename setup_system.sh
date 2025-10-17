#!/bin/bash

echo "🚀 Setting up Intelligent Test Recommendation System..."

# Backend setup
echo "📦 Setting up Backend..."
cd backend_python

echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

echo "⚙️ Installing additional dependencies for new features..."
pip install langgraph textract

echo "✅ Backend setup complete!"

# Frontend setup
echo "📦 Setting up Frontend..."
cd ../frontend

echo "📦 Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete!"

cd ..

echo "🎉 Setup complete! 

🔧 Next steps:
1. Create a .env file in backend_python with:
   GEMINI_API_KEY=your_gemini_api_key_here
   SUPABASE_URL=your_supabase_url (optional)
   SUPABASE_KEY=your_supabase_key (optional)

2. Start the backend:
   cd backend_python
   uvicorn main:app --reload

3. Start the frontend (in a new terminal):
   cd frontend
   npm start

🌟 Features available:
✅ BRD Upload (PDF, DOCX, TXT, MD support)
✅ Jira Integration & Authentication
✅ User Stories Processing
✅ AI-Powered Gap Analysis (using Gemini AI)
✅ Intelligent Test Recommendations
✅ Step-by-step workflow with progress tracking

🔗 Access the app at: http://localhost:3000
🔗 API docs at: http://localhost:8000/docs
"