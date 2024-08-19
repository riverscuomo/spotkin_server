
import os
import json
import gzip
import base64
import time
import requests


class DataService:
    def get_all_data(self):
        data_str = os.environ.get('SPOTKIN_DATA', '{}')
        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            return self._decompress_json(data_str)

    def store_job_and_token(self, user_id, job, token_info):
        print('Storing job and token')
        all_data = self.get_all_data()
        print(all_data)
        all_data[user_id] = {
            'job': job,
            'token': token_info,
            'last_updated': int(time.time()),
        }
        compressed = self._compress_json(all_data)
        os.environ['SPOTKIN_DATA'] = compressed
        self._update_heroku_config(compressed)

    def delete_job(self, user_id):
        all_jobs = self.get_all_data()
        if user_id in all_jobs:
            del all_jobs[user_id]
            os.environ['SPOTKIN_DATA'] = json.dumps(all_jobs)

    def _compress_json(self, data):
        json_str = json.dumps(data)
        compressed = gzip.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')

    def _decompress_json(self, compressed_str):
        try:
            decoded = base64.b64decode(compressed_str)
            decompressed = gzip.decompress(decoded)
            return json.loads(decompressed.decode('utf-8'))
        except Exception as e:
            print(f"Error decompressing JSON: {str(e)}, returning as is")
            return json.loads(compressed_str)

    def _update_heroku_config(self, compressed_data):
        heroku_api_key = os.environ.get('HEROKU_API_KEY')
        app_name = os.environ.get('HEROKU_APP_NAME')
        if heroku_api_key and app_name:
            url = f"https://api.heroku.com/apps/{app_name}/config-vars"
            headers = {
                "Accept": "application/vnd.heroku+json; version=3",
                "Authorization": f"Bearer {heroku_api_key}",
                "Content-Type": "application/json",
            }
            payload = {"SPOTKIN_DATA": compressed_data}
            response = requests.patch(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Successfully updated Heroku config var")
            else:
                print(
                    f"Failed to update Heroku config var. Status code: {response.status_code}")
