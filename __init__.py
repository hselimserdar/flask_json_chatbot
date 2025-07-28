from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def landing_page():
    return 'Welcome to the Landing Page!'

@app.route('/login', methods=['POST'])
def login():
    print(request.get_json())
    return {"message": "Login successful!"}

'''
@app.route('/get/login', methods=['GET'])
def get_login():
    print(request.args.get('username'))
    return {"message": "This is a GET request for login."}
'''
    
if __name__ == '__main__':
    app.run(debug=True)