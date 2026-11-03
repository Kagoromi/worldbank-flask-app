import base64
import io
from flask import Flask, jsonify, redirect, render_template, request, url_for
import matplotlib

matplotlib.use("Agg")
import database as db
import matplotlib.pyplot as plt
from services import fetch_world_bank_data

app = Flask(__name__)

db.init_db()


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
            item
            for item in filtered_records
            if item["country_name"] in selected_countries
        ]

    if not filtered_records:
        return None

    grouped_data = {}
    for item in filtered_records:
        c_name = item["country_name"]
        if c_name not in grouped_data:
            grouped_data[c_name] = []
        grouped_data[c_name].append(item)

    plt.figure(figsize=(9, 4.5))

    scale_factor = 1.0
    unit_label = "Value"
    if target_indicator in ["GDP", "Population"]:
        scale_factor = 1e9
        unit_label = "Billions" if target_indicator == "GDP" else "Millions / Billions"

    for c_name, c_records in grouped_data.items():
        sorted_c = sorted(c_records, key=lambda x: x["year"])
        years = [x["year"] for x in sorted_c]
        values = [x["value"] / scale_factor for x in sorted_c]

        if len(years) == 1:
            plt.scatter(years, values, label=c_name, s=80, zorder=3)
        else:
            plt.plot(years, values, marker="o", linewidth=2, label=c_name)

    plt.title(f"Comparison - {target_indicator}")
    plt.xlabel("Year")
    plt.ylabel(unit_label)
    plt.legend(loc="best")
    plt.grid(True, linestyle="--", alpha=0.6)

    ax = plt.gca()
    ax.ticklabel_format(style="plain", axis="y")

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    chart_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    plt.close()
    return chart_base64


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
    c_code = request.form.get("country_code")
    c_name = request.form.get("country_name")
    i_name = request.form.get("indicator_name")
    val = float(request.form.get("value"))
    yr = int(request.form.get("year"))

    db.add_indicator(c_code, c_name, i_name, val, yr)
    return redirect(url_for("index", country=c_code, indicator=i_name))


@app.route("/saved")
def saved_list():
    search = request.args.get("search", "").strip()
    chart_indicator = request.args.get("chart_indicator", "").strip()
    selected_countries = request.args.getlist("chart_countries")

    records = db.get_all_indicators(search_query=search if search else None)

    unique_countries = (
        sorted(list({r["country_name"] for r in records})) if records else []
    )
    unique_indicators = (
        sorted(list({r["indicator_name"] for r in records})) if records else []
    )

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
        c_code = request.form.get("country_code")
        c_name = request.form.get("country_name")
        i_name = request.form.get("indicator_name")
        val = float(request.form.get("value"))
        yr = int(request.form.get("year"))

        db.update_indicator(
            item_id,
            country_code=c_code,
            country_name=c_name,
            indicator_name=i_name,
            value=val,
            year=yr,
        )
        return redirect(url_for("saved_list"))

    return render_template("edit.html", item=item)


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    db.delete_indicator(item_id)
    return redirect(url_for("saved_list"))


# REST API Endpoints


@app.route("/api/indicators", methods=["GET"])
def api_get_all():
    records = db.get_all_indicators()
    return jsonify(records), 200


@app.route("/api/indicators/<int:item_id>", methods=["GET"])
def api_get_one(item_id):
    item = db.get_indicator_by_id(item_id)
    if item:
        return jsonify(item), 200
    return jsonify({"error": "Record not found"}), 404


@app.route("/api/indicators", methods=["POST"])
def api_create():
    data = request.get_json()
    if not data or not all(
        k in data
        for k in ("country_code", "country_name", "indicator_name", "value", "year")
    ):
        return jsonify({"error": "Missing required fields"}), 400

    new_id = db.add_indicator(
        data["country_code"],
        data["country_name"],
        data["indicator_name"],
        float(data["value"]),
        int(data["year"]),
    )

    if new_id is None:
        return jsonify({"error": "Record already exists"}), 400

    created_item = db.get_indicator_by_id(new_id)
    return jsonify(created_item), 201


@app.route("/api/indicators/<int:item_id>", methods=["PATCH"])
def api_update(item_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input data"}), 400

    success = db.update_indicator(
        item_id,
        country_code=data.get("country_code"),
        country_name=data.get("country_name"),
        indicator_name=data.get("indicator_name"),
        value=data.get("value"),
        year=data.get("year"),
    )
    if success:
        updated_item = db.get_indicator_by_id(item_id)
        return jsonify(updated_item), 200
    return jsonify({"error": "Record not found"}), 404


@app.route("/api/indicators/<int:item_id>", methods=["DELETE"])
def api_delete(item_id):
    success = db.delete_indicator(item_id)
    if success:
        return jsonify({"message": "Record deleted successfully"}), 200
    return jsonify({"error": "Record not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)