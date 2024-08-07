import requests
import os


def refresh_all_jobs():
    print("Refreshing jobs...")
    app_url = os.environ.get('APP_URL', 'https://spotkin.herokuapp.com')
    response = requests.post(f'{app_url}/refresh_jobs')

    if response.status_code == 200:
        print("Jobs refreshed successfully")
        print(response.json())
    else:
        print(f"Error refreshing jobs: Status {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    print("Running refresh_jobs.py")
    refresh_all_jobs()
