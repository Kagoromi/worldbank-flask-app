import base64
import io
import math
import os
from collections import defaultdict

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for
from matplotlib.figure import Figure

import database as db
from services import fetch_world_bank_data

app = Flask(__name__)

db.init_db()

FIELDS = ("country_code", "country_name", "indicator_name", "value", "year")
TEXT_FIELDS = ("country_code", "country_name", "indicator_name")

# indicator -> (axis label, divisor applied to values on the chart)
INDICATOR_UNITS = {
    "GDP": ("Billions USD", 1e9),
    "Population": ("Millions", 1e6),
    "Inflation": ("% per year", 1.0),
}


class ValidationError(ValueError):
    """Raised when incoming data is missing or has the wrong type."""


def clean_fields(data, partial=False):
    """Validate and normalize indicator fields from a form or JSON body.

    With partial=True only the fields that are present are checked (PATCH).
    """
    cleaned = {}
    for field in FIELDS:
        if field not in data or data[field] is None:
            if partial:
                continue
            raise ValidationError(f"Missing field: {field}")

        raw = data[field]

        if field in TEXT_FIELDS:
            if not isinstance(raw, str) or not raw.strip():
                raise ValidationError(f"Invalid {field}")
            text = raw.strip()
            cleaned[field] = text.upper() if field == "country_code" else text

        elif field == "value":
            try:
                if isinstance(raw, bool):
                    raise ValueError
                number = float(raw)
            except (TypeError, ValueError):
                raise ValidationError("Invalid value: must be a number")
            if not math.isfinite(number):
                raise ValidationError("Invalid value: must be a finite number")
            cleaned[field] = number

        else:  # year
            try:
                if isinstance(raw, bool):
                    raise ValueError
                year = int(str(raw).strip())
            except ValueError:
                raise ValidationError("Invalid year: must be an integer")
            if not 1900 <= year <= 2100:
                raise ValidationError("Invalid year: must be between 1900 and 2100")
            cleaned[field] = year

    return cleaned


def generate_chart(records, selected_countries=None, target_indicator=None):
    if not records:
        return None

    if not target_indicator:
        target_indicator = records[0]["indicator_name"]

    filtered_records = [
        item
        for item in records
        if item["indicator_name"].lower() == target_indicator.lower()
    ]

    if selected_countries:
        filtered_records = [
            item for item in filtered_records if item["country_name"] in selected_countries
        ]

    if not filtered_records:
        return None

    indicator_name = filtered_records[0]["indicator_name"]
    unit_label, scale_factor = INDICATOR_UNITS.get(indicator_name, ("Value", 1.0))

    grouped_data = defaultdict(list)
    for item in filtered_records:
        grouped_data[item["country_name"]].append(item)

    # Figure() is used instead of pyplot: no global state, safe for Flask threads,
    # and nothing has to be closed manually.
    fig = Figure(figsize=(9, 4.5))
    ax = fig.subplots()

    for c_name, c_records in grouped_data.items():
        sorted_c = sorted(c_records, key=lambda x: x["year"])
        years = [x["year"] for x in sorted_c]
        values = [x["value"] / scale_factor for x in sorted_c]

        if len(years) == 1:
            ax.scatter(years, values, label=c_name, s=80, zorder=3)
        else:
            ax.plot(years, values, marker="o", linewidth=2, label=c_name)

    ax.set_title(f"Comparison - {indicator_name}")
    ax.set_xlabel("Year")
    ax.set_ylabel(unit_label)
    ax.legend(loc="best")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.ticklabel_format(style="plain", axis="y")
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@app.route("/")
def index():
    country = request.args.get("country", "").strip()
    indicator = request.args.get("indicator", "GDP")

    results = []
    error = None

    if country:
        results, error = fetch_world_bank_data(country, indicator)

    return render_template(
        "index.html",
        results=results,
        error=error,
        country=country,
        indicator=indicator,
    )


@app.route("/save", methods=["POST"])
def save_record():
    try:
        fields = clean_fields(request.form)
    except ValidationError as exc:
        abort(400, str(exc))

    try:
        db.add_indicator(**fields)
    except db.DuplicateRecordError:
        pass  # already saved, nothing to do

    return redirect(
        url_for(
            "index",
            country=fields["country_code"],
            indicator=fields["indicator_name"],
        )
    )


@app.route("/saved")
def saved_list():
    search = request.args.get("search", "").strip()
    chart_indicator = request.args.get("chart_indicator", "").strip()
    selected_countries = request.args.getlist("chart_countries")

    records = db.get_all_indicators(search_query=search if search else None)

    unique_countries = sorted({r["country_name"] for r in records})
    unique_indicators = sorted({r["indicator_name"] for r in records})

    chart = None
    if records:
        chart = generate_chart(
            records,
            selected_countries=selected_countries if selected_countries else None,
            target_indicator=chart_indicator if chart_indicator else None,
        )

    return render_template(
        "saved.html",
        records=records,
        search=search,
        chart=chart,
        unique_countries=unique_countries,
        unique_indicators=unique_indicators,
        selected_countries=selected_countries,
        selected_indicator=chart_indicator,
    )


@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    item = db.get_indicator_by_id(item_id)
    if not item:
        return redirect(url_for("saved_list"))

    if request.method == "POST":
        try:
            fields = clean_fields(request.form)
        except ValidationError as exc:
            abort(400, str(exc))

        try:
            db.update_indicator(item_id, **fields)
        except db.DuplicateRecordError:
            abort(409, "A record for this country, indicator and year already exists")

        return redirect(url_for("saved_list"))

    return render_template("edit.html", item=item)


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    db.delete_indicator(item_id)
    return redirect(url_for("saved_list"))


# REST API Endpoints


@app.route("/api/indicators", methods=["GET"])
def api_get_all():
    return jsonify(db.get_all_indicators()), 200


@app.route("/api/indicators/<int:item_id>", methods=["GET"])
def api_get_one(item_id):
    item = db.get_indicator_by_id(item_id)
    if item:
        return jsonify(item), 200
    return jsonify({"error": "Record not found"}), 404


@app.route("/api/indicators", methods=["POST"])
def api_create():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    try:
        fields = clean_fields(data)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        new_id = db.add_indicator(**fields)
    except db.DuplicateRecordError:
        return jsonify({"error": "Record already exists"}), 409

    return jsonify(db.get_indicator_by_id(new_id)), 201


@app.route("/api/indicators/<int:item_id>", methods=["PATCH"])
def api_update(item_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "Invalid input data"}), 400

    try:
        fields = clean_fields(data, partial=True)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400

    try:
        success = db.update_indicator(item_id, **fields)
    except db.DuplicateRecordError:
        return jsonify({"error": "Record already exists"}), 409

    if success:
        return jsonify(db.get_indicator_by_id(item_id)), 200
    return jsonify({"error": "Record not found"}), 404


@app.route("/api/indicators/<int:item_id>", methods=["DELETE"])
def api_delete(item_id):
    if db.delete_indicator(item_id):
        return jsonify({"message": "Record deleted successfully"}), 200
    return jsonify({"error": "Record not found"}), 404


if __name__ == "__main__":
    # Debug mode only when explicitly enabled: FLASK_DEBUG=1 python app.py
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")