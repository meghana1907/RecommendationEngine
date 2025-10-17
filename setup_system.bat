@echo off
echo 🚀 Setting up Intelligent Test Recommendation System...

rem Backend setup
echo 📦 Setting up Backend...
cd backend_python

echo 🐍 Installing Python dependencies...
pip install -r requirements.txt

echo ⚙️ Installing additional dependencies for new features...
pip install langgraph textract

echo ✅ Backend setup complete!

rem Frontend setup
echo 📦 Setting up Frontend...
cd ..\frontend

echo 📦 Installing Node.js dependencies...
npm install

echo ✅ Frontend setup complete!

cd ..

echo 🎉 Setup complete! 
echo.
echo 🔧 Next steps:
echo 1. Create a .env file in backend_python with:
echo    GEMINI_API_KEY=your_gemini_api_key_here
echo    SUPABASE_URL=your_supabase_url (optional)
echo    SUPABASE_KEY=your_supabase_key (optional)
echo.
echo 2. Start the backend:
echo    cd backend_python
echo    uvicorn main:app --reload
echo.
echo 3. Start the frontend (in a new terminal):
echo    cd frontend
echo    npm start
echo.
echo 🌟 Features available:
echo ✅ BRD Upload (PDF, DOCX, TXT, MD support)
echo ✅ Jira Integration & Authentication
echo ✅ User Stories Processing
echo ✅ AI-Powered Gap Analysis (using Gemini AI)
echo ✅ Intelligent Test Recommendations
echo ✅ Step-by-step workflow with progress tracking
echo.
echo 🔗 Access the app at: http://localhost:3000
echo 🔗 API docs at: http://localhost:8000/docs

pause