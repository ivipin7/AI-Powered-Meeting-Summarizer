# AI-Powered Meeting Summarizer

## Overview

This project is an AI-powered meeting summarizer web application. It allows users to upload audio files of meetings, transcribes the audio using OpenAI Whisper, summarizes the transcript using Llama (or other LLMs), and provides downloadable summaries and transcripts in both text and PDF formats. All user and meeting data is stored in MongoDB (compatible with MongoDB Compass for easy management).

---

## Features

- **Modern Web UI**: Built with FastAPI and Jinja2 templates, styled with Bootstrap for a responsive, user-friendly experience.
- **User Authentication**: Secure sign up, sign in, logout, and profile management (CRUD) with password hashing and JWT authentication.
- **Audio Summarization**: Upload audio files in most common formats (WAV, MP3, OGG, M4A, etc.).
- **Multi-language Transcription**: Whisper supports nearly 100 languages for transcription.
- **English Summarization**: Llama model provides best results for English transcripts.
- **Download Options**: Download both summary and transcript as text or PDF.
- **History Page**: View all previous meeting summaries and transcripts, with download options for each.
- **MongoDB Storage**: All data is stored in a local MongoDB database, viewable and manageable with MongoDB Compass.

---

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- MongoDB installed and running locally (default: `mongodb://localhost:27017/`)
- FFmpeg installed (for audio processing)
- (Optional) MongoDB Compass for GUI database management

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
uvicorn main:app --reload
```
Visit [http://localhost:8000/](http://localhost:8000/) in your browser.

### 4. Using the App
- **Sign Up / Sign In**: Create an account or log in.
- **Summarize**: Upload an audio file, select models, and get your summary and transcript.
- **Download**: Use the dropdowns to download summary or transcript as text or PDF.
- **History**: View all your previous meeting summaries and transcripts on the History page.
- **Profile**: Update your user info or delete your account.

---

## Project Structure
- `main.py` - FastAPI app, routes, and business logic
- `database_manager.py` - MongoDB integration and data management
- `templates/` - Jinja2 HTML templates for UI
- `static/` - Static assets (CSS, JS, etc.)
- `uploads/` - Uploaded audio files (temporary)
- `requirements.txt` - Python dependencies

---

## Notes
- **Audio Input**: Most common audio formats are supported. FFmpeg is used to convert files as needed.
- **Transcription Language**: Whisper can transcribe nearly any language, but summarization is best in English.
- **Database**: All data is stored in the `meeting_summarizer` database, `transcription_history` collection.
- **Security**: Passwords are hashed, and JWT is used for authentication.
- **PDF Generation**: Summaries and transcripts can be downloaded as well-formatted PDFs.

---

## Future Improvements
- Add support for multi-language summarization (with translation step)
- Add admin dashboard and analytics
- Add user roles and permissions
- Deploy to cloud (Heroku, AWS, etc.)

---

## License
See [LICENSE](LICENSE) for details.
