from flask import Flask, request
from user_process import compare_passwords, search_for_existing_user, add_new_user
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

debugging = os.getenv("debugging", "false").lower() == "true"
flaskDebugging = os.getenv("flaskDebugging", "false").lower() == "true"

signed_user = "guest"

if debugging:
    print("Debugging is enabled.")
    print("Current signed user: ", signed_user)

@app.route('/')
def landing_page():
    return 'Welcome to the Landing Page!'

@app.route('/login', methods=['POST', 'GET'])
def login():
    global signed_user
    if (signed_user != "guest"):
        if debugging:
            print("User is already signed in as: ", signed_user)
        return {"message": "Redirecting to the chat page."}
    else:
        if debugging:
            print("Post request: ", request.get_json())
            print("Get request: ", request.args)
        if (request.args.get('login_attempt') == "true"):
            username = request.get_json().get('username')
            password = request.get_json().get('password')

            found_password = search_for_existing_user(username)
            if(found_password is None):
                if debugging:
                    print("User not found!")
                return {"message": "User not found!"}
            else:
                if (compare_passwords(username, password)):
                    signed_user = username
                    if debugging:
                        print("Signed in user: ", signed_user)
                    return {"message": "Login successful!"}
                else:
                    if debugging:
                        print("Incorrect password for user: ", username)
                    return {"message": "Incorrect password!"}
        return {"message": "Page refreshed. Login attempt never tried."}

@app.route('/register', methods=['POST', 'GET'])
def register():
    global signed_user
    if (signed_user != "guest"):
        if debugging:
            print("User is already signed in as: ", signed_user)
        return {"message": "Redirecting to the chat page."}
    else:
        if debugging:
            print("Post request: ", request.get_json())
            print("Get request: ", request.args)
        if (request.args.get('register_attempt') == "true"):
            username = request.get_json().get('username')
            password = request.get_json().get('password')

            found_password = search_for_existing_user(username)
            if(found_password is not None):
                if debugging:
                    print("Same username is found on the database!")
                return {"message": "User already exists!"}
            else:
                if debugging:
                    print("Registering new user: ", username)
                if add_new_user(username, password):
                    signed_user = username
                    if debugging:
                        print("New user registered and signed in: ", signed_user)
                    return {"message": "Registration successful! " + signed_user}
                else:
                    if debugging:
                        print("Failed to register new user: ", username)
                    return {"message": "Registration failed!"}
        return {"message": "Page refreshed. Registration attempt never tried."}

@app.route('/chatbot', methods=['POST', 'GET'])
def chatbot():
    if debugging:
        print("Post request: ", request.get_json())
    return {"message": "Chatbot request received!"}

if __name__ == '__main__':
    app.run(debug=flaskDebugging)

