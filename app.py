from flask import Flask, request, redirect
from flask import jsonify
import os
import requests 
app = Flask(__name__)

# === Autoryzacja ===
@app.route('/authorize')
def authorize():
    client_id = os.getenv('STRAVA_CLIENT_ID')
    redirect_url = "http://127.0.0.1:5000/authorized"
    auth_url = (
        f"https://www.strava.com/oauth/authorize?client_id={client_id}"
        f"&response_type=code&redirect_uri={redirect_url}"
        f"&approval_prompt=auto&scope=activity:read_all"
    )
    print("debug: auth_url: ", auth_url)
    return redirect(auth_url)

# === Callback po autoryzacji ===
@app.route('/authorized')
def authorized():
    code = request.args.get("code")
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": os.getenv("STRAVA_CLIENT_ID"),
            "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
            "code": code,
            "grant_type": "authorization_code"
        }
    )

    token_data = response.json()
    print("DEBUG token_data:", token_data)

    if "access_token" not in token_data:
        return f"Token exchange failed: {token_data}"

    access_token = token_data["access_token"]

    # Możesz dodać tu zapis tokenów do pliku/bazy
    return f"Authorized! Access Token: {access_token}"

# === Pobieranie aktywności ===
def get_activities(access_token):
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    activities = response.json()
    print("DEBUG activities:", activities)
    return activities


@app.route('/activities')
def show_activities():
    access_token = "d29bfc9e780d1c4ccc319999b38fdb3e8fb76806"  # testowo
    activities = get_activities(access_token)
    preview = []
    for act in activities[:10]:
        preview.append({
            "name": act["name"],
            "distance": act["distance"],
            "type": act["type"],
            "moving_time": act["moving_time"],
            "average_speed": act["average_speed"],
            "start_date": act["start_date"],
            "effort": act["effort"],
            "has_heartrate": act["has_heartrate"],
            "average_heartrate": act["average_heartrate"],
            "max_heartrate": act["max_heartrate"],
        })
    return jsonify(preview)