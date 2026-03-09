# Prescripto – Never Miss a Dose

A full-stack web application that helps users understand prescription instructions by converting messy medication instructions into a clear daily schedule.

## Tech Stack
-   **Frontend:** HTML, CSS, JavaScript
-   **Backend:** Python, Flask

## Prerequisites
-   Python 3.x
-   pip (Python package manager)

## Installation and Setup

1.  **Navigate to the project directory:**
    ```bash
    cd prescripto
    ```

2.  **Install dependencies:**
    You need Flask installed to run the backend server.
    ```bash
    pip install flask flask-cors
    ```

3.  **Run the Flask application:**
    ```bash
    cd backend
    python app.py
    ```

4.  **Access the application:**
    Open your web browser and go to `http://127.0.0.1:5000/`. The Flask server will serve the frontend automatically.

## How it works
1.  The frontend captures the text from the large text box.
2.  It sends this text via a POST request to the backend at `/generate_schedule`.
3.  The Flask backend uses simple keyword detection logic to route the medicines to morning, afternoon, evening, or night.
4.  The JSON response is caught by the frontend and presented dynamically on the 4 time cards.
