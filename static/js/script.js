let currentChart = null;

function loadActivities() {
    const chartSection = document.querySelector(".chart-section");
    let summaryHeading = document.querySelector(".summary-heading");
    let sportSubText = document.querySelector(".sport-subtext");
    chartSection.innerHTML = '<div class="loader"></div>';

    if (document.querySelector("#sport-type-select").value == "All") {
        summaryHeading.innerHTML = "All"
        sportSubText.innerHTML = "Recent activities"
    }

    const sportType = document.getElementById("sport-type-select").value;
    const choosenChart = document.getElementById("chart-select").value;

    let url = "/activities";
    if (sportType && sportType.trim() !== "") {
        url += "?sport_type=" + encodeURIComponent(sportType);
        summaryHeading.textContent = `${sportType} summary`;
        sportSubText.innerHTML = "Recent activities of " + sportType;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            chartSection.innerHTML = "";

            if (data.error) {
                console.error('Server error:', data.error);
                alert('Wystąpił błąd: ' + data.error);
                return;
            }

            const summary = data.summary || {};
            const preview = data.preview || [];
            const recent_rides = preview.slice(0, 5);

            // Podsumowanie
            document.getElementById("total_distance").textContent = (summary.total_distance_km ?? 0) + " km";
            document.getElementById("average_speed").textContent = (summary.average_speed_kmh ?? 0) + " km/h";
            document.getElementById("average_hr").textContent = (summary.average_heart_rate_bpm ?? 0) + " bpm";
            document.getElementById("longest_distance_bike").textContent = (summary.longest_distance_bike ?? 0) + " km";
            document.getElementById("total_average_cadence").textContent = (summary.total_average_cadence ?? "N/A") + " cad";
            document.getElementById("total_time_bike").textContent = (summary.total_time_bike ?? 0) + " h";

            // Listy
            const distanceList = document.querySelector(".distance-list");
            const speedList = document.querySelector(".speed-list");
            const heartRateList = document.querySelector(".heart-rate-list");

            distanceList.innerHTML = "";
            speedList.innerHTML = "";
            heartRateList.innerHTML = "";

            recent_rides.forEach(activity => {
                distanceList.innerHTML += `<li>${activity.name || "Brak nazwy"} - ${(activity.distance / 1000).toFixed(2)} km</li>`;
                speedList.innerHTML += `<li>${activity.name || "Brak nazwy"} - ${(activity.average_speed * 3.6).toFixed(2)} km/h</li>`;
                heartRateList.innerHTML += `<li>${activity.name || "Brak nazwy"} - ${activity.average_heartrate ?? "N/A"} bpm</li>`;
            });

            // Dane do wykresów (kod wykresów pozostaje bez zmian)
            const labels = preview.map(a => a.name || "Brak nazwy");
            const distanceData = preview.map(a => a.distance / 1000);
            const speedData = preview.map(a => a.average_speed * 3.6);

            const sportTypeCounts = {};
            preview.forEach(a => {
                const st = a.sport_type || "Unknown";
                sportTypeCounts[st] = (sportTypeCounts[st] || 0) + 1;
            });
            const pieLabels = Object.keys(sportTypeCounts);
            const pieData = Object.values(sportTypeCounts);

            if (currentChart) {
                currentChart.destroy();
                currentChart = null;
            }

            chartSection.innerHTML = "";
            const canvas = document.createElement("canvas");
            chartSection.appendChild(canvas);

            if (choosenChart === "distance") {
                currentChart = new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [{
                            label: 'Distance (km)',
                            data: distanceData,
                            borderWidth: 1,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        }]
                    },
                    options: { scales: { y: { beginAtZero: true } } }
                });
            } else if (choosenChart === "speed") {
                currentChart = new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels,
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
                    options: { scales: { y: { beginAtZero: true } } }
                });
            } else if (choosenChart === "sport-type-percentage") {
                currentChart = new Chart(canvas, {
                    type: 'pie',
                    data: {
                        labels: pieLabels,
                        datasets: [{
                            label: 'Sport type',
                            data: pieData,
                            backgroundColor: pieLabels.map((_, i) => `hsl(${i * 360 / pieLabels.length}, 70%, 60%)`),
                            borderColor: '#fff',
                            borderWidth: 1,
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'bottom' } }
                    }
                });
            } else {
                chartSection.innerHTML = "<span>Wybierz wykres</span>";
            }

            // ✅ POPRAWKA: Użyj nowego endpointu predict_distances
            const averageSpeedKmh = summary.average_speed_kmh ?? 10; // km/h
            fetchPredictionDistances(averageSpeedKmh);

        })
        .catch(error => {
            console.error('Error fetching activities:', error);
            alert(error.error || error.message || 'Wystąpił błąd podczas ładowania danych');
        });
}

// ✅ NOWA FUNKCJA: Predykcja dla wszystkich dystansów
function fetchPredictionDistances(averageSpeedKmh) {
    fetch('/predict_distances', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({average_speed_kmh: averageSpeedKmh})
    })
    .then(response => response.json())
    .then(data => {
        console.log('Predykcje dla wszystkich dystansów:', data);
        
        // Wyświetl predykcje na stronie
        const predictionsDiv = document.getElementById("predictions_display");
        if (predictionsDiv) {
            let html = `<h4>Predykcje czasów dla ${averageSpeedKmh} km/h:</h4><ul>`;
            for (const [distance, prediction] of Object.entries(data.predictions)) {
                html += `<li><strong>${distance}:</strong> ${prediction.formatted} (${prediction.seconds}s)</li>`;
            }
            html += '</ul>';
            predictionsDiv.innerHTML = html;
        }
    })
    .catch(error => {
        console.error('Błąd predykcji dystansów:', error);
    });
}

// ✅ FUNKCJA: Predykcja dla konkretnego dystansu
function fetchSpecificPrediction(distanceKm, averageSpeedKmh) {
    fetch('/predict_specific', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            distance_km: distanceKm,
            average_speed_kmh: averageSpeedKmh
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log(`Predykcja ${distanceKm} km:`, data);
        
        const specificDiv = document.getElementById("specific_prediction_display");
        if (specificDiv) {
            specificDiv.innerHTML = `
                <h4>Predykcja dla ${distanceKm} km przy ${averageSpeedKmh} km/h:</h4>
                <p><strong>${data.predicted_time_formatted}</strong> (${data.predicted_time_seconds}s)</p>
            `;
        }
    })
    .catch(error => {
        console.error('Błąd predykcji specyficznej:', error);
    });
}

loadActivities();
document.getElementById("chart-select").addEventListener("change", loadActivities);
document.getElementById("sport-type-select").addEventListener("change", loadActivities);

// ✅ PRZYKŁAD: Dodaj przyciski do testowania
// fetchSpecificPrediction(5, 12); // 5 km przy 12 km/h
