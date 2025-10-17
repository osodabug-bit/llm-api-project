import os
import json
from google import genai
from google.genai import types
from google.genai.errors import APIError

# --- Konfigurācija ---
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.3 # Atbilst prasībai (temperature <= 0.3) 
JD_PATH = "sample_inputs/jd.txt"
PROMPT_PATH = "prompt.md"
CV_FILES = ["sample_inputs/cv1.txt", "sample_inputs/cv2.txt", "sample_inputs/cv3.txt"]
OUTPUT_DIR = "outputs"

# Pārliecināmies, ka ir iestatīta API atslēga
if not os.getenv("GEMINI_API_KEY"):
    print("Kļūda: Lūdzu, iestatiet vides mainīgo GEMINI_API_KEY.")
    exit()

# --- Funkcijas ---

def load_text(file_path: str) -> str:
    """Ielādē teksta saturu no faila."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Kļūda: Fails nav atrasts: {file_path}")
        return ""

def create_report(cv_json: dict, cv_filename: str) -> str:
    """Ģenerē īsu pārskatu Markdown formātā no JSON datiem."""
    report = f"# 📊 CV Vērtēšanas Pārskats: {os.path.basename(cv_filename)}\n\n"
    report += f"## Kopējais Novērtējums\n"
    report += f"| Novērtējums | Vērtība |\n"
    report += f"| :--- | :--- |\n"
    report += f"| **Atbilstības Vērtējums** | **{cv_json.get('match_score', 'N/A')}%** |\n"
    report += f"| **Ieteikums** | **{cv_json.get('verdict', 'N/A').upper()}** |\n\n"

    report += f"## Kopsavilkums\n"
    report += f"> {cv_json.get('summary', 'Nav pieejams.')}\n\n"

    report += f"## Spēcīgās Puses (Strengths)\n"
    if cv_json.get("strengths"):
        for s in cv_json["strengths"]:
            report += f"* {s}\n"
    else:
        report += "* Nav skaidri definētas.\n"

    report += f"\n## Trūkstošās Prasības\n"
    if cv_json.get("missing_requirements"):
        for m in cv_json["missing_requirements"]:
            report += f"* {m}\n"
    else:
        report += "* Nav būtisku trūkstošu prasību.\n"

    return report

def process_cv(cv_path: str, jd_text: str, base_prompt: str, client: genai.Client):
    """Apstrādā vienu CV: izsauc Gemini un ģenerē JSON/Markdown failus."""
    print(f"--- Apstrādā: {os.path.basename(cv_path)} ---")

    # 1. Ielādējam CV tekstu
    cv_text = load_text(cv_path)
    if not cv_text:
        return

    # 2. Sagatavojam galīgo promptu 
    final_prompt = base_prompt.replace("--- JD TEKSTS ---", jd_text).replace("--- CV TEKSTS ---", cv_text)

    # 3. Izsaucam Gemini Flash 2.5 
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=final_prompt,
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                response_mime_type="application/json", # JSON formāts
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "match_score": types.Schema(type=types.Type.INTEGER, description="0-100"),
                        "summary": types.Schema(type=types.Type.STRING),
                        "strengths": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                        "missing_requirements": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                        "verdict": types.Schema(type=types.Type.STRING)
                    }
                )
            )
        )
    except APIError as e:
        print(f"Kļūda, izsaucot Gemini API: {e}")
        return
    except Exception as e:
        print(f"Neparedzēta kļūda: {e}")
        return

    # Pārliecināmies, ka atbilde ir JSON formātā
    try:
        cv_json = json.loads(response.text)
    except json.JSONDecodeError:
        print("Kļūda: Nevar parsēt atbildi kā JSON.")
        print(f"Neapstrādāts Gemini teksts: {response.text}")
        return

    # 4. Saglabājam modeli atbildi kā outputs/cvN.json [cite: 10]
    base_name = os.path.splitext(os.path.basename(cv_path))[0]
    json_output_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(cv_json, f, indent=4, ensure_ascii=False)
    print(f"   -> JSON atskaite saglabāta: {json_output_path}")

    # 5. Ģenerējam īsu pārskatu (Markdown) 
    report_content = create_report(cv_json, cv_path)
    report_output_path = os.path.join(OUTPUT_DIR, f"{base_name}_report.md")
    with open(report_output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"   -> Markdown pārskats saglabāts: {report_output_path}")

# --- Galvenā Programma ---

def main():
    print("🤖 AI CV Vērtētājs Sāk Darbu 🤖")

    # Ielādējam JD un promptu
    jd_text = load_text(JD_PATH)
    base_prompt = load_text(PROMPT_PATH)

    if not jd_text or not base_prompt:
        print("Trūkst būtisku ievaddatu (JD vai prompt.md). Apturam izpildi.")
        return

    # Inicializējam Gemini klientu
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Kļūda, inicializējot Gemini klientu: {e}")
        return

    # 6. Atkārtojam soļus visiem trim CV 
    for cv_file in CV_FILES:
        process_cv(cv_file, jd_text, base_prompt, client)

    print("\n✅ Projekts pabeigts. Rezultāti atrodami 'outputs' direktorijā.")

if __name__ == "__main__":
    main()