from flask import Flask, request, jsonify
from instaloader.instaloader_api import InstagramLoader
import os

app = Flask(__name__)
loader = InstagramLoader()

# Path to store session files
SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)


def get_session_file(username: str) -> str:
    """
    Get the path to the session file for a given username.
    """
    return os.path.join(SESSION_DIR, f"{username}.session")


@app.route('/login', methods=['POST'])
def login():
    """
    Log in to Instagram using username and password.
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"status": "failed", "message": "Username and password are required."}), 400

    # Attempt to load an existing session
    session_file = get_session_file(username)
    if os.path.exists(session_file):
        try:
            loader.load_session_from_file(username, session_file)
            return jsonify({"status": "success", "message": "Logged in using existing session."}), 200
        except Exception as e:
            print(f"Failed to load session: {e}")

    # Perform a fresh login
    if loader.login(username, password):
        # Save the session to a file
        loader.save_session_to_file(session_file)
        return jsonify({"status": "success", "message": "Logged in successfully."}), 200
    else:
        return jsonify({"status": "failed", "message": "Login failed. Check your credentials."}), 401


@app.route('/reattempt_login', methods=['POST'])
def reattempt_login():
    """
    Reattempt login if the session is invalid or expired.
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"status": "failed", "message": "Username and password are required."}), 400

    # Perform a fresh login
    if loader.login(username, password):
        # Save the session to a file
        session_file = get_session_file(username)
        loader.save_session_to_file(session_file)
        return jsonify({"status": "success", "message": "Re-login successful."}), 200
    else:
        return jsonify({"status": "failed", "message": "Re-login failed. Check your credentials."}), 401


@app.route('/load_session_from_browser', methods=['POST'])
def load_session_from_browser():
    """
    Load session cookies from a browser.
    """
    data = request.json
    username = data.get('username')  # Username is required to save the session
    browser = data.get('browser')
    cookiefile = data.get('cookiefile')

    if not username or not browser:
        return jsonify({"status": "failed", "message": "Username and browser name are required."}), 400

    if loader.load_session_from_browser(browser, cookiefile):
        # Save the session to a file
        session_file = get_session_file(username)
        loader.save_session_to_file(session_file)
        return jsonify({"status": "success", "message": f"Session loaded from {browser}."}), 200
    else:
        return jsonify({"status": "failed", "message": "Failed to load session from browser."}), 400


@app.route('/download_profile', methods=['POST'])
def download_profile():
    """
    Download content from a profile.
    """
    data = request.json
    profile_name = data.get('profile_name')
    download_posts = data.get('download_posts', True)
    download_stories = data.get('download_stories', False)
    download_highlights = data.get('download_highlights', False)
    download_tagged = data.get('download_tagged', False)
    download_reels = data.get('download_reels', False)
    download_igtv = data.get('download_igtv', False)
    fast_update = data.get('fast_update', False)

    if not profile_name:
        return jsonify({"status": "failed", "message": "Profile name is required."}), 400

    if loader.download_profile(
        profile_name,
        download_posts=download_posts,
        download_stories=download_stories,
        download_highlights=download_highlights,
        download_tagged=download_tagged,
        download_reels=download_reels,
        download_igtv=download_igtv,
        fast_update=fast_update,
    ):
        return jsonify({"status": "success", "message": f"Downloaded content from {profile_name}."}), 200
    else:
        return jsonify({"status": "failed", "message": f"Failed to download content from {profile_name}."}), 400


@app.route('/download_hashtag', methods=['POST'])
def download_hashtag():
    """
    Download posts from a hashtag.
    """
    data = request.json
    hashtag = data.get('hashtag')
    max_count = data.get('max_count')

    if not hashtag:
        return jsonify({"status": "failed", "message": "Hashtag is required."}), 400

    if loader.download_hashtag(hashtag, max_count):
        return jsonify({"status": "success", "message": f"Downloaded posts from #{hashtag}."}), 200
    else:
        return jsonify({"status": "failed", "message": f"Failed to download posts from #{hashtag}."}), 400


@app.route('/download_stories', methods=['POST'])
def download_stories():
    """
    Download stories from a profile.
    """
    data = request.json
    profile_name = data.get('profile_name')

    if not profile_name:
        return jsonify({"status": "failed", "message": "Profile name is required."}), 400

    if loader.download_stories(profile_name):
        return jsonify({"status": "success", "message": f"Downloaded stories from {profile_name}."}), 200
    else:
        return jsonify({"status": "failed", "message": f"Failed to download stories from {profile_name}."}), 400


@app.route('/close', methods=['POST'])
def close():
    """
    Close the Instagram loader.
    """
    loader.close()
    return jsonify({"status": "success", "message": "Loader closed successfully."}), 200


if __name__ == '__main__':
    app.run(debug=True)