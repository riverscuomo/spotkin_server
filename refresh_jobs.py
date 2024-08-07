import requests


def refresh_all_jobs():
    response = requests.post(
        'https://spotkin.herokuapp.com/refresh_jobs')
    print(response.json())


if __name__ == "__main__":
    refresh_all_jobs()
