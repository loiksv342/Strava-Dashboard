# Personal Sports Performance Dashboard (Strava Sync)

A personal web application that connects to Strava, analyzes your training data, and visualizes performance metrics in an interactive dashboard. The app synchronizes activities, identifies personal bests on standard distances (1 km, 1 mile, 5 km, Half Marathon, Marathon for running; 1 km, 5 km, 10 km, 20 km, 50 km, 100 km for cycling), and tracks progress over time with predictive analytics.

This project is designed for individual athletes who want to monitor their performance trends, and for portfolio presentation to showcase full-stack data engineering and analytics skills.

## Features
- Synchronization with Strava API (OAuth2 Authorization)
- Automatic download of detailed activity streams (GPS, speed, heart rate)
- Personal Best detection via moving window analysis
- Rolling averages and performance trend visualization
- Predictive models estimating future race times (5K, 10K, Half Marathon, Marathon)
- Interactive dashboard with dynamic filtering (date ranges, activity type)
- Export reports to CSV (optional PDF export)
- Responsive UI using Bootstrap and Chart.js

## Tech Stack
- Backend: Python (Flask), PostgreSQL, SQLAlchemy, Pandas, Scikit-learn
- Frontend: HTML5, CSS3 (Bootstrap 5), JavaScript (Chart.js, AJAX)
- API Integration: Strava API (OAuth2, Activity Streams)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/strava-dashboard.git
   cd strava-dashboard
