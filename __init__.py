from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def landing_page():
    return 'Welcome to the Landing Page!'

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        print("Post request: ", request.get_json())
        return {"message": "Login successful!"}
    else:
        print("Get request: ", request.args)
        return {"message": "This is a GET request for login."}

if __name__ == '__main__':
    app.run(debug=True)