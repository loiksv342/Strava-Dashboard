
import pandas as pd
from sklearn.linear_model import LinearRegression 
import numpy as np
import requests
class StravaModel:
    def __init__(self):
        self.model = LinearRegression()
        self.trained = False
        self.feature_names = ['distance', 'average_speed']
    def fetch_data(self, access_token):
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"per_page": 100}
        )
        data = response.json()
        return pd.DataFrame(data)
    def prepare_data(self, df):
        # przygotowanie danych treningowych
        df = df.fillna(0)
        X = df[['distance', 'average_speed']]
        y = df['moving_time']
        
        return X, y
    def train(self, access_token):
        df = self.fetch_data(access_token)
        X, y = self.prepare_data(df)
        self.model.fit(X, y)
        self.trained = True
    def predict(self, features):
        if not self.trained:
            raise Exception("Model not trained yet!")
        
        # Użyj DataFrame z nazwami cech, aby uniknąć ostrzeżenia
        X_new = pd.DataFrame([features], columns=self.feature_names)
        return self.model.predict(X_new)[0]
    def predict_for_distance(self, distance_km, average_speed_kmh):
        """
        Przewiduje czas dla konkretnego dystansu i średniej prędkości
        
        Args:
            distance_km: dystans w kilometrach
            average_speed_kmh: średnia prędkość w km/h
        
        Returns:
            przewidywany czas w sekundach
        """
        distance_m = distance_km * 1000  # konwersja na metry
        average_speed_ms = average_speed_kmh / 3.6  # konwersja na m/s
        
        features = [distance_m, average_speed_ms]
        return self.predict(features)
    def predict_5km(self, average_speed_kmh):
        """Przewiduje czas na 5 km"""
        return self.predict_for_distance(5, average_speed_kmh)
    def predict_10km(self, average_speed_kmh):
        """Przewiduje czas na 10 km"""
        return self.predict_for_distance(10, average_speed_kmh)
    def predict_20km(self, average_speed_kmh):
        """Przewiduje czas na 20 km"""
        return self.predict_for_distance(20, average_speed_kmh)
    def predict_marathon(self, average_speed_kmh):
        """Przewiduje czas na maraton (42.195 km)"""
        return self.predict_for_distance(42.195, average_speed_kmh)
    def predict_all_distances(self, average_speed_kmh):
        """
        Przewiduje czasy dla wszystkich dystansów standardowych
        
        Returns:
            dict z przewidywanymi czasami dla każdego dystansu
        """
        print(f"demo {strava_model.predict_10km}")
        return {
            "5km": self.predict_5km(average_speed_kmh),
            "10km": self.predict_10km(average_speed_kmh),
            "20km": self.predict_20km(average_speed_kmh),
            "marathon": self.predict_marathon(average_speed_kmh)
        }
strava_model = StravaModel()
def train_model_if_needed(access_token):
    if not strava_model.trained:
        strava_model.train(access_token)
def format_time(seconds):
    """Formatuje czas w sekundach na czytelny format (HH:MM:SS)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"