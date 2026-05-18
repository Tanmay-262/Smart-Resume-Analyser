# Smart Resume Analyzer

An AI-powered web application that analyzes resumes and provides feedback on strengths, weaknesses, and matching roles.

## Features
- Upload PDF or DOCX resumes.
- AI analysis using Google's Gemini API (`gemini-2.5-flash`).
- Displays summary, strengths, weaknesses, suggested roles, and an overall score.

## Tech Stack
- **Frontend**: React, Vite, Axios.
- **Backend**: Flask, Python, `google-generativeai`, `pdfplumber`.

## Setup Instructions

### Backend Setup
1. Navigate to the `backend` directory.
2. Create a virtual environment and activate it.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend` directory and add your API key:
   ```env
   GEMINI_API_KEY=your_actual_api_key
   ```
5. Run the server:
   ```bash
   python app.py
   ```

### Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
