# 🚀 Quick Setup Guide

## Prerequisites
- Node.js 16+ and npm
- Supabase account ([supabase.com](https://supabase.com))
- Google AI Studio account for Gemini API ([aistudio.google.com](https://aistudio.google.com))

## Step-by-Step Setup

### 1. Get Your API Keys

#### Supabase Setup:
1. Create a new project at [supabase.com](https://supabase.com)
2. Go to Settings → API
3. Copy your:
   - Project URL
   - `anon public` key
   - `service_role` key

#### Gemini API Setup:
1. Visit [Google AI Studio](https://aistudio.google.com)
2. Create a new API key
3. Copy the API key

### 2. Clone and Install

```bash
# Clone the repository
git clone <your-repo-url>
cd RecommendationEngine

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install
```

### 3. Configure Environment Variables

#### Backend Configuration:
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with your actual values:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE=your_service_role_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Frontend Configuration:
```bash
cd frontend
cp .env.example .env.local
```

The default values should work, but you can customize if needed.

### 4. Start the Application

#### Terminal 1 - Backend:
```bash
cd backend
npm run dev
```
Backend will start on `http://localhost:5000`

#### Terminal 2 - Frontend:
```bash
cd frontend
npm start
```
Frontend will start on `http://localhost:3000`

### 5. First Run

1. Open `http://localhost:3000` in your browser
2. The database tables will be created automatically on first API call
3. Upload a test document or paste some content
4. Watch the AI process your document!

## Troubleshooting

### Backend Won't Start:
- Check if your API keys are correctly set in `.env`
- Ensure Supabase project is active
- Verify Node.js version (16+)

### Database Errors:
- Check Supabase service role key has proper permissions
- Verify your Supabase project URL is correct

### Gemini API Errors:
- Ensure your API key is valid and has quota
- Check if Gemini API is available in your region

### Frontend Issues:
- Ensure backend is running on port 5000
- Check browser console for errors
- Verify `REACT_APP_API_URL` in `.env.local`

## Test the Application

### Sample Content to Test:
```
User Story 1: As a customer, I want to register for an account so that I can access personalized features.

Acceptance Criteria:
- User can enter email, password, and confirm password
- System validates email format and password strength
- User receives confirmation email
- Account is created with pending status until email verification

User Story 2: As a customer, I want to login to my account so that I can access my dashboard.

Acceptance Criteria:
- User can enter email and password
- System authenticates credentials
- User is redirected to dashboard on successful login
- Error message displayed for invalid credentials
```

This should generate test recommendations for authentication and user management features.

## Next Steps

1. **Explore Features**: Try different document types and see how the AI adapts
2. **Debug Mode**: Enable debug mode to see detailed processing logs
3. **Export Tests**: Use the export feature to download your recommendations
4. **Regenerate**: Try regenerating recommendations for specific clusters

Happy testing! 🎯