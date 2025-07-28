from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def landing_page():
    return 'Welcome to the Landing Page!'

@app.route('/login', methords=['POST'])
def login():
    data = request.get_json()
    return data

if __name__ == '__main__':
    app.run()