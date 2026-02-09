import json
import ai_processor

def test_summarize_validation():
    prep = ["Peel banana", "Slice banana"]
    cook = []
    
    print("--- TESTING SUMMARIZATION VALIDATION ---")
    
    # Simulate AI failure (returning only header)
    # We mock _call_gemini inside ai_processor
    original_call = ai_processor._call_gemini
    ai_processor._call_gemini = lambda x: "Prep_steps:\n"
    
    res = ai_processor.summarize_steps(prep, cook)
    print("Result with bad AI response (should fallback):")
    print(repr(res))
    
    ai_processor._call_gemini = original_call

if __name__ == "__main__":
    test_summarize_validation()
