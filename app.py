from flask import Flask, request, redirect, render_template, jsonify, session
from dotenv import load_dotenv
import os
import requests 
import pandas as pd
import time
from model import strava_model, train_model_if_needed

# === Załaduj dane z .env ===
load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

app = Flask(__name__)
app.secret_key = "secret"

def format_time(seconds):
    """Formatuje czas w sekundach na czytelny format (HH:MM:SS)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

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
        f"&response_type=code&redirect_uri=http://127.0.0.1:1234/authorized"
        f"&approval_prompt=auto&scope=activity:read_all"
    )
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
            print(" Błąd podczas odświeżania tokena:", response.text)
            return None

        token_data = response.json()
        if "access_token" not in token_data:
            print("Renspond without token", token_data)
            return None

        session["access_token"] = token_data["access_token"]
        session["refresh_token"] = token_data["refresh_token"]
        session["expires_at"] = token_data["expires_at"]

        print("Access token refreshed.")
        return session["access_token"]

    return access_token

# === Aktywności ===
@app.route('/activities')
def activities():
    access_token = get_valid_token()
    if not access_token:
        return redirect('/authorize')

    sport_type = request.args.get("sport_type")
    if not sport_type:
        sport_type = None

    bike_activities = get_activities(access_token, sport_type=sport_type)

    if not isinstance(bike_activities, list):
        return jsonify({"Sport data is not valid format"}), 400

    total_distance_km = sum(a.get("distance", 0) for a in bike_activities) / 1000 if bike_activities else 0
    total_time_hours = sum(a.get("moving_time", 0) for a in bike_activities) / 3600 if bike_activities else 0
    average_speed_kmh = total_distance_km / total_time_hours if total_time_hours > 0 else 0

    hr_values = [a.get("average_heartrate") for a in bike_activities if a.get("average_heartrate") is not None]
    average_heart_rate = sum(hr_values) / len(hr_values) if hr_values else 0

    longest_distance_bike = max((a.get("distance", 0) for a in bike_activities), default=0) / 1000

    cadence_values = [a.get("average_cadence") for a in bike_activities if a.get("average_cadence") is not None]
    total_average_cadence = round(sum(cadence_values) / len(cadence_values), 1) if cadence_values else "N/A"

    preview = [{
        "name": a.get("name", "Brak nazwy"),
        "distance": a.get("distance", 0),
        "average_speed": a.get("average_speed", 0),
        "start_date": a.get("start_date", ""),
        "sport_type": a.get("sport_type", ""),
        "average_heartrate": a.get("average_heartrate"),
        "moving_time": a.get("moving_time", 0),
        "average_cadence": a.get("average_cadence")
    } for a in bike_activities]

    return jsonify({
        "summary": {
            "total_distance_km": round(total_distance_km, 2),
            "average_speed_kmh": round(average_speed_kmh, 2),
            "average_heart_rate_bpm": round(average_heart_rate, 1),
            "longest_distance_bike": round(longest_distance_bike, 2),
            "total_average_cadence": total_average_cadence if total_average_cadence == "N/A" else round(total_average_cadence, 1),
            "total_time_bike": round(total_time_hours, 1),
            "sport_type": sport_type
        },
        "preview": preview
    })

@app.route('/dashboard')
def dashboard():
    access_token = get_valid_token()
    if not access_token:
        return redirect('/authorize')
    return render_template('dashboard.html')

# === Fetching data from strava api===
def get_activities(access_token, max_pages=1, per_page=10, sport_type=None):
    all_activities = []
    for page in range(1, max_pages + 1):
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"per_page": per_page, "page": page}
        )

        if response.status_code != 200:
            print(f"Błąd API (strona {page}): {response.status_code} - {response.text}")
            break

        try:

            page_activities = response.json()
        except Exception as e:
            print(f"Nie można sparsować odpowiedzi JSON: {e}")
            print(f"Treść odpowiedzi: {response.text}")
            break
        print(f"📦 Strona {page}: pobrano {len(page_activities)} aktywności")

        if not isinstance(page_activities, list) or not page_activities:
            break

        # 👇 Filtrowanie po sport_type, jeśli podano
        if sport_type:
            page_activities = [a for a in page_activities if a.get("sport_type") == sport_type]
        recent_rides = page_activities[:5]
        all_activities.extend(page_activities)

    print(f"DEBUG: Fetched  {len(all_activities)} activities{' type of sport ' + sport_type if sport_type else ''}")
    return all_activities

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/predict_distances', methods=['POST','GET'])
def predict_distances_route():
    token = get_valid_token()
    if not token:
        return redirect('/authorize')

    train_model_if_needed(token)
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    # average_speed_kmh = data.get('average_speed_kmh', 10)  # domyślnie 10 km/h
    average_speed_kmh = 10.91

    try:
        predictions = strava_model.predict_all_distances(average_speed_kmh)
        
        # Console log predykcji
        print(f"🏃 Predykcje dla prędkości {average_speed_kmh} km/h:")
        for distance, time_seconds in predictions.items():
            print(f"  {distance}: {time_seconds:.1f} sekund ({format_time(time_seconds)})")
        
        # Formatuj czasy na czytelny format
        formatted_predictions = {}
        for distance, time_seconds in predictions.items():
            formatted_predictions[distance] = {
                "seconds": round(time_seconds, 1),
                "formatted": format_time(time_seconds)
            }

        return jsonify({
            "average_speed_kmh": average_speed_kmh,
            "predictions": formatted_predictions
        })

    except Exception as e:
        print(f"❌ Błąd predykcji dystansów: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/predict_specific', methods=['POST'])
def predict_specific_route():
    token = get_valid_token()
    if not token:
        return redirect('/authorize')

    train_model_if_needed(token)

    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    distance_km = data.get('distance_km', 5)
    average_speed_kmh = data.get('average_speed_kmh', 10)

    try:
        prediction = strava_model.predict_for_distance(distance_km, average_speed_kmh)
        prediction10 = prediction.predict_10km(average_speed_kmh)
        prediction20 = prediction.predict_20km(average_speed_kmh)
        prediction5 = prediction.predict_5km(average_speed_kmh)
        predictionMarathon = prediction.predict_marathon(average_speed_kmh)
        
        # Console log predykcji
        print(f"🎯 Predykcja dla {distance_km} km przy {average_speed_kmh} km/h: {prediction:.1f} sekund ({format_time(prediction)})")
        
        return jsonify({
            "distance_km": distance_km,
            "average_speed_kmh": average_speed_kmh,
            "predicted_time_seconds": round(prediction, 1),
            "predicted_time_formatted": format_time(prediction),
            "prediction_5km": prediction5,
            "prediction_10km": prediction10,
            "prediction_20km": prediction20,
            "prediction_marathon": predictionMarathon
        })

    except Exception as e:
        print(f"❌ Błąd predykcji specyficznej: {e}")
        return jsonify({"error": str(e)}), 500
@app.route('/prediction')
def prediction():
    return render_template('prediction.html')

@app.route('/demo_data')
def load_demo_data():
    demo_data = pd.read_csv('activities.csv')
@app.route('/save_activities_csv')
def save_activities_csv():
    token = get_valid_token()
    activities_to_save = get_activities(token)
    df = pd.DataFrame(activities_to_save)
    df.to_csv('activities.csv', index=False)
    return render_template('dashboard.html')
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1234, debug=True)
 