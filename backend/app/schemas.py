from pydantic import BaseModel, Field


class OtpRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20, pattern=r"^\+?\d+$")
    role: str = Field(pattern="^(rider|driver)$")


class OtpVerify(OtpRequest):
    code: str = Field(min_length=4, max_length=8)
    name: str = ""


class TripCreate(BaseModel):
    pickup_lat: float = Field(ge=-90, le=90)
    pickup_lng: float = Field(ge=-180, le=180)
    pickup_label: str = ""
    dest_lat: float | None = Field(default=None, ge=-90, le=90)
    dest_lng: float | None = Field(default=None, ge=-180, le=180)
    dest_label: str = ""
    tier: str = Field(default="economy", pattern="^(economy|family|premium)$")


class LocationUpdate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class OnlineUpdate(BaseModel):
    online: bool
    car_model: str = ""
    plate: str = ""
    car_color: str = ""


class PaymentInit(BaseModel):
    trip_id: str
    method: str = Field(pattern="^(cash|zaincash|fib|qi)$")
