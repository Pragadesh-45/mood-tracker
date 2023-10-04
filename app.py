# Import necessary libraries
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_bcrypt import Bcrypt
import os  # Import the os module
from flask_cors import CORS  # Import CORS

# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv()

# Create a Flask web application
app = Flask(__name__)

CORS(app)  # Enable CORS for all routes

# Initialize Flask-Bcrypt for password hashing
bcrypt = Bcrypt(app)

# MongoDB configuration
# Use the environment variable to get the MongoDB URI
mongodb_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongodb_uri)  # Use the URI from the environment variable
db = client["users"]
users_collection = db["users"]
user_data_collection = db["user_data"]


# Define a route for the homepage
@app.route('/')
def index():
    return "Welcome to User API"

# User Registration and Login endpoints

# Endpoint for user registration
@app.route('/register', methods=['POST'])
def register():
    # Extract user data from the request
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    
    # Initialize empty arrays for user journals and form data
    journals_array = []
    forms_data_array = []

    # Check if the user with the provided email already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return jsonify({'message': 'User with this email already exists'}), 400

    # Hash the user's password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create a dictionary with user data
    user_data = {
        'username': username,
        'email': email,
        'password': hashed_password,
        'journals_array': journals_array,
        'forms_data_array': forms_data_array
    }

    # Insert the user data into the database
    user_id = users_collection.insert_one(user_data).inserted_id

    return jsonify({'message': 'User registered successfully', 'user_id': str(user_id)}), 201

# Endpoint for user login
@app.route('/login', methods=['POST'])
def login():
    # Extract email and password from the request
    email = request.json['email']
    password = request.json['password']

    # Find the user with the provided email
    user = users_collection.find_one({'email': email})

    # Check if the user exists and the password is correct
    if user and bcrypt.check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

# Retrieve user information by user ID
@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        user['_id'] = str(user['_id'])  # Convert ObjectId to string
        return jsonify(user), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Delete a user by user ID
@app.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    result = users_collection.delete_one({'_id': ObjectId(user_id)})
    if result.deleted_count == 1:
        return jsonify({'message': 'User deleted successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Journal-related endpoints

# Add a journal entry for a user
@app.route('/journals/<user_id>', methods=['POST'])
def add_user_journal(user_id):
    journal_data = request.json.get('journal_data')

    if not journal_data:
        return jsonify({'message': 'Missing journal_data in the request'}), 400

    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        user['journals_array'].append(journal_data)

        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'journals_array': user['journals_array']}})

        return jsonify({'message': 'Journal added successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Retrieve all journals for a user
@app.route('/journals/<user_id>', methods=['GET'])
def get_user_journals(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        journals = user.get('journals_array', [])
        return jsonify({'journals': journals}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Form data submission and retrieval endpoints

# Submit a form response for a user
@app.route('/forms', methods=['POST'])
def submit_form_response():
    user_id = request.json.get('user_id')
    form_data = request.json.get('form_data')

    if not user_id or not form_data:
        return jsonify({'message': 'Missing user_id or form_data in the request'}), 400

    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        user['forms_data_array'].append(form_data)

        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'forms_data_array': user['forms_data_array']}})

        return jsonify({'message': 'Form response added successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Retrieve all form responses for a user
@app.route('/forms', methods=['GET'])
def get_form_responses():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'message': 'Missing user_id parameter in the request'}), 400

    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        form_responses = user.get('forms_data_array', [])
        return jsonify({'form_responses': form_responses}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Analytics endpoints

# Get the total creative hours for a user
@app.route('/analytics/creative-hours', methods=['GET'])
def get_total_creative_hours():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'message': 'Missing user_id parameter in the request'}), 400

    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        form_responses = user.get('forms_data_array', [])
        total_creative_hours = sum(response.get('creative_hours', 0) for response in form_responses)
        return jsonify({'total_creative_hours': total_creative_hours}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Get mood trends for a user
@app.route('/analytics/mood-trends', methods=['GET'])
def get_mood_trends():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'message': 'Missing user_id parameter in the request'}), 400

    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        form_responses = user.get('forms_data_array', [])
        mood_data = []  # Initialize an empty list to store mood data

        # Extract mood data (e.g., "How was your day" rating) from form responses
        for response in form_responses:
            mood_entry = {
                'date': response.get('date'),  # Assuming you have a 'date' field in your form responses
                'rating': response.get('rating')  # Replace 'rating' with the actual field name for mood data
            }
            mood_data.append(mood_entry)

        return jsonify({'mood_trends': mood_data}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Get daily highlights for a user
@app.route('/analytics/highlights', methods=['GET'])
def get_daily_highlights():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'message': 'Missing user_id parameter in the request'}), 400

    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        form_responses = user.get('forms_data_array', [])
        daily_highlights = []  # Initialize an empty list to store daily highlights

        # Extract portions of daily highlights from form responses
        for response in form_responses:
            daily_highlight_entry = {
                'date': response.get('date'),  # Assuming you have a 'date' field in your form responses
                'highlight': response.get('daily_highlight')  # Replace 'daily_highlight' with the actual field name
            }
            daily_highlights.append(daily_highlight_entry)

        return jsonify({'daily_highlights': daily_highlights}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Run the Flask app if this script is executed
if __name__ == '__main__':
    app.run(debug=True)
