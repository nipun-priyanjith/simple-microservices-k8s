from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def products():
    return jsonify({"products": ["Laptop", "Phone", "Tablet"]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
