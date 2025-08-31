from flask import Flask, jsonify
import os
from flask_cors import CORS
from utils.garmin import fetch_all_users  

app = Flask(__name__)
CORS(app)

@app.route("/api/body-battery")
def get_data():
    return jsonify(fetch_all_users())



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)