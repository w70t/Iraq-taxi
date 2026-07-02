"""End-to-end flow: OTP login for rider and driver, trip lifecycle, payments."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///./test_taxi.db"
os.environ["SECRET_KEY"] = "test-secret"

import pathlib

import pytest
from fastapi.testclient import TestClient

pathlib.Path("test_taxi.db").unlink(missing_ok=True)

from app.main import app  # noqa: E402
from app.sms import get_sender  # noqa: E402

client = TestClient(app)


def login(phone: str, role: str, name: str = "") -> dict:
    response = client.post("/auth/otp/request", json={"phone": phone, "role": role})
    assert response.status_code == 200, response.text
    code = get_sender().last_codes[phone]
    response = client.post(
        "/auth/otp/verify",
        json={"phone": phone, "role": role, "code": code, "name": name},
    )
    assert response.status_code == 200, response.text
    return response.json()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def rider():
    return login("+9647701112222", "rider", "Rider One")


@pytest.fixture(scope="module")
def driver():
    return login("+9647703334444", "driver", "Driver One")


def test_wrong_otp_rejected():
    client.post("/auth/otp/request", json={"phone": "+9647700000000", "role": "rider"})
    response = client.post(
        "/auth/otp/verify",
        json={"phone": "+9647700000000", "role": "rider", "code": "000000"},
    )
    assert response.status_code in (400, 429)


def test_full_trip_lifecycle(rider, driver):
    rider_headers = auth(rider["access_token"])
    driver_headers = auth(driver["access_token"])

    # Driver goes online with a car
    response = client.post(
        "/drivers/status",
        json={"online": True, "car_model": "Toyota Corolla", "plate": "27 A 1234"},
        headers=driver_headers,
    )
    assert response.status_code == 200 and response.json()["online"] is True

    response = client.post(
        "/drivers/location", json={"lat": 33.312, "lng": 44.361}, headers=driver_headers
    )
    assert response.status_code == 200

    # Rider requests a trip in Baghdad
    response = client.post(
        "/trips",
        json={
            "pickup_lat": 33.315,
            "pickup_lng": 44.366,
            "pickup_label": "الكرادة",
            "dest_lat": 33.340,
            "dest_lng": 44.400,
            "dest_label": "الأعظمية",
            "tier": "economy",
        },
        headers=rider_headers,
    )
    assert response.status_code == 201, response.text
    trip = response.json()
    assert trip["fare_estimate"] >= 5000

    # A second request while one is active must be rejected
    response = client.post(
        "/trips",
        json={"pickup_lat": 33.3, "pickup_lng": 44.3},
        headers=rider_headers,
    )
    assert response.status_code == 409

    # Driver sees the open trip nearby and accepts it
    response = client.get("/drivers/trips/open", headers=driver_headers)
    assert response.status_code == 200
    open_trips = response.json()
    assert any(t["id"] == trip["id"] for t in open_trips)

    response = client.post(f"/trips/{trip['id']}/accept", headers=driver_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["driver"]["car_model"] == "Toyota Corolla"

    # Second accept attempt fails (already claimed)
    response = client.post(f"/trips/{trip['id']}/accept", headers=driver_headers)
    assert response.status_code == 409

    # Lifecycle: arrived -> in_progress -> completed
    for action, expected in [("arrived", "arrived"), ("start", "in_progress"), ("complete", "completed")]:
        response = client.post(f"/trips/{trip['id']}/{action}", headers=driver_headers)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == expected

    # Cash trips are settled on completion
    assert response.json()["paid"] is True

    # History and earnings reflect the completed trip
    response = client.get("/trips/history", headers=rider_headers)
    assert any(t["id"] == trip["id"] for t in response.json())

    response = client.get("/drivers/earnings", headers=driver_headers)
    body = response.json()
    assert body["count"] == 1 and body["total"] == trip["fare_estimate"]


def test_payment_methods_and_unconfigured_providers(rider):
    response = client.get("/payments/methods")
    assert response.status_code == 200
    methods = {m["id"]: m["enabled"] for m in response.json()}
    assert methods["cash"] is True
    assert methods["zaincash"] is False  # no merchant creds in test env
    assert methods["qi"] is False

    rider_headers = auth(rider["access_token"])
    response = client.post(
        "/trips",
        json={"pickup_lat": 33.3, "pickup_lng": 44.3, "tier": "premium"},
        headers=rider_headers,
    )
    assert response.status_code == 201
    trip = response.json()

    # Unconfigured provider returns a clear 503, not a crash
    response = client.post(
        "/payments/init",
        json={"trip_id": trip["id"], "method": "zaincash"},
        headers=rider_headers,
    )
    assert response.status_code == 503

    # Cash always works
    response = client.post(
        "/payments/init",
        json={"trip_id": trip["id"], "method": "cash"},
        headers=rider_headers,
    )
    assert response.status_code == 200

    client.post(f"/trips/{trip['id']}/cancel", headers=rider_headers)


def test_role_separation(rider):
    rider_headers = auth(rider["access_token"])
    response = client.post("/drivers/status", json={"online": True}, headers=rider_headers)
    assert response.status_code == 403
