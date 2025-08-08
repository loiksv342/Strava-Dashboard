from flask import Flask, request, redirect, render_template, jsonify, session
from dotenv import load_dotenv
import os
import requests 
import pandas as pd
import time

# === Załaduj dane z .env ===
load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

app = Flask(__name__)
app.secret_key = "jakiś_super_sekret"

# === Strona główna ===
@app.route('/')
def index():
    access_token = get_valid_token()
    if not access_token:
        return redirect('/authorize')
    else: 
        return redirect('/dashboard')

@app.route('/about_project')
def about_project():
    return render_template('about_project.html')

# === Autoryzacja Strava ===
@app.route('/authorize')
def authorize():
    auth_url = (
        f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}"
        f"&response_type=code&redirect_uri=http://127.0.0.1:5000/authorized"
        f"&approval_prompt=auto&scope=activity:read_all"
    )
    print("debug: auth_url:", auth_url)
    return redirect(auth_url)

# === Po autoryzacji: zapis tokenów ===
@app.route('/authorized')
def authorized():
    code = request.args.get("code")
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code"
        }
    )

    token_data = response.json()
    print("DEBUG token_data:", token_data)

    if "access_token" not in token_data:
        return f"Token exchange failed: {token_data}"

    session["access_token"] = token_data["access_token"]
    session["refresh_token"] = token_data["refresh_token"]
    session["expires_at"] = token_data["expires_at"]

    return redirect('/dashboard')

# === Automatyczne odświeżanie tokena ===
def get_valid_token():
    access_token = session.get("access_token")
    refresh_token = session.get("refresh_token")
    expires_at = session.get("expires_at")

    if not access_token or not refresh_token or not expires_at:
        return None

    if time.time() > expires_at:
        print("Access token expired. Refreshing...")

        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        )

        if response.status_code != 200:
            print("❌ Błąd podczas odświeżania tokena:", response.text)
            return None

        token_data = response.json()
        if "access_token" not in token_data:
            print("❌ Brak tokena w odpowiedzi:", token_data)
            return None

        session["access_token"] = token_data["access_token"]
        session["refresh_token"] = token_data["refresh_token"]
        session["expires_at"] = token_data["expires_at"]

        print("✅ Access token refreshed.")
        return session["access_token"]

    return access_token

# === Aktywności ===
@app.route('/activities')
def activities():
    access_token = get_valid_token()
    if not access_token:
        return redirect('/authorize')
    activities = get_activities(access_token)
    bike_activities = get_activities(access_token, sport_type="Ride")

    # DEBUG – sprawdź co zawiera bike_activities
    print("DEBUG TYPE:", type(bike_activities))
    print("DEBUG FIRST ITEM:", bike_activities[0] if isinstance(bike_activities, list) else bike_activities)

    if not isinstance(bike_activities, list):
        return "Błąd: dane nie są listą aktywności"

    total_distance_km = sum(activity.get("distance", 0) for activity in bike_activities) / 1000
    total_time_hours = sum(activity.get("moving_time", 0) for activity in bike_activities) / 3600
    average_speed_kmh = total_distance_km / total_time_hours if total_time_hours > 0 else 0
    hr_values = [activity.get("average_heartrate") for activity in bike_activities if activity.get("average_heartrate") is not None]
    run_activities = get_activities(access_token, sport_type="Run")
    average_heart_rate = sum(hr_values) / len(hr_values) if hr_values else 0
    longest_distance_bike = max(activity.get("distance", 0) for activity in bike_activities) / 1000

    preview = [{
        "name": activity.get("name"),
        "distance": activity.get("distance", 0),
        "average_speed": activity.get("average_speed", 0),
        "start_date": activity.get("start_date", "")
    } for activity in bike_activities]

    return jsonify({
        "summary": {
            "total_distance_km": round(total_distance_km, 2),
            "average_speed_kmh": round(average_speed_kmh, 2),
            "average_heart_rate_bpm": round(average_heart_rate, 1),
            "longest_distance_bike": round(longest_distance_bike, 2),
        },
        "preview": preview
    })


@app.route('/dashboard')
def dashboard():
    access_token = get_valid_token()
    if not access_token:
        return redirect('/authorize')
    return render_template('dashboard.html')

# === Pobieranie aktywności ze Strava API ===
def get_activities(access_token, max_pages=5, per_page=100, sport_type=None):
    all_activities = []

    for page in range(1, max_pages + 1):
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"per_page": per_page, "page": page}
        )

        if response.status_code != 200:
            print(f"❌ Błąd API (strona {page}): {response.status_code} - {response.text}")
            break

        try:
            page_activities = response.json()
        except Exception as e:
            print(f"❌ Nie można sparsować odpowiedzi JSON: {e}")
            print(f"Treść odpowiedzi: {response.text}")
            break

        print(f"📦 Strona {page}: pobrano {len(page_activities)} aktywności")

        if not isinstance(page_activities, list) or not page_activities:
            break

        # 👇 Filtrowanie po sport_type, jeśli podano
        if sport_type:
            page_activities = [a for a in page_activities if a.get("sport_type") == sport_type]

        all_activities.extend(page_activities)

    print(f"✅ Łącznie pobrano {len(all_activities)} aktywności{' typu ' + sport_type if sport_type else ''}")
    
    return all_activities
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=1234)
