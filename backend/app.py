from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
  "temperature": 0.1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
  model_name="gemini-2.5-flash",
  generation_config=generation_config,
)

@app.route('/api/parse', methods=['POST'])
def parse_prescription():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    
    messy_text = data['text']
    
    prompt = f"""
    You are an AI assistant that extracts prescription instructions into a clear daily schedule.
    Extract the medication instructions from the following text and categorize them into four time periods: Morning, Afternoon, Evening, and Night.
    If a time period has no medications, return an empty array for it.

    Text:
    {messy_text}

    Return ONLY a raw JSON object with this exact structure:
    {{
      "Morning": ["Medication A info", ...],
      "Afternoon": ["Medication B info", ...],
      "Evening": ["Medication C info", ...],
      "Night": ["Medication D info", ...]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error generating content: {e}")
        return jsonify({"error": "Failed to parse prescription"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
