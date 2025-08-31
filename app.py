from flask import Flask, jsonify
from flask_cors import CORS
from utils.garmin import fetch_all_users  

app = Flask(__name__)
CORS(app)

@app.route("/api/body-battery")
def get_data():
    return jsonify(fetch_all_users())

# 🟢 THIS IS CRITICAL
if __name__ == "__main__":
    app.run(debug=True, port=5000)