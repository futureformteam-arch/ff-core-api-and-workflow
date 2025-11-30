import requests
import sys
import time

API_URL = "http://localhost:8000/api/v1"

def wait_for_api():
    print("Waiting for API to be ready...")
    for _ in range(10):
        try:
            response = requests.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("API is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("API failed to start.")
    return False

def test_create_assessment():
    print("\nTesting Assessment Creation...")
    payload = {
        "organization_id": "org_123",
        "sector": "financial"
    }
    response = requests.post(f"{API_URL}/workflow/assessments/", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Created Assessment ID: {data['id']}")
        return data['id']
    else:
        print(f"Failed: {response.text}")
        return None

def test_add_respondent(assessment_id):
    print("\nTesting Add Respondent...")
    payload = {
        "email": "cto@bank.com",
        "role": "CTO"
    }
    response = requests.post(f"{API_URL}/workflow/assessments/{assessment_id}/respondents/", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Added Respondent ID: {data['id']}")
    else:
        print(f"Failed: {response.text}")

def main():
    if not wait_for_api():
        sys.exit(1)
        
    assessment_id = test_create_assessment()
    if assessment_id:
        test_add_respondent(assessment_id)

if __name__ == "__main__":
    main()
