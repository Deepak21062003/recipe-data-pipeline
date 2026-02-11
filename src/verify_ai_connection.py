
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

print("--- AI CONNECTION TEST ---")

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ ERROR: GOOGLE_API_KEY environment variable is NOT set.")
    print("Please run: export GOOGLE_API_KEY='your_key_here'")
    exit(1)

print(f"✅ Found API Key: {api_key[:4]}...{api_key[-4:]}")

try:
    print("Connecting to Google Gemini...")
    genai.configure(api_key=api_key)
    
    # List of models to try in order
    model_candidates = [
        'gemini-1.5-flash',
        'gemini-flash-latest', 
        'gemini-1.5-pro',
        'gemini-pro',
        'gemini-2.0-flash-exp'
    ]
    
    success = False
    for m_name in model_candidates:
        try:
            print(f"Attempting: {m_name}")
            model = genai.GenerativeModel(m_name)
            response = model.generate_content("Reply with only: 'AI IS WORKING!'")
            print(f"🎉 SUCCESS with {m_name}!")
            print(f"Response: {response.text.strip()}")
            success = True
            break
        except Exception as e:
            print(f"❌ Failed: {e}")
            
    if success:
        print("\n✅ AI PIPELINE IS READY!")
    else:
        print("\n❌ ALL MODELS FAILED. Check API Key quotas/permissions.")

except Exception as e_outer:
    print(f"\n❌ FATAL ERROR: {e_outer}")
