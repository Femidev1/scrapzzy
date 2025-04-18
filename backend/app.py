from flask import Flask, jsonify, send_from_directory
import json
import os

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")

# Serve index.html at root
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

# Serve static assets (JS, CSS, etc.)
@app.route("/<path:path>")
def serve_static(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")  # Fallback for SPA routes

# JSON listings API
@app.route("/listings")
def get_listings():
    try:
        filepath = os.path.join(os.path.dirname(__file__), "listing_history.json")
        if not os.path.exists(filepath):
            return jsonify([])

        with open(filepath, "r") as f:
            data = json.load(f)
        return jsonify(list(data.values()))

    except Exception as e:
        print(f"⚠️ Error reading listings: {e}")
        return jsonify({"error": str(e)}), 500

# Entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)