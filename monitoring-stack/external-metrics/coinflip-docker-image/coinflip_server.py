from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.route('/')
def index():
    return "Coinflip server up and running!"

@app.route('/metrics')
def metrics():
    # Simulate a coin flip: 0 or 1
    coinflip_result = random.choice([0, 1])
    # Return the result as a JSON response
    return f"coinflip_result {coinflip_result}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
