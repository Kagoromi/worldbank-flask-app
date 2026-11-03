# World Bank Data Explorer & Analytics API

A robust Flask-based web application that integrates with the public World Bank REST API to fetch, analyze, and visualize global economic metrics. The application provides interactive web interfaces for data exploration, persists historical records in a local SQLite database, generates time-series visual charts using Matplotlib, and exposes a full RESTful JSON API for external clients.

## Key Features

- External Data Integration: Interacts with the World Bank REST API to query key financial and social indicators such as GDP, Population, and Inflation.
- Relational Data Storage: Persists user-selected indicators into a SQLite database using parameterized SQL queries to guarantee security against SQL injection.
- Data Integrity: Input validation on both web forms and the API, plus a unique database index that prevents duplicate records (same country, indicator and year).
- Data Filtering & Analytics: Enables fast in-database searching across stored metrics and dynamic rendering of historical trend charts using Matplotlib.
- RESTful API: Exposes structured JSON endpoints supporting full CRUD operations on stored indicator records.
- Automated Tests: A pytest suite covering the REST API, validation rules and duplicate handling.
- User-Friendly Interface: Features a responsive Bootstrap 5 interface enhanced with custom CSS styling, intuitive data table visualization, and action triggers.

## Tech Stack

- Backend: Python 3, Flask
- Database: SQLite3
- Visualization: Matplotlib
- HTTP Client: Requests
- Testing: pytest
- Frontend: HTML5, CSS3, Jinja2, Bootstrap 5

## Project Structure

```
.
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── edit.html
│   ├── index.html
│   └── saved.html
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── .gitignore
├── app.py
├── database.py
├── README.md
├── requirements.txt
└── services.py
```

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application: web routes, input validation and REST API endpoints |
| `database.py` | SQLite helper module with parameterized queries |
| `services.py` | World Bank API integration and response parsing |
| `templates/base.html` | Base layout with Bootstrap setup and navigation |
| `templates/index.html` | Search interface for World Bank API data |
| `templates/saved.html` | Saved records: search filter and chart visualization |
| `templates/edit.html` | Form for updating an existing record |
| `static/style.css` | Custom styles extending Bootstrap 5 |
| `tests/conftest.py` | Shared pytest fixtures (test client, temporary database) |
| `tests/test_api.py` | Tests for the REST API, validation and duplicate handling |
| `requirements.txt` | Project dependencies |

The SQLite database file `worldbank.db` is created automatically on the first run and is not stored in the repository.

## Database Schema

The application uses a relational SQLite database (`worldbank.db`) with a main table named `indicators` to store economic metrics:

- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT) – Unique record identifier.
- `country_code` (TEXT, NOT NULL) – ISO 3-letter country code (e.g., UKR, USA).
- `country_name` (TEXT, NOT NULL) – Full name of the country.
- `indicator_name` (TEXT, NOT NULL) – Economic indicator name (GDP, Population, Inflation).
- `value` (REAL, NOT NULL) – Numeric value of the indicator.
- `year` (INTEGER, NOT NULL) – Year of observation.

A unique index on (`country_code`, `indicator_name`, `year`) guarantees that the same data point cannot be stored twice.

## API Documentation

The application provides a standalone RESTful JSON API accessible under the `/api/indicators` route handler.

- `GET /api/indicators` – Retrieve all saved indicator records (Status 200 OK)
- `GET /api/indicators/<id>` – Fetch a specific record by primary key (Status 200 OK or 404 Not Found)
- `POST /api/indicators` – Create a new economic indicator entry (Status 201 Created, 400 Bad Request or 409 Conflict if the record already exists)
- `PATCH /api/indicators/<id>` – Update fields of an existing record (Status 200 OK, 400 Bad Request, 404 Not Found or 409 Conflict)
- `DELETE /api/indicators/<id>` – Remove a record from the database (Status 200 OK or 404 Not Found)

Example request:

```bash
curl -X POST http://127.0.0.1:5000/api/indicators \
  -H "Content-Type: application/json" \
  -d '{"country_code": "UKR", "country_name": "Ukraine", "indicator_name": "GDP", "value": 178.8e9, "year": 2022}'
```

Validation rules: `value` must be a finite number, `year` must be an integer between 1900 and 2100, and the text fields must not be empty.

## Installation & Local Setup

1. Clone the repository using `git clone https://github.com/Kagoromi/worldbank-flask-app.git` and navigate to the project directory.
2. Create and activate a Python virtual environment.
3. Install required dependencies using `pip install -r requirements.txt`.
4. Run the application using `python app.py`.
5. Open `http://127.0.0.1:5000` in your web browser.

To run in debug mode during development, set the environment variable `FLASK_DEBUG=1` before starting the app.

## Running Tests

From the project root, run:

```bash
pytest
```

Tests use a temporary database, so your local `worldbank.db` is never touched.
