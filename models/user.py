# models/user.py

from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask import current_app

mongo = PyMongo()
bcrypt = Bcrypt()


class User:

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def save(self):
        mongo.db.users.insert_one({
            'username': self.username,
            'email': self.email,
            'password': self.password,
        })

    @staticmethod
    def find_by_username(username):
        with current_app.app_context():
            return mongo.db.users.find_one({'username': username})

    @staticmethod
    def check_password(user, password):
        return bcrypt.check_password_hash(user['password'], password)
