import subprocess
import os
import gradio as gr
import requests
import json
from database_manager import get_database_manager
import pandas as pd
from fastapi import FastAPI, Request, Form, Depends, status, HTTPException, Response, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from jose import JWTError, jwt
import pymongo
from typing import Optional
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

OLLAMA_SERVER_URL = "http://localhost:11434"  # Replace this with your actual Ollama server URL if different
WHISPER_MODEL_DIR = "./whisper.cpp/models"  # Directory where whisper models are stored


# FastAPI app and Jinja2 setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"

# MongoDB setup for users
def get_user_collection():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["meeting_summarizer"]
    if "users" not in db.list_collection_names():
        db.create_collection("users")
    return db["users"]

# Dependency to get current user from JWT cookie
def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        users = get_user_collection()
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Sign up page (GET)
@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})

# Sign up (POST)
@app.post("/signup", response_class=HTMLResponse)
def signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    users = get_user_collection()
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match."})
    if users.find_one({"email": email}):
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Email already registered."})
    hashed_password = pwd_context.hash(password)
    user = {"_id": email, "username": username, "email": email, "hashed_password": hashed_password}
    users.insert_one(user)
    # Auto-login after signup
    token = jwt.encode({"sub": user["_id"]}, SECRET_KEY, algorithm=ALGORITHM)
    response = RedirectResponse("/summarize", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

# Sign in page (GET)
@app.get("/signin", response_class=HTMLResponse)
def signin_page(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request, "error": None})

# Sign in (POST)
@app.post("/signin", response_class=HTMLResponse)
def signin(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    users = get_user_collection()
    user = users.find_one({"email": email})
    if not user or not pwd_context.verify(password, user["hashed_password"]):
        return templates.TemplateResponse("signin.html", {"request": request, "error": "Invalid credentials."})
    token = jwt.encode({"sub": user["_id"]}, SECRET_KEY, algorithm=ALGORITHM)
    response = RedirectResponse("/summarize", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

# Profile page (GET)
@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "error": None})

# Update profile (POST)
@app.post("/profile", response_class=HTMLResponse)
def update_profile(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(None), user: dict = Depends(get_current_user)):
    users = get_user_collection()
    update_data = {"username": username, "email": email}
    if password:
        update_data["hashed_password"] = pwd_context.hash(password)
    users.update_one({"_id": user["_id"]}, {"$set": update_data})
    user.update(update_data)
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "error": "Profile updated."})

# Delete profile (POST)
@app.post("/delete_profile", response_class=HTMLResponse)
def delete_profile(request: Request, user: dict = Depends(get_current_user)):
    users = get_user_collection()
    users.delete_one({"_id": user["_id"]})
    response = RedirectResponse("/signup", status_code=302)
    response.delete_cookie("access_token")
    return response

# Logout endpoint
@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    response = RedirectResponse("/signin", status_code=302)
    response.delete_cookie("access_token")
    return response

# Summarize page (GET)
@app.get("/summarize", response_class=HTMLResponse)
def summarize_page(request: Request, user: dict = Depends(get_current_user)):
    db_manager = get_database_manager()
    history = db_manager.get_all_transcriptions()
    return templates.TemplateResponse("summarize.html", {"request": request, "user": user, "result": None, "history": history, "error": None})

# Summarize page (POST)
@app.post("/summarize", response_class=HTMLResponse)
def summarize_upload(request: Request, user: dict = Depends(get_current_user), audio_file: UploadFile = Form(...), context: Optional[str] = Form(""), whisper_model_name: str = Form("base"), llm_model_name: str = Form("llama2")):
    try:
        # Save uploaded file
        audio_path = f"uploads/{audio_file.filename}"
        with open(audio_path, "wb") as f:
            f.write(audio_file.file.read())
        # Run summarization logic
        summary, transcript_file = translate_and_summarize(audio_path, context or "", whisper_model_name, llm_model_name)
        db_manager = get_database_manager()
        history = db_manager.get_all_transcriptions()
        return templates.TemplateResponse("summarize.html", {"request": request, "user": user, "result": summary, "history": history, "error": None})
    except Exception as e:
        db_manager = get_database_manager()
        history = db_manager.get_all_transcriptions()
        return templates.TemplateResponse("summarize.html", {"request": request, "user": user, "result": None, "history": history, "error": str(e)})

# Download summary endpoint
@app.get("/download_summary/{record_id}")
def download_summary(record_id: str, user: dict = Depends(get_current_user)):
    db_manager = get_database_manager()
    record = db_manager.get_transcription_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Summary not found")
    summary_text = record['summary']
    filename = f"summary_{record_id}.txt"
    return StreamingResponse(io.BytesIO(summary_text.encode()), media_type='text/plain', headers={"Content-Disposition": f"attachment; filename={filename}"})

# Download transcript as text
@app.get("/download_transcript_txt/{record_id}")
def download_transcript_txt(record_id: str, user: dict = Depends(get_current_user)):
    db_manager = get_database_manager()
    record = db_manager.get_transcription_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Transcript not found")
    transcript_text = record['transcript']
    filename = f"transcript_{record_id}.txt"
    return StreamingResponse(io.BytesIO(transcript_text.encode()), media_type='text/plain', headers={"Content-Disposition": f"attachment; filename={filename}"})

# Download transcript as PDF (improved formatting)
@app.get("/download_transcript_pdf/{record_id}")
def download_transcript_pdf(record_id: str, user: dict = Depends(get_current_user)):
    db_manager = get_database_manager()
    record = db_manager.get_transcription_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Transcript not found")
    transcript_text = record['transcript']
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("<b>Transcript</b>", styles['Title']), Spacer(1, 12)]
    for para in transcript_text.split('\n\n'):
        story.append(Paragraph(para.replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 12))
    doc.build(story)
    buffer.seek(0)
    filename = f"transcript_{record_id}.pdf"
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"attachment; filename={filename}"})

# Download summary as PDF (improved formatting)
@app.get("/download_summary_pdf/{record_id}")
def download_summary_pdf(record_id: str, user: dict = Depends(get_current_user)):
    db_manager = get_database_manager()
    record = db_manager.get_transcription_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Summary not found")
    summary_text = record['summary']
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("<b>Summary</b>", styles['Title']), Spacer(1, 12)]
    for para in summary_text.split('\n\n'):
        story.append(Paragraph(para.replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 12))
    doc.build(story)
    buffer.seek(0)
    filename = f"summary_{record_id}.pdf"
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"attachment; filename={filename}"})

# History page (ensure all records are fetched and passed to template)
@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request, user: dict = Depends(get_current_user)):
    db_manager = get_database_manager()
    history = db_manager.get_all_transcriptions()
    print('DEBUG: History records fetched:', history)
    return templates.TemplateResponse("history.html", {"request": request, "user": user, "history": history})


def get_available_models() -> list[str]:
    """
    Retrieves a list of all available models from the Ollama server and extracts the model names.

    Returns:
        A list of model names available on the Ollama server.
    """
    response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags")
    if response.status_code == 200:
        models = response.json()["models"]
        llm_model_names = [model["model"] for model in models]  # Extract model names
        return llm_model_names
    else:
        raise Exception(
            f"Failed to retrieve models from Ollama server: {response.text}"
        )


def get_available_whisper_models() -> list[str]:
    """
    Retrieves a list of available Whisper models based on downloaded .bin files in the whisper.cpp/models directory.
    Filters out test models and only includes official Whisper models (e.g., base, small, medium, large).

    Returns:
        A list of available Whisper model names (e.g., 'base', 'small', 'medium', 'large-V3').
    """
    # List of acceptable official Whisper models
    valid_models = ["base", "small", "medium", "large", "large-V3"]

    # Get the list of model files in the models directory
    model_files = [f for f in os.listdir(WHISPER_MODEL_DIR) if f.endswith(".bin")]

    # Filter out test models and models that aren't in the valid list
    whisper_models = [
        os.path.splitext(f)[0].replace("ggml-", "")
        for f in model_files
        if any(valid_model in f for valid_model in valid_models) and "for-tests" not in f
    ]

    # Remove any potential duplicates
    whisper_models = list(set(whisper_models))

    return whisper_models


def summarize_with_model(llm_model_name: str, context: str, text: str) -> str:
    """
    Uses a specified model on the Ollama server to generate a summary.
    Handles streaming responses by processing each line of the response.

    Args:
        llm_model_name (str): The name of the model to use for summarization.
        context (str): Optional context for the summary, provided by the user.
        text (str): The transcript text to summarize.

    Returns:
        str: The generated summary text from the model.
    """
    prompt = f"""You are given a transcript from a meeting, along with some optional context.
    
    Context: {context if context else 'No additional context provided.'}
    
    The transcript is as follows:
    
    {text}
    
    Please summarize the transcript."""

    headers = {"Content-Type": "application/json"}
    data = {"model": llm_model_name, "prompt": prompt}

    response = requests.post(
        f"{OLLAMA_SERVER_URL}/api/generate", json=data, headers=headers, stream=True
    )

    if response.status_code == 200:
        full_response = ""
        try:
            # Process the streaming response line by line
            for line in response.iter_lines():
                if line:
                    # Decode each line and parse it as a JSON object
                    decoded_line = line.decode("utf-8")
                    json_line = json.loads(decoded_line)
                    # Extract the "response" part from each JSON object
                    full_response += json_line.get("response", "")
                    # If "done" is True, break the loop
                    if json_line.get("done", False):
                        break
            return full_response
        except json.JSONDecodeError:
            print("Error: Response contains invalid JSON data.")
            return f"Failed to parse the response from the server. Raw response: {response.text}"
    else:
        raise Exception(
            f"Failed to summarize with model {llm_model_name}: {response.text}"
        )


def preprocess_audio_file(audio_file_path: str) -> str:
    """
    Converts the input audio file to a WAV format with 16kHz sample rate and mono channel.

    Args:
        audio_file_path (str): Path to the input audio file.

    Returns:
        str: The path to the preprocessed WAV file.
    """
    output_wav_file = f"{os.path.splitext(audio_file_path)[0]}_converted.wav"

    # Ensure ffmpeg converts to 16kHz sample rate and mono channel
    cmd = f'ffmpeg -y -i "{audio_file_path}" -ar 16000 -ac 1 "{output_wav_file}"'
    subprocess.run(cmd, shell=True, check=True)

    return output_wav_file


def translate_and_summarize(
    audio_file_path: str, context: str, whisper_model_name: str, llm_model_name: str
) -> tuple[str, str]:
    """
    Translates the audio file into text using the whisper.cpp model and generates a summary using Ollama.
    Also provides the transcript file for download.

    Args:
        audio_file_path (str): Path to the input audio file.
        context (str): Optional context to include in the summary.
        whisper_model_name (str): Whisper model to use for audio-to-text conversion.
        llm_model_name (str): Model to use for summarizing the transcript.

    Returns:
        tuple[str, str]: A tuple containing the summary and the path to the transcript file for download.
    """
    output_file = "output.txt"

    print("Processing audio file:", audio_file_path)

    # Convert the input file to WAV format if necessary
    audio_file_wav = preprocess_audio_file(audio_file_path)

    print("Audio preprocessed:", audio_file_wav)

    # Call the whisper.cpp binary
    import os
    current_dir = os.getcwd()
    whisper_exe = os.path.join(current_dir, "whisper.cpp", "build", "bin", "Release", "whisper-cli.exe")
    whisper_model = os.path.join(current_dir, "whisper.cpp", "models", f"ggml-{whisper_model_name}.bin")
    
    whisper_command = f'"{whisper_exe}" -m "{whisper_model}" -f "{audio_file_wav}" > {output_file}'
    subprocess.run(whisper_command, shell=True, check=True)

    print("Whisper.cpp executed successfully")

    # Read the output from the transcript
    with open(output_file, "r") as f:
        transcript = f.read()

    # Save the transcript to a downloadable file
    transcript_file = "transcript.txt"
    with open(transcript_file, "w") as transcript_f:
        transcript_f.write(transcript)

    # Generate summary from the transcript using Ollama's model
    summary = summarize_with_model(llm_model_name, context, transcript)
    
    # Save to database
    db_manager = get_database_manager()
    audio_filename = os.path.basename(audio_file_path)
    record_id = db_manager.save_transcription(
        audio_filename=audio_filename,
        transcript=transcript,
        summary=summary,
        whisper_model=whisper_model_name,
        llm_model=llm_model_name,
        context=context
    )
    
    print(f"Saved transcription to database with ID: {record_id}")

    # Clean up temporary files
    os.remove(audio_file_wav)
    os.remove(output_file)

    # Return the downloadable link for the transcript and the summary text
    return summary, transcript_file


# Gradio interface
def gradio_app(
    audio, context: str, whisper_model_name: str, llm_model_name: str
) -> tuple[str, str]:
    """
    Gradio application to handle file upload, model selection, and summary generation.

    Args:
        audio: The uploaded audio file.
        context (str): Optional context provided by the user.
        whisper_model_name (str): The selected Whisper model name.
        llm_model_name (str): The selected language model for summarization.

    Returns:
        tuple[str, str]: A tuple containing the summary text and a downloadable transcript file.
    """
    return translate_and_summarize(audio, context, whisper_model_name, llm_model_name)


# Main function to launch the Gradio interface
if __name__ == "__main__":
    # Retrieve available models for Gradio dropdown input
    ollama_models = get_available_models()  # Retrieve models from Ollama server
    whisper_models = (
        get_available_whisper_models()
    )  # Dynamically detect downloaded Whisper models

    # Ensure the first model is selected by default
    iface = gr.Interface(
        fn=gradio_app,
        inputs=[
            gr.Audio(type="filepath", label="Upload an audio file"),
            gr.Textbox(
                label="Context (optional)",
                placeholder="Provide any additional context for the summary",
            ),
            gr.Dropdown(
                choices=whisper_models,
                label="Select a Whisper model for audio-to-text conversion",
                value=whisper_models[0],
            ),
            gr.Dropdown(
                choices=ollama_models,
                label="Select a model for summarization",
                value=ollama_models[0] if ollama_models else None,
            ),
        ],
        outputs=[
            gr.Textbox(
                label="Summary",
                show_copy_button=True,
            ),  # Display the summary generated by the Ollama model
            gr.File(
                label="Download Transcript"
            ),  # Provide the transcript as a downloadable file
        ],
        analytics_enabled=False,
        title="Meeting Summarizer",
        description="Upload an audio file of a meeting and get a summary of the key concepts discussed.",
    )

    iface.launch(debug=True)
