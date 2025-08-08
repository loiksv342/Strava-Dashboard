fetch("/activities")
    .then(response => response.json())
    .then(data => {
      const summary = data.summary;

      document.getElementById("total_distance").textContent = summary.total_distance_km + " km";
      document.getElementById("average_speed").textContent = summary.average_speed_kmh + " km/h";
      document.getElementById("average_hr").textContent = summary.average_heart_rate_bpm + " bpm";
      document.getElementById("longest_distance_bike").textContent = summary.longest_distance_bike + " km";
    })
    .catch(error => {
      console.error("Błąd podczas pobierania danych:", error);
    });
