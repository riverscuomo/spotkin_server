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

