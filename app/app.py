import os
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["github"]
collection = db["events"]


# Webhook route to handle GitHub events
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "push":
        handle_push_event(data)
    elif (
        event_type == "pull_request"
        and data["action"] == "closed"
        and data["pull_request"]["merged"]
    ):
        handle_merge_event(data)
    elif event_type == "pull_request":
        handle_pull_request_event(data)

    return jsonify({"status": "success"}), 200


# Function to handle push events
def handle_push_event(data):
    author = data["pusher"]["name"]
    to_branch = data["ref"].split("/")[-1]  # Extract branch name from ref
    timestamp = datetime.strptime(
        data["head_commit"]["timestamp"], "%Y-%m-%dT%H:%M:%S%z"
    )

    event_data = {
        "event_type": "push",
        "author": author,
        "from_branch": None,  # No from_branch for push
        "to_branch": to_branch,
        "timestamp": timestamp,
    }
    collection.insert_one(event_data)


# Function to handle pull request events
def handle_pull_request_event(data):
    author = data["pull_request"]["user"]["login"]
    to_branch = data["pull_request"]["base"]["ref"]
    from_branch = data["pull_request"]["head"]["ref"]
    timestamp = datetime.strptime(
        data["pull_request"]["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
    )

    event_data = {
        "event_type": "pull_request",
        "author": author,
        "from_branch": from_branch,
        "to_branch": to_branch,
        "timestamp": timestamp,
    }
    collection.insert_one(event_data)


# Function to handle merge events
def handle_merge_event(data):
    author = data["pull_request"]["user"]["login"]
    from_branch = data["pull_request"]["head"]["ref"]
    to_branch = data["pull_request"]["base"]["ref"]
    timestamp = datetime.strptime(
        data["pull_request"]["merged_at"], "%Y-%m-%dT%H:%M:%SZ"
    )

    event_data = {
        "event_type": "merge",
        "author": author,
        "from_branch": from_branch,
        "to_branch": to_branch,
        "timestamp": timestamp,
    }

    # Insert merge event into MongoDB
    collection.insert_one(event_data)


# Route to retrieve stored events
@app.route("/events", methods=["GET"])
def get_events():
    events = list(collection.find({}, {"_id": 0}))
    return jsonify(events), 200


@app.route("/")
def index():
    return render_template("events.html")


if __name__ == "__main__":
    app.run(port=5000)
