from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Initialize engines once at module level to avoid reloading spaCy model on every call.
# This makes it super fast during Streamlit reruns.
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def scrub_text(text: str) -> str:
    """
    Analyzes and redacts PII from the given text.
    Replaces names with <PERSON>, emails with <EMAIL_ADDRESS>, etc.
    """
    if not text:
        return text
    
    # We explicitly specify entities to ensure fast and accurate scrubbing of major identifiers
    results = analyzer.analyze(
        text=text, 
        entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"], 
        language='en'
    )
    
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized_result.text

if __name__ == "__main__":
    # Test block for manual verification
    test_string = "My name is Shreyas and my phone number is 9876543210. Email me at test@example.com."
    print("--- Presidio PII Scrubber Test ---")
    print(f"Original: {test_string}")
    print(f"Scrubbed: {scrub_text(test_string)}")
