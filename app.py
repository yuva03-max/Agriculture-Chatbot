import os
import random
import string
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename
from gtts import gTTS
from groq import Groq


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'webm', 'wav', 'mp3', 'm4a', 'mpga'}


groq_client = Groq(api_key="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")

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def transcribe_audio_groq(filepath):
    """Convert audio file to text using Groq's Whisper API."""
    try:
        with open(filepath, "rb") as f:
            response = groq_client.audio.transcriptions.create(
                model="llama-3.1-8b-instant",
                file=f,
            )
            return response.text
    except Exception as e:
        app.logger.error(f"Error transcribing audio: {e}")
        return f"Error transcribing audio: {str(e)}"

def get_answer_groq(question):
    """Get a chat response from a Groq LLM."""
    try:
        response = groq_client.chat.completions.create(

            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful agriculture chatbot for Indian farmers."},
                {"role": "user", "content": question}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        app.logger.error(f"Error getting answer: {e}")
        return f"Error getting answer: {str(e)}"

def text_to_audio(text, filename):
    """Convert text to speech and save as an MP3 file."""
    try:
        tts = gTTS(text, lang='en')
        audio_path = os.path.join("static", "audio", f"{filename}.mp3")
        tts.save(audio_path)
        
        return url_for('static', filename=f'audio/{filename}.mp3')
    except Exception as e:
        app.logger.error(f"Error converting text to audio: {e}")
        return None


@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests from the frontend."""
    try:
        if 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file and allowed_file(audio_file.filename):
                filename = secure_filename(audio_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                audio_file.save(filepath)

                transcription = transcribe_audio_groq(filepath)
               
                if "Error" in transcription:
                    return jsonify({'text': transcription, 'voice': None}), 500

                answer = get_answer_groq(transcription)
                
                if "Error" in answer:
                    return jsonify({'text': answer, 'voice': None}), 500

                voice_filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                audio_url = text_to_audio(answer, voice_filename)

                return jsonify({
                    'text': f"🎤 Transcribed: {transcription}\n\n🤖 Answer: {answer}",
                    'voice': audio_url
                })
            
            return jsonify({'text': 'Invalid audio file.', 'voice': None}), 400

        elif 'text' in request.form:
            question = request.form['text']
            answer = get_answer_groq(question)
            
            
            if "Error" in answer:
                return jsonify({'text': answer, 'voice': None}), 500
                
            voice_filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            audio_url = text_to_audio(answer, voice_filename)

            return jsonify({
                'text': answer,
                'voice': audio_url
            })

        return jsonify({'text': 'No valid input found.', 'voice': None}), 400

    except Exception as e:
        app.logger.error(f"Server error during chat request: {e}")
        return jsonify({'text': f"Server error: {str(e)}", 'voice': None}), 500

if __name__ == '__main__':
    
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static/audio", exist_ok=True)
    app.run(debug=True)