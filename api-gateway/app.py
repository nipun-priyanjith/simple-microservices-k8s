from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "API Gateway Running"})

@app.route('/users')
def get_users():
    r = requests.get("http://user-service:5001/")
    return r.json()

@app.route('/products')
def get_products():
    r = requests.get("http://product-service:5002/")
    return r.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
