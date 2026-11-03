from services import fetch_world_bank_data

SAMPLE = {
    "country_code": "UKR",
    "country_name": "Ukraine",
    "indicator_name": "GDP",
    "value": 100.5,
    "year": 2020,
}


def create(client, **overrides):
    return client.post("/api/indicators", json={**SAMPLE, **overrides})


def test_create_and_get(client):
    response = create(client)
    assert response.status_code == 201
    item_id = response.get_json()["id"]

    fetched = client.get(f"/api/indicators/{item_id}")
    assert fetched.status_code == 200
    assert fetched.get_json()["country_name"] == "Ukraine"


def test_get_all(client):
    create(client)
    create(client, year=2021)
    response = client.get("/api/indicators")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_missing_fields(client):
    response = client.post("/api/indicators", json={"country_code": "UKR"})
    assert response.status_code == 400


def test_invalid_value_returns_400(client):
    assert create(client, value="abc").status_code == 400


def test_invalid_year_returns_400(client):
    assert create(client, year="twenty").status_code == 400


def test_duplicate_returns_409(client):
    assert create(client).status_code == 201
    assert create(client).status_code == 409


def test_not_found(client):
    assert client.get("/api/indicators/999").status_code == 404
    assert client.patch("/api/indicators/999", json={"value": 1}).status_code == 404
    assert client.delete("/api/indicators/999").status_code == 404


def test_patch_updates_value(client):
    item_id = create(client).get_json()["id"]
    response = client.patch(f"/api/indicators/{item_id}", json={"value": 0})
    assert response.status_code == 200
    assert response.get_json()["value"] == 0


def test_patch_invalid_value_returns_400(client):
    item_id = create(client).get_json()["id"]
    response = client.patch(f"/api/indicators/{item_id}", json={"value": "abc"})
    assert response.status_code == 400


def test_patch_cannot_create_duplicate(client):
    create(client, year=2020)
    second_id = create(client, year=2021).get_json()["id"]
    response = client.patch(f"/api/indicators/{second_id}", json={"year": 2020})
    assert response.status_code == 409


def test_delete(client):
    item_id = create(client).get_json()["id"]
    assert client.delete(f"/api/indicators/{item_id}").status_code == 200
    assert client.get(f"/api/indicators/{item_id}").status_code == 404


def test_form_save_with_invalid_value_returns_400(client):
    response = client.post("/save", data={**SAMPLE, "value": "abc"})
    assert response.status_code == 400


def test_saved_page_with_chart(client):
    create(client)
    create(client, year=2021, value=120.0)
    response = client.get("/saved")
    assert response.status_code == 200


def test_invalid_country_code_rejected_without_network():
    results, error = fetch_world_bank_data("../etc", "GDP")
    assert results == []
    assert "Invalid country code" in error