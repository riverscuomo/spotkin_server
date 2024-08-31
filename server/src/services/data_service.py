import os
import json
import gzip
import base64
import time
import requests

# Adjust the import path as necessary
from server.src.models.models import db, User, Job, Token


class DataService:
    def get_all_data(self):
        print('Getting all data...')
        users = User.query.all()
        all_data = {}

        for user in users:
            user_data = {
                'jobs': [],
                'token': user.token.token_info if user.token else {},
                'last_updated': user.last_updated,
            }
            for job in user.jobs:
                user_data['jobs'].append({
                    'playlist_id': job.playlist_id,
                    'name': job.name,
                    'scheduled_time': job.scheduled_time,
                    'index': job.index
                })
            all_data[user.id] = user_data

        return all_data

    def store_job_and_token(self, user_id, job, token_info):
        print('Storing job and token')
        user = User.query.get(user_id)

        if not user:
            user = User(id=user_id, last_updated=int(time.time()))
            db.session.add(user)

        if user.token:
            user.token.token_info = token_info
        else:
            token = Token(user_id=user_id, token_info=token_info)
            db.session.add(token)

        job_exists = False
        for existing_job in user.jobs:
            if existing_job.playlist_id == job['playlist_id']:
                existing_job.name = job.get('name', existing_job.name)
                existing_job.scheduled_time = job.get(
                    'scheduled_time', existing_job.scheduled_time)
                existing_job.index = job.get('index', existing_job.index)
                job_exists = True
                break

        if not job_exists:
            new_job = Job(
                user_id=user_id,
                playlist_id=job['playlist_id'],
                name=job['name'],
                scheduled_time=job.get('scheduled_time'),
                index=job.get('index')
            )
            db.session.add(new_job)

        user.last_updated = int(time.time())
        db.session.commit()

    def delete_job(self, user_id, job_index=None):
        user = User.query.get(user_id)
        if not user:
            return

        if job_index is not None and 0 <= job_index < len(user.jobs):
            job_to_delete = user.jobs[job_index]
            db.session.delete(job_to_delete)
        else:
            db.session.delete(user)

        db.session.commit()


# class DataService:
#     def get_all_data(self):
#         print('Getting all data...')
#         data_str = os.environ.get('SPOTKIN_DATA', '{}')
#         if not data_str or data_str == '{}':
#             print("No data found in SPOTKIN_DATA, returning empty dictionary.")
#             return {}
#         try:
#             return json.loads(data_str)
#         except json.JSONDecodeError:
#             return self._decompress_json(data_str)

#     def store_job_and_token(self, user_id, job, token_info):
#         print('Storing job and token')
#         all_data = self.get_all_data()
#         self.print_all_jobs(all_data)

#         if user_id not in all_data:
#             all_data[user_id] = {'jobs': [], 'token': token_info,
#                                  'last_updated': int(time.time())}

#         # Check if the job already exists based on playlist_id
#         job_exists = False
#         for existing_job in all_data[user_id]['jobs']:
#             if existing_job['playlist_id'] == job['playlist_id']:
#                 # Update existing job
#                 existing_job.update(job)
#                 job_exists = True
#                 break

#         if not job_exists:
#             # Add new job if it doesn't exist
#             all_data[user_id]['jobs'].append(job)

#         all_data[user_id]['last_updated'] = int(time.time())
#         all_data[user_id]['token'] = token_info

#         compressed = self._compress_json(all_data)
#         os.environ['SPOTKIN_DATA'] = compressed
#         self._update_heroku_config(compressed)

#     def print_all_jobs(self, all_data):
#         print('\nAll data:')
#         i = 1
#         for user, value in all_data.items():
#             jobs = value.get('jobs', [])
#             for job_entry in jobs:
#                 scheduled_time = job_entry.get('scheduled_time')
#                 playlist_id = job_entry.get('playlist_id')
#                 name = job_entry.get('name')
#                 index = job_entry.get('index')
#                 print(
#                     f'{i}. {user} "{name}", Scheduled Time: {scheduled_time}, Index: {index}, Playlist ID: {playlist_id}')
#                 i += 1

#     def delete_job(self, user_id, job_index=None):
#         all_data = self.get_all_data()
#         if user_id in all_data:
#             if job_index is not None:
#                 jobs = all_data[user_id].get('jobs', [])
#                 if 0 <= job_index < len(jobs):
#                     del jobs[job_index]
#                     all_data[user_id]['jobs'] = jobs
#             else:
#                 del all_data[user_id]
#             os.environ['SPOTKIN_DATA'] = self._compress_json(all_data)

#     def _compress_json(self, data):
#         json_str = json.dumps(data)
#         compressed = gzip.compress(json_str.encode('utf-8'))
#         return base64.b64encode(compressed).decode('utf-8')

#     def _decompress_json(self, compressed_str):
#         try:
#             decoded = base64.b64decode(compressed_str)
#             decompressed = gzip.decompress(decoded)
#             return json.loads(decompressed.decode('utf-8'))
#         except Exception as e:
#             print(f"Error decompressing JSON: {str(e)}, returning as is")
#             return json.loads(compressed_str)

#     def _update_heroku_config(self, compressed_data):
#         heroku_api_key = os.environ.get('HEROKU_API_KEY')
#         app_name = os.environ.get('HEROKU_APP_NAME')
#         if heroku_api_key and app_name:
#             url = f"https://api.heroku.com/apps/{app_name}/config-vars"
#             headers = {
#                 "Accept": "application/vnd.heroku+json; version=3",
#                 "Authorization": f"Bearer {heroku_api_key}",
#                 "Content-Type": "application/json",
#             }
#             payload = {"SPOTKIN_DATA": compressed_data}
#             response = requests.patch(url, headers=headers, json=payload)
#             if response.status_code == 200:
#                 print("Successfully updated Heroku config var")
#             else:
#                 print(
#                     f"Failed to update Heroku config var. Status code: {response.status_code}")