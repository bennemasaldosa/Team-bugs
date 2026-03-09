from flask import Flask, request, jsonify, send_from_directory
import os
import re

# Create Flask app
# Point static folder and template folder to the frontend directory so we don't need a separate static folder
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

@app.route('/')
def index():
    """Serve the main frontend page index.html"""
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/generate_schedule', methods=['POST'])
def generate_schedule():
    """
    API endpoint to process prescription instructions
    and return a daily schedule JSON response.
    """
    data = request.json
    instructions = data.get('instructions', '')
    
    # Initialize the required schedule dictionary with 4 time slots
    schedule = {
        "morning": [],
        "afternoon": [],
        "evening": [],
        "night": []
    }
    
    if not instructions:
        return jsonify(schedule)

    # Process instructions line by line
    lines = instructions.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        lower_line = line.lower()
        
        # Determine the medicine name
        # We find all matching keywords and remove them to isolate the medicine name
        keywords = ["after breakfast", "after lunch", "after dinner", "after food", "before sleep", "twice daily"]
        
        matched_keywords = [kw for kw in keywords if kw in lower_line]
        
        # Extract medicine name by removing all keywords from the line
        medicine = line
        for kw in matched_keywords:
            medicine = re.sub(rf'(?i){re.escape(kw)}', '', medicine)
            
        # Clean up any extra spaces or punctuation
        medicine = medicine.strip(' ,-:')
            
        if not medicine:
            continue

        # Keywords detection based on the user's requirements
        is_morning = "after breakfast" in lower_line
        is_afternoon = "after lunch" in lower_line or "after food" in lower_line or "twice daily" in lower_line
        is_evening = "after dinner" in lower_line or "twice daily" in lower_line
        is_night = "before sleep" in lower_line
        
        # Append medicine to the correct lists
        if is_morning:
            schedule["morning"].append(medicine)
        if is_afternoon:
            schedule["afternoon"].append(medicine)
        if is_evening:
            schedule["evening"].append(medicine)
        if is_night:
            schedule["night"].append(medicine)
            
        # If no explicit timing was found, we add it to a generic slot or just ignore. 
        # For this application, we only schedule it if it matches the text.
        
    return jsonify(schedule)

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, port=5000)
