from google import genai
from google.genai import types
from config import API_KEY 
import json
from datetime import datetime
import os # Needed to check if the log file exists

# Initialize the Gemini client
client = genai.Client(api_key=API_KEY)
LOG_FILE = "log.json"

# Define the LLM-generated fields (without timestamp)
llm_response_schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
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
    required=["classification", "subject", "body"],
)

# --- Logging Functions ---

def load_log():
    """Loads existing log entries from the JSON file."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {LOG_FILE} is corrupted or empty. Starting new log.")
                return []
    return []

def log_to_file(original_email: str, llm_response_json: dict):
    """Appends the new email and LLM response to the log file."""
    log_entries = load_log()
    
    new_entry = {
        "original_email": original_email,
        "llm_response": llm_response_json
    }
    
    log_entries.append(new_entry)
    
    with open(LOG_FILE, 'w') as f:
        json.dump(log_entries, f, indent=4)
    print(f"Log updated successfully in {LOG_FILE}.")

# --- LLM Processing Function ---

def classify_and_reply(email_body: str) -> dict:
    """
    Calls the LLM, inserts the system timestamp, and returns the final response as a Python dict.
    """
    # 1. Capture the system timestamp *before* calling the LLM
    current_timestamp = datetime.now().isoformat() + 'Z' # ISO 8601 format + Z for UTC

    # 2. Define the prompt
    prompt = (
        f"Analyze the following email and output a JSON object containing the classification, a subject, and the reply body. "
        f"1. Classify it as one of: support, complaint, general, promo, or spam. "
        f"2. Write a short, suitable reply in the same language as the email body. "
        f"3. Use the signature: 'EasyAgents support team'. "
        f"4. If classified as 'spam', **do not** write a reply; the 'body' field must be empty or contain only a dash ('-')."
        f"5. Create a concise 'subject' line for the reply."
        f"\n\nEmail: {email_body}"
    )

    # 3. Get the JSON response from the LLM
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=llm_response_schema
        )
    )
    
    # 4. Parse the LLM's JSON output
    try:
        llm_data = json.loads(response.text)
    except json.JSONDecodeError:
        return {"error": "LLM returned invalid JSON", "raw_output": response.text}

    # 5. Insert the system-generated timestamp to complete the response
    final_output = {
        "timestamp": current_timestamp,
        "classification": llm_data.get("classification"),
        "subject": llm_data.get("subject"),
        "body": llm_data.get("body"),
    }
    
    return final_output

# --- Main Loop ---

print(f"Starting email classifier. Logs will be saved to {LOG_FILE}.")

while True:
    email_body = input("\nPaste email body (or type 'quit' to exit): ")
    if email_body.lower() == "quit":
        break
    
    print("\n--- LLM Output (JSON) ---")
    try:
        # 1. Get the final response dictionary
        final_response_dict = classify_and_reply(email_body)
        
        # Check for error before logging
        if "error" in final_response_dict:
            print(json.dumps(final_response_dict, indent=2))
        else:
            # 2. Print the formatted JSON output to the console
            print(json.dumps(final_response_dict, indent=2))
            
            # 3. Log the original email and the final response
            log_to_file(email_body, final_response_dict)

    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
    
    print("-------------------------\n")