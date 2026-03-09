import requests

url = 'http://127.0.0.1:5000/generate_schedule'

def test_case(instructions):
    print(f"\n--- Testing: {instructions} ---")
    response = requests.post(url, json={"instructions": instructions})
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.status_code}")

test_case("Paracetamol after breakfast\nAntibiotic twice daily after food\nVitamin D before sleep")
test_case("Aspirin after lunch")
test_case("Medicine with no time")
test_case("Twice daily Heart Meds")
test_case("Random text that doesn't make sense after dinner")
