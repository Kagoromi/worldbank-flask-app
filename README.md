# World Bank Data Explorer & Analytics API

A robust Flask-based web application that integrates with the public World Bank REST API to fetch, analyze, and visualize global economic metrics. The application provides interactive web interfaces for data exploration, persists historical records in a local SQLite database, generates time-series visual charts using Matplotlib, and exposes a full RESTful JSON API for external clients.

## Key Features

- External Data Integration: Interacts with the World Bank REST API to query key financial and social indicators such as GDP, Population, and Inflation.
- Relational Data Storage: Persists user-selected indicators into a SQLite database using parameterized SQL queries to guarantee security against SQL injection.
- Data Filtering & Analytics: Enables fast in-database searching across stored metrics and dynamic rendering of historical trend charts using Matplotlib.
- RESTful API: Exposes structured JSON endpoints supporting full CRUD operations on stored indicator records.
- User-Friendly Interface: Features a responsive Bootstrap 5 interface enhanced with custom CSS styling, intuitive data table visualization, and action triggers.

## Tech Stack

- Backend: Python 3, Flask
- Database: SQLite3
- Visualization: Matplotlib
- HTTP Client: Requests
- Frontend: HTML5, CSS3, Jinja2, Bootstrap 5

## Project Structure

```
├── static/
│   └── style.css          # Custom styles extending Bootstrap 5
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Base layout template with Bootstrap setup & navigation
│   ├── index.html         # Search interface for external World Bank API data
│   ├── saved.html         # View, search filter, and chart visualization for saved records
│   └── edit.html          # Form interface for updating existing database records
├── app.py                 # Main Flask application & REST API routes
├── database.py            # SQLite helper module & parameterized SQL queries
├── services.py            # External World Bank API integration & data parsing service
├── requirements.txt       # Project dependencies
└── README.md
```

## Database Schema

The application uses a relational SQLite database (`worldbank.db`) with a main table named `indicators` to store economic metrics:

- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT) – Unique record identifier.
- `country_code` (TEXT, NOT NULL) – ISO 3-letter country code (e.g., UKR, USA).
- `country_name` (TEXT, NOT NULL) – Full name of the country.
- `indicator_name` (TEXT, NOT NULL) – Economic indicator name (GDP, Population, Inflation).
- `value` (REAL, NOT NULL) – Numeric value of the indicator.
- `year` (INTEGER, NOT NULL) – Year of observation.

## API Documentation

The application provides a standalone RESTful JSON API accessible under the `/api/indicators` route handler.

- `GET /api/indicators` – Retrieve all saved indicator records (Status 200 OK)
- `GET /api/indicators/<id>` – Fetch a specific record by primary key (Status 200 OK or 404 Not Found)
- `POST /api/indicators` – Create a new economic indicator entry (Status 201 Created or 400 Bad Request)
- `PATCH /api/indicators/<id>` – Update fields of an existing record (Status 200 OK, 400 Bad Request or 404 Not Found)
- `DELETE /api/indicators/<id>` – Remove a record from the database (Status 200 OK or 404 Not Found)

## Installation & Local Setup

1. Clone the repository using `git clone https://github.com/Kagoromi/worldbank-flask-app.git` and navigate to the project directory.
2. Create and activate a Python virtual environment.
3. Install required dependencies using `pip install -r requirements.txt`.
4. Run the application using `python app.py`.
5. Open `http://127.0.0.1:5000` in your web browser.
