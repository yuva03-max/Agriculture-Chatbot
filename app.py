# app.py 
import os
import random
import time
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from gtts import gTTS
from groq import Groq
import concurrent.futures
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'webm', 'wav', 'mp3', 'm4a', 'mpga', 'ogg'}

# Initialize Groq client with direct API key
groq_client = None
api_status = "disconnected"

def initialize_groq_client():
    global groq_client, api_status
    
    # Direct API key assignment
    GROQ_API_KEY = "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"
    
    if not GROQ_API_KEY:
        print("❌ No GROQ_API_KEY found")
        api_status = "no_key"
        return None
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # Test the connection with a simple request using updated model
        test_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Updated model
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        print("✅ Groq API connected successfully!")
        api_status = "connected"
        return client
        
    except Exception as e:
        print(f"❌ Groq API connection failed: {e}")
        api_status = "invalid_key"
        return None

# Initialize the client
groq_client = initialize_groq_client()

# Thread pool for parallel processing
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def transcribe_audio_groq(filepath):
    """Fast audio transcription with error handling."""
    if not groq_client:
        return None
        
    try:
        with open(filepath, "rb") as f:
            response = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                language="ta",  # Tamil language code
                prompt="விவசாயம், பயிர்கள், தமிழ்நாடு, வேளாண்மை"
            )
            return response.text
    except Exception as e:
        app.logger.error(f"Transcription error: {e}")
        return None

def get_answer_groq(question):
    """Fast LLM response optimized for Tamil Nadu agriculture."""
    if not groq_client:
        return None
        
    try:
        # Tamil Nadu specific context in Tamil
        system_prompt = """நீங்கள் தமிழ்நாடு விவசாயிகளுக்கான விவசாய நிபுணர் சாட்போட். 
        தமிழில் சுருக்கமான, நடைமுறை அறிவுரைகளை வழங்குங்கள். கவனம் செலுத்த வேண்டியவை:
        - தமிழ்நாடு பயிர்கள்: நெல், கரும்பு, தேங்காய், வாழை, பருத்தி, வேர்கடலை
        - பிராந்திய காலநிலை: வெப்பமண்டல, பருவமழை வடிவங்கள்
        - உள்ளூர் விவசாய முறைகள்
        - தமிழ்நாடு விவசாயிகளுக்கான அரசு திட்டங்கள்
        - தமிழ்நாட்டில் சந்தை விலைகள்
        - பிராந்திய பயிர்களுக்கான பூச்சி கட்டுப்பாடு
        பதில்களை 150 சொற்களுக்குள் வைத்து மிகவும் நடைமுறைத்துவமிக்கதாக வைக்கவும். தமிழில் மட்டுமே பதிலளிக்கவும்."""
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Updated model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        app.logger.error(f"LLM error: {e}")
        return None

def text_to_audio(text, filename):
    """Fast text-to-speech conversion in Tamil."""
    try:
        # Limit text length for faster TTS
        if len(text) > 500:
            text = text[:500] + "..."
            
        # Tamil TTS
        tts = gTTS(text=text, lang='ta', slow=False)
        audio_path = os.path.join("static", "audio", f"{filename}.mp3")
        tts.save(audio_path)
        return f"/static/audio/{filename}.mp3"
    except Exception as e:
        app.logger.error(f"TTS error: {e}")
        return None

def cleanup_file(filepath):
    """Clean up temporary files."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        app.logger.error(f"Cleanup error: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Optimized chat endpoint with parallel processing."""
    try:
        start_time = time.time()
        
        if not groq_client:
            error_msg = {
                "no_key": "API key not configured.",
                "invalid_key": "Invalid API key.",
                "disconnected": "API service unavailable."
            }
            return jsonify({
                'text': f'Error: {error_msg.get(api_status, "API service unavailable")}',
                'voice': None
            }), 503
        
        if 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file and audio_file.filename != '' and allowed_file(audio_file.filename):
                filename = secure_filename(f"{int(time.time())}_{audio_file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                audio_file.save(filepath)

                # Process transcription
                transcription = transcribe_audio_groq(filepath)
                cleanup_file(filepath)

                if not transcription:
                    return jsonify({'text': 'Error: Could not transcribe audio. Please try again.', 'voice': None}), 500

                # Process LLM response
                answer = get_answer_groq(transcription)
                if not answer:
                    return jsonify({'text': 'Error: Could not generate response. Please try again.', 'voice': None}), 500

                # Generate audio in Tamil
                voice_filename = f"voice_{int(time.time())}_{random.randint(1000,9999)}"
                audio_url = text_to_audio(answer, voice_filename)

                processing_time = time.time() - start_time
                app.logger.info(f"Audio request processed in {processing_time:.2f}s")
                
                return jsonify({
                    'text': f"🎤 உங்கள் கேள்வி: {transcription}\n\n🌾 பதில்: {answer}",
                    'voice': audio_url
                })
            else:
                return jsonify({'text': 'Invalid audio file. Please check the format.', 'voice': None}), 400

        elif 'text' in request.form:
            question = request.form['text'].strip()
            
            if not question:
                return jsonify({'text': 'Please enter a question.', 'voice': None}), 400

            # Process LLM response
            answer = get_answer_groq(question)
            if not answer:
                return jsonify({'text': 'Error: Could not generate response. Please try again.', 'voice': None}), 500

            # Generate audio in Tamil
            voice_filename = f"voice_{int(time.time())}_{random.randint(1000,9999)}"
            audio_url = text_to_audio(answer, voice_filename)

            processing_time = time.time() - start_time
            app.logger.info(f"Text request processed in {processing_time:.2f}s")
            
            return jsonify({
                'text': answer,
                'voice': audio_url
            })

        return jsonify({'text': 'No valid input provided.', 'voice': None}), 400

    except Exception as e:
        app.logger.error(f"Server error: {e}")
        return jsonify({'text': 'Server busy. Please try again in a moment.', 'voice': None}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    status_messages = {
        "connected": {"status": "healthy", "message": "விவசாய சாட்போட் இயங்குகிறது", "api_connected": True},
        "invalid_key": {"status": "unhealthy", "message": "தவறான API விசை", "api_connected": False},
        "no_key": {"status": "unhealthy", "message": "API விசை இல்லை", "api_connected": False},
        "disconnected": {"status": "unhealthy", "message": "API இணைப்பு இல்லை", "api_connected": False}
    }
    
    status_info = status_messages.get(api_status, {"status": "unknown", "message": "தெரியாத நிலை", "api_connected": False})
    
    return jsonify(status_info), 200 if api_status == "connected" else 500

def cleanup_old_files():
    """Clean up old audio files."""
    try:
        audio_dir = "static/audio"
        if os.path.exists(audio_dir):
            for file in os.listdir(audio_dir):
                if file.endswith(".mp3"):
                    file_path = os.path.join(audio_dir, file)
                    # Remove files older than 1 hour
                    if os.path.getctime(file_path) < time.time() - 3600:
                        os.remove(file_path)
    except Exception as e:
        app.logger.error(f"Cleanup error: {e}")

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static/audio", exist_ok=True)
    
    # Clean up old files on startup
    cleanup_old_files()
    
    print("🚀 Starting Tamil Agriculture Chatbot Server...")
    print("📁 Directories created: uploads, static/audio")
    
    if groq_client:
        print("✅ Groq API is connected and ready!")
        print("🤖 Using model: llama-3.1-8b-instant")
        print("🗣️ Output language: Tamil")
    else:
        print("❌ Groq API connection failed!")
        print("\n💡 The chatbot will work but without AI responses until you fix the API key.")
    
    # Run the app
    app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)