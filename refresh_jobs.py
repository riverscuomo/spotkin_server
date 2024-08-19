import requests
import os
from rich import print


def refresh_all_jobs():
    """ To be run as a scheduled job by Heroku scheduler to refresh all jobs """
    print("Running refresh_jobs.py To be run as a scheduled job by Heroku scheduler to refresh all jobs")
    app_url = os.environ.get(
        'APP_URL', 'https://spotkin-1b998975756a.herokuapp.com')
    response = requests.post(f'{app_url}/refresh_jobs')

    if response.status_code == 200:
        print("Jobs refreshed successfully")
        print(response.json())
    else:
        print(f"Error refreshing jobs: Status {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    refresh_all_jobs()
