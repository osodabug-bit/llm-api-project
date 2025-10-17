from google import genai
from google.genai import types
from config import API_KEY 
import json
from datetime import datetime

# Initialize the Gemini client
client = genai.Client(api_key=API_KEY)

# 1. Define the desired JSON structure for the LLM output
response_schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "timestamp": types.Schema(
            type=types.Type.STRING,
            description="The current UTC timestamp in ISO 8601 format."
        ),
        "classification": types.Schema(
            type=types.Type.STRING,
            description="The classified category of the email: support, complaint, general, promo, or spam."
        ),
        "subject": types.Schema(
            type=types.Type.STRING,
            description="A concise subject line for the generated reply."
        ),
        "body": types.Schema(
            type=types.Type.STRING,
            description="The full body of the reply, including the signature 'EasyAgents support team' and written in the original email's language. If the email is classified as spam, this field should be empty or contain a single dash: '-'."
        ),
    },
    required=["timestamp", "classification", "subject", "body"],
)

def classify_and_reply(email_body: str) -> str:
    # 2. Update the prompt to clearly instruct the model on the required content
    prompt = (
        f"Analyze the following email. "
        f"1. Classify it as one of: support, complaint, general, promo, or spam. "
        f"2. Write a short, suitable reply in the same language as the email body. "
        f"3. Use the signature: 'EasyAgents support team'. "
        f"4. If classified as 'spam', **do not** write a reply; the 'body' field must be empty or contain only a dash ('-')."
        f"5. Create a concise 'subject' line for the reply."
        f"6. Populate the 'timestamp' field with the current UTC time in ISO 8601 format (e.g., 2024-01-01T10:00:00Z)."
        f"\n\nEmail: {email_body}"
    )

    # 3. Use the response_mime_type and response_schema to enforce JSON output
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema
        )
    )
    
    # 4. Return the raw JSON string from the model response
    return response.text

while True:
    email_body = input("Paste email body (or type 'quit' to exit): ")
    if email_body.lower() == "quit":
        break
    print("\n--- LLM Output (JSON) ---")
    try:
        json_output = classify_and_reply(email_body)
        # Optional: Print formatted JSON for better readability
        print(json.dumps(json.loads(json_output), indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")
    print("-------------------------\n")