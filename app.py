from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["github_webhooks"]
collection = db["events"]


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    data["timestamp"] = datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
    collection.insert_one(data)
    return jsonify({"status": "success"}), 200


@app.route("/events", methods=["GET"])
def get_events():
    events = list(collection.find({}, {"_id": 0}))
    return jsonify(events), 200


if __name__ == "__main__":
    app.run(port=5000)
