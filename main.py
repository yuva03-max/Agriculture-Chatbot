import os
import time
from groq import Groq
from gtts import gTTS


groq_client = Groq(api_key="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")


def transcribe_audio(filepath):
    """Convert speech file to text using Groq Whisper."""
    try:
        with open(filepath, "rb") as f:
            response = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
            )
        return response.text
    except Exception as e:
        return f"[Error] Transcription failed: {e}"


def get_answer(question):
    """Get chatbot response from Groq Llama model."""
    try:
        response = groq_client.chat.completions.create(
            model="whisper-large-v3",
            messages=[
                {"role": "system", "content": "You are a helpful agriculture chatbot for Indian farmers."},
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
    """Convert text to speech and save as MP3."""
    try:
        output_path = f"{filename}.mp3"
        tts = gTTS(text)
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

    print("\n🔊 Converting answer to speech...")
    audio_file = text_to_speech(answer, "response_audio")
    if audio_file:
        print(f"🎧 Voice saved to: {audio_file}")
    else:
        print("❌ Failed to create audio file.")


if __name__ == "__main__":
    main()
