"""End-to-end flow: OTP login for rider and driver, trip lifecycle, payments."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_taxi.db")  # CI overrides with PostgreSQL
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ADMIN_TOKEN"] = "admin-test-token"

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

    # Cash trips are settled on completion, with the default 10% commission
    completed = response.json()
    assert completed["paid"] is True
    expected_commission = round(trip["fare_estimate"] * 0.10)
    assert completed["commission"] == expected_commission

    # History and earnings reflect the completed trip (net of commission)
    response = client.get("/trips/history", headers=rider_headers)
    assert any(t["id"] == trip["id"] for t in response.json())

    response = client.get("/drivers/earnings", headers=driver_headers)
    body = response.json()
    assert body["count"] == 1
    assert body["gross"] == trip["fare_estimate"]
    assert body["commission"] == expected_commission
    assert body["total"] == trip["fare_estimate"] - expected_commission


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


def test_incentives(driver):
    response = client.get("/drivers/incentives", headers=auth(driver["access_token"]))
    assert response.status_code == 200
    body = response.json()
    assert body["trips_today"] >= 1  # the lifecycle test completed one trip today
    assert body["plans"] and body["plans"][0]["steps"]
    assert body["plans"][0]["seconds_remaining"] > 0


def test_admin_controls_fees(rider, driver):
    admin = {"X-Admin-Token": "admin-test-token"}

    # Wrong or missing token is rejected
    assert client.get("/admin/settings").status_code == 403
    assert client.get("/admin/settings", headers={"X-Admin-Token": "nope"}).status_code == 403

    # Owner raises commission to 20% and adds a 1,000 IQD booking fee
    settings = client.get("/admin/settings", headers=admin).json()
    response = client.put(
        "/admin/settings",
        json={"commission_percent": 20, "booking_fee": 1000, "tariffs": settings["tariffs"]},
        headers=admin,
    )
    assert response.status_code == 200
    assert response.json()["commission_percent"] == 20

    # Out-of-range values are rejected
    assert client.put("/admin/settings", json={"commission_percent": 90}, headers=admin).status_code == 400

    # New trip picks up the booking fee: economy minimum 5000 + 1000
    rider_headers = auth(rider["access_token"])
    driver_headers = auth(driver["access_token"])
    response = client.post(
        "/trips",
        json={"pickup_lat": 33.312, "pickup_lng": 44.361, "tier": "economy"},
        headers=rider_headers,
    )
    assert response.status_code == 201
    trip = response.json()
    assert trip["fare_estimate"] == 6000

    # Complete it and verify the platform cut: (6000-1000)*20% + 1000 = 2000
    client.post(f"/trips/{trip['id']}/accept", headers=driver_headers)
    client.post(f"/trips/{trip['id']}/arrived", headers=driver_headers)
    client.post(f"/trips/{trip['id']}/start", headers=driver_headers)
    response = client.post(f"/trips/{trip['id']}/complete", headers=driver_headers)
    assert response.status_code == 200
    assert response.json()["commission"] == 2000


def test_complaints_and_admin_resolution(driver):
    admin = {"X-Admin-Token": "admin-test-token"}
    driver_headers = auth(driver["access_token"])

    response = client.post(
        "/complaints", json={"text": "الزبون ألغى بعد وصولي"}, headers=driver_headers
    )
    assert response.status_code == 201
    complaint = response.json()
    assert complaint["status"] == "open"

    # Driver sees it in their own list
    response = client.get("/complaints/mine", headers=driver_headers)
    assert any(c["id"] == complaint["id"] for c in response.json())

    # Admin sees it and resolves it
    response = client.get("/admin/complaints", headers=admin)
    assert any(c["id"] == complaint["id"] for c in response.json())

    response = client.post(f"/admin/complaints/{complaint['id']}/resolve", headers=admin)
    assert response.status_code == 200 and response.json()["status"] == "resolved"


def test_admin_stats_and_driver_management(driver):
    admin = {"X-Admin-Token": "admin-test-token"}

    stats = client.get("/admin/stats", headers=admin).json()
    assert stats["trips_completed"] >= 2
    assert stats["revenue_total"] > 0
    assert "cash" in stats["payments_by_method"]

    drivers = client.get("/admin/drivers", headers=admin).json()
    assert drivers and drivers[0]["trips_completed"] >= 1
    driver_id = drivers[0]["id"]

    # Suspend then re-approve; suspension also forces the driver offline
    response = client.post(f"/admin/drivers/{driver_id}/approve", json={"approved": False}, headers=admin)
    assert response.json()["approved"] is False
    response = client.post(
        "/drivers/status", json={"online": True}, headers=auth(driver["access_token"])
    )
    assert response.status_code == 403  # suspended drivers cannot go online
    client.post(f"/admin/drivers/{driver_id}/approve", json={"approved": True}, headers=admin)


def test_admin_edits_incentive_plans(driver):
    admin = {"X-Admin-Token": "admin-test-token"}
    response = client.put(
        "/admin/settings",
        json={"incentive_plans": [{
            "title": "خطة الجمعة",
            "description": "مكافآت مضاعفة",
            "steps": [{"trips": 2, "bonus": 3000}, {"trips": 5, "bonus": 9000}],
        }]},
        headers=admin,
    )
    assert response.status_code == 200

    body = client.get("/drivers/incentives", headers=auth(driver["access_token"])).json()
    assert body["plans"][0]["title"] == "خطة الجمعة"
    assert body["plans"][0]["steps"][0] == {"trips": 2, "bonus": 3000}

    # Invalid plans rejected
    response = client.put(
        "/admin/settings",
        json={"incentive_plans": [{"title": "", "steps": []}]},
        headers=admin,
    )
    assert response.status_code == 400


def test_role_separation(rider):
    rider_headers = auth(rider["access_token"])
    response = client.post("/drivers/status", json={"online": True}, headers=rider_headers)
    assert response.status_code == 403
