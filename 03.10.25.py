import google.generativeai as genai
from config import API_KEY

# Configure Gemini
genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"

def generate_email(subject: str, tone: str):
    tone_map = {
        "formal": 0.3,
        "normal": 0.7,
        "creative": 1.0,
        "crazy": 2
    }
    temperature = tone_map.get(tone.lower(), 0.7)

    prompt = f"Write an email with subject: '{subject}' in a {tone} tone."

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": temperature}
    )
    return response.text

if __name__ == "__main__":
    subject = input("Enter email subject: ")
    tone = input("Enter tone (formal, normal, creative): ")
    email_text = generate_email(subject, tone)
    print("\nGenerated Email:\n")
    print(email_text)