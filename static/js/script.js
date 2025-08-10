let distanceChart = null;
let speedChart = null;

function loadActivities() {
    fetch("/activities")
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Server error:', data.error);
                alert('Wystąpił błąd: ' + data.error);
                return;
            }

            const summary = data.summary || {};
            const preview = data.preview || [];
            const recent_rides = preview.slice(0, 5);

            // Aktualizacja podsumowania
            document.getElementById("total_distance").textContent = (summary.total_distance_km ?? 0) + " km";
            document.getElementById("average_speed").textContent = (summary.average_speed_kmh ?? 0) + " km/h";
            document.getElementById("average_hr").textContent = (summary.average_heart_rate_bpm ?? 0) + " bpm";
            document.getElementById("longest_distance_bike").textContent = (summary.longest_distance_bike ?? 0) + " km";
            document.getElementById("total_average_cadence").textContent = (summary.total_average_cadence ?? "N/A") + " cad";
            document.getElementById("total_time_bike").textContent = (summary.total_time_bike ?? 0) + " h";  

            // Listy w HTML
            
            const distanceList = document.querySelector(".distance-list");
            const speedList = document.querySelector(".speed-list");
            const heartRateList = document.querySelector(".heart-rate-list");

            distanceList.innerHTML = "";
            speedList.innerHTML = "";
            heartRateList.innerHTML = "";

            recent_rides.forEach(activity => {
                const distLi = document.createElement("li");
                distLi.textContent = `${activity.name || "Brak nazwy"} - ${(activity.distance / 1000).toFixed(2)} km`;
                distanceList.appendChild(distLi);

                const speedLi = document.createElement("li");
                speedLi.textContent = `${activity.name || "Brak nazwy"} - ${(activity.average_speed * 3.6).toFixed(2)} km/h`;
                speedList.appendChild(speedLi);

                const hrLi = document.createElement("li");
                hrLi.textContent = `${activity.name || "Brak nazwy"} - ${activity.average_heartrate ?? "N/A"} bpm`;
                heartRateList.appendChild(hrLi);
            });

            // Dane do wykresów
            const distanceData = preview.map(a => a.distance / 1000);
            const speedData = preview.map(a => a.average_speed * 3.6);

            // Niszczenie poprzednich wykresów (jeśli istnieją)
            if (distanceChart) {
                distanceChart.destroy();
                distanceChart = null;
            }
            if (speedChart) {
                speedChart.destroy();
                speedChart = null;
            }

            // Tworzenie wykresu dystansu
            const distanceCtx = document.getElementById("distanceChart").getContext("2d");
            const labels = preview.map(a => a.name || "Brak nazwy");
            distanceChart = new Chart(distanceCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Distance (km)',
                        data: distanceData,
                        borderWidth: 1,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    }]
                },
                options: {
                    scales: { y: { beginAtZero: true } }
                }
            });

            // Tworzenie wykresu prędkości
            const speedCtx = document.getElementById("speedChart").getContext("2d");
            speedChart = new Chart(speedCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Speed (km/h)',
                        data: speedData,
                        borderWidth: 1,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        fill: true,
                        tension: 0.3,
                    }]
                },
                options: {
                    scales: { y: { beginAtZero: true } }
                }
            });

        })
        .catch(error => {
            console.error('Error fetching activities:', error);
            let errorMessage = 'Wystąpił błąd podczas ładowania danych';
            if (error.error) {
                errorMessage = error.error;
            } else if (error.message) {
                errorMessage = error.message;
            }
            alert(errorMessage);
        });
}

// Załaduj dane od razu
loadActivities();

