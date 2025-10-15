import os
import time
from groq import Groq
from gtts import gTTS


# Direct API key assignment
groq_client = Groq(api_key="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")


def transcribe_audio(filepath):
    """Convert speech file to text using Groq Whisper."""
    try:
        with open(filepath, "rb") as f:
            response = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                language="ta",  # Tamil language code
            )
        return response.text
    except Exception as e:
        return f"[Error] Transcription failed: {e}"


def get_answer(question):
    """Get chatbot response from Groq Llama model in Tamil."""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Updated model
            messages=[
                {"role": "system", "content": "நீங்கள் இந்திய விவசாயிகளுக்கான உதவிகரமான விவசாய சாட்போட். தமிழில் மட்டுமே பதிலளிக்கவும்."},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Error] Could not fetch answer: {e}"


def typing_effect(text, delay=0.03):
    """Print text with typing animation."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


def text_to_speech(text, filename="response_audio"):
    """Convert text to speech and save as MP3 in Tamil."""
    try:
        output_path = f"{filename}.mp3"
        tts = gTTS(text=text, lang='ta')  # Tamil TTS
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"[Error] Could not generate speech: {e}")
        return None


def main():
    mode = input("Choose input type ('text' or 'audio'): ").strip().lower()

    if mode == 'text':
        question = input("Enter your question: ").strip()

    elif mode == 'audio':
        filepath = input("Enter the path to your audio file: ").strip()
        if not os.path.exists(filepath):
            print("❌ File not found.")
            return
        print("🎤 Transcribing audio...")
        question = transcribe_audio(filepath)
        print(f"📝 Transcribed Text: {question}")

    else:
        print("❌ Invalid input type. Use 'text' or 'audio'.")
        return

    print("🤖 Getting response from LLM...")
    answer = get_answer(question)

    print("\n✅ Answer:")
    typing_effect(answer)

    print("\n🔊 Converting answer to Tamil speech...")
    audio_file = text_to_speech(answer, "response_audio")
    if audio_file:
        print(f"🎧 Tamil voice saved to: {audio_file}")
    else:
        print("❌ Failed to create audio file.")


if __name__ == "__main__":
    main()