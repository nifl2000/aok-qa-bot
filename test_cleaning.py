import re

def clean_answer(text: str) -> str:
    """Refined cleaning for FAQ answers to preserve structure and fix concatenation."""
    if not text:
        return ""

    # 1. Fix concatenated words like "smartAZuB" or "AuszahlungFremdkunde"
    # Look for lowercase followed by uppercase
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    # 2. Handle line breaks
    # Join "hard breaks": newline followed by lowercase (likely middle of sentence)
    text = re.sub(r"\n([a-z])", r" \1", text)
    
    # 3. Add breaks before semantic headers/tags
    tags = ["Bestandskunde:", "Fremdkunde:", "Hinweis:", "Wichtig:", "Weiterleitung:", "Guten Tag"]
    for tag in tags:
        # Add two newlines before tag if not at start, ensure space after tag
        text = re.sub(f"(?<!^)\\s*({re.escape(tag)})", r"\n\n\1", text)

    # 4. Clean up whitespace
    # Replace single newlines that remain with a space (unless they are part of our double newlines)
    # But wait, we might want to keep some. Let's try to keep newlines followed by uppercase.
    text = text.replace("\n", "TEMP_NL")
    text = re.sub(r"TEMP_NL(TEMP_NL)+", "\n\n", text) # Preserve double breaks
    text = text.replace("TEMP_NL", " ") # Convert single ones to space
    
    # Final polish
    text = re.sub(r"  +", " ", text) # Collapse multiple spaces
    text = re.sub(r"\n\n+", "\n\n", text) # Collapse multiple paragraph breaks
    
    # Fix missing spaces after punctuation (if not already handled)
    text = re.sub(r"([.!?])([A-ZÄÖÜ])", r"\1 \2", text)
    text = re.sub(r":([A-ZÄÖÜ])", r": \1", text)

    return text.strip()

# Test cases
test_texts = [
    "AZuB ProaktivAufruf AZuB smartAZuB smart Erstattung",
    "Bestandskunde:  Nach dem Einreichen Ihrer\nNachweise für die entsprechenden Gesundheitsmaßnahmen werden diese geprüft. Die\nNachweise können nur berücksichtigt werden, wenn sie der AOK bis spätestens\n31.01. des Folgejahres vorliegen.Fremdkunde:\nFür Neukunden erfolgt die\nAuszahlung grds. im Jahr des Mitgliedschafts-beginns nach erfolgreicher\nEchtanmeldung.",
    "Guten Tag Herr/ Frau, vielen Dank für Ihre\nAnfrage.  Bestandskunde:Der Bonus wird grundsätzlich\nnach Prüfung der Nachweise ausgezahlt."
]

if __name__ == "__main__":
    for t in test_texts:
        print("--- ORIGINAL ---")
        print(t)
        print("--- CLEANED ---")
        print(clean_answer(t))
        print("\n")
