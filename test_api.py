# test_api.py
import os
from groq import Groq

def test_groq_api():
    try:
        # Test with your API key
        api_key = "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"
        client = Groq(api_key=api_key)
        
        # Test listing models
        models = client.models.list()
        print("✅ API Connection Successful!")
        print("Available models:")
        for model in models.data[:5]:  # Show first 5 models
            print(f"  - {model.id}")
        
        # Test a simple chat
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=10
        )
        print(f"✅ Chat test successful: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        print("Please check your API key and internet connection.")

if __name__ == "__main__":
    test_groq_api()