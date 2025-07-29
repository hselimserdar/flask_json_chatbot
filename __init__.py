from flask import Flask, request
import sqlite3

app = Flask(__name__)

debugging = True

global signed_user
signed_user = "guest"

if debugging:
    print("Debugging is enabled.")

@app.route('/')
def landing_page():
    return 'Welcome to the Landing Page!'

@app.route('/login', methods=['POST', 'GET'])
def login():
    if (signed_user != "guest"):
        if debugging:
            print("User is already signed in as: ", signed_user)
        return {"message": "Redirecting to the chat page."}
    else:
        if debugging:
            print("Post request: ", request.get_json())
            print("Get request: ", request.args)
        if (request.args.get('login_attempt') == "true"):
            found_password = search_for_existing_user(request.get_json('username'))
            if(found_password is None):
                if debugging:
                    print("User not found!")
                return {"message": "User not found!"}
            else:
                if (request.get_json('password') == found_password):
                    signed_user = request.get_json('username')
                    if debugging:
                        print("Signed in user: ", signed_user)
                    return {"message": "Login successful!"}
                else:
                    if debugging:
                        print("Incorrect password for user: ", request.get_json('username'))
                    return {"message": "Incorrect password!"}
        return {"message": "Page refreshed. Login attempt never tried."}

@app.route('/register', methods=['POST', 'GET'])
def register():
    if (signed_user != "guest"):
        if debugging:
            print("User is already signed in as: ", signed_user)
        return {"message": "Redirecting to the chat page."}
    else:
        if debugging:
            print("Post request: ", request.get_json())
            print("Get request: ", request.args)
        if (request.args.get('register_attempt') == "true"):
            found_password = search_for_existing_user(request.get_json('username'))
            if(found_password is not None):
                if debugging:
                    print("Same username is found on the database!")
                return {"message": "User already exists!"}
            else:
                if debugging:
                    print("Registering new user: ", request.get_json('username'))
                if add_new_user(request.get_json('username'), request.get_json('password')):
                    signed_user = request.get_json('username')
                    if debugging:
                        print("New user registered and signed in: ", signed_user)
                    return {"message": "Registration successful!"}
                else:
                    if debugging:
                        print("Failed to register new user: ", request.get_json('username'))
                    return {"message": "Registration failed!"}
        return {"message": "Page refreshed. Registration attempt never tried."}

@app.route('/chatbot', methods=['POST', 'GET'])
def chatbot():
    if debugging:
        print("Post request: ", request.get_json())
    return {"message": "Chatbot request received!"}

if __name__ == '__main__':
    app.run(debug=True)

def search_for_existing_user(username): #returns password if user exists
    database = sqlite3.connect('database.db')
    db_cursor = database.cursor()
    try:
        db_cursor.execute("SELECT username, password FROM user")
        for user in db_cursor.fetchall():
            if user[0] == username:
                if debugging:
                    print("User found: ", user)
                    return user[1]
    except sqlite3.Error as e:
        print("SQLite error occurred:", e)
        return None
    finally:
        db_cursor.close()
        database.close()
    return None

def add_new_user(username, password):
    database = sqlite3.connect('database.db')
    db_cursor = database.cursor()
    
    try:
        db_cursor.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, password))
        database.commit()
        return True
    except sqlite3.Error as e:
        print("SQLite error occurred:", e)
        return False
    finally:
        db_cursor.close()
        database.close()
