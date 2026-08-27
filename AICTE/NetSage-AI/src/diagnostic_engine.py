import os
import json
import pandas as pd
from google import genai
from google.genai import types
from typing import Dict, Any

from prompts.diagnose_prompt import DiagnosticResult, SYSTEM_PROMPT, generate_prompt
from src.rule_checker import run_deterministic_checks

# Cache the DataFrame so we only read the CSV once when the server starts
_DF_CACHE = None


def get_relevant_reference(symptom: str, max_cases: int = 3) -> str:
    """Dynamically filters the CSV to only include relevant cases, slashing API wait times."""
    global _DF_CACHE
    if _DF_CACHE is None:
        try:
            _DF_CACHE = pd.read_csv("data/cases_dataset_50_final.csv")
        except Exception as e:
            return f"Warning: Could not load dataset: {e}"

    # 1. Extract keywords from the user's prompt
    keywords = set(symptom.lower().replace(',', '').replace('.', '').split())

    # 2. Score each row based on how many keywords match the symptom or expected fault
    def score_row(row):
        text = str(row.get('symptom', '')) + " " + str(row.get('expected_fault', ''))
        row_words = set(text.lower().split())
        return len(keywords.intersection(row_words))

    # 3. Sort and grab only the top matching cases
    _DF_CACHE['score'] = _DF_CACHE.apply(score_row, axis=1)
    top_cases = _DF_CACHE.sort_values(by='score', ascending=False).head(max_cases)

    # 4. Convert to highly token-efficient JSON instead of a bloated string
    clean_cases = top_cases.drop(columns=['score']).to_dict(orient='records')
    return json.dumps(clean_cases, indent=2)


def run_diagnosis(symptom: str, show_outputs: str, api_key: str = None) -> Dict[str, Any]:
    rule_errors = run_deterministic_checks(show_outputs)
    if rule_errors:
        return {
            "is_network_issue": True,
            "root_cause": rule_errors[0]["message"],
            "osi_layer": "Layer 1/2",
            "confidence": "Absolute",
            "evidence": f"Rule triggered: {rule_errors[0]['rule']}",
            "next_command": "Verify interface state",
            "fix_steps": [{"explanation": "Review the deterministic error.", "command": "show run"}]
        }

    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        return {"error": "Missing API Key."}

    client = genai.Client(api_key=key)

    # RAG INJECTION: Only pass the top 3 relevant cases to the AI context!
    ref_data = get_relevant_reference(symptom)

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=generate_prompt(symptom, show_outputs, ref_data),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DiagnosticResult,
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1
            )
        )
        return json.loads(response.text)

    except Exception as e:
        return {"error": f"API Diagnostics failed: {str(e)}"}