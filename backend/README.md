# خادم تكسي واحد عراق | Taxi One Iraq Backend

خادم FastAPI حقيقي لتطبيقي الزبون والسائق: حسابات OTP، مطابقة الرحلات، تتبع حي، ودفع إلكتروني (زين كاش + FIB + نقدي).

## التشغيل محلياً

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # ثم عدّل القيم
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

التوثيق التفاعلي الكامل بعد التشغيل: `http://localhost:8000/docs`

بـ Docker:

```bash
docker compose up --build
```

## النشر للإنتاج (Raspberry Pi أو أي خادم)

الدليل الكامل في [`DEPLOY.md`](DEPLOY.md) — حزمة `docker-compose.prod.yml` تشغّل
PostgreSQL + Redis + الخادم + Caddy (HTTPS تلقائي) على أي جهاز arm64 أو amd64:

```bash
cp .env.example .env   # عبّئ SECRET_KEY, ADMIN_TOKEN, POSTGRES_PASSWORD, DOMAIN
docker compose -f docker-compose.prod.yml up -d --build
```

## ترحيلات قاعدة البيانات (Alembic)

- SQLite (تطوير/اختبارات): الجداول تُنشأ تلقائياً عند الإقلاع — لا شيء عليك.
- PostgreSQL (إنتاج): `alembic upgrade head` — يعمل تلقائياً في حزمة الإنتاج.
- عند تعديل `app/models.py`: `alembic revision --autogenerate -m "وصف"` ثم راجع
  الملف المولَّد في `alembic/versions/`.

## الاختبارات

```bash
.venv/bin/python -m pytest tests/ -q
```

## واجهة الـ API

| المسار | الوصف |
|---|---|
| `POST /auth/otp/request` | إرسال رمز تحقق (rider أو driver) |
| `POST /auth/otp/verify` | التحقق واستلام JWT |
| `POST /trips` | الزبون يطلب رحلة (تقدير سعر تلقائي) |
| `GET /trips/current` | الرحلة النشطة (تشمل موقع السائق الحي) |
| `POST /trips/{id}/accept·arrived·start·complete·cancel` | دورة حياة الرحلة |
| `POST /drivers/status` | السائق متصل/غير متصل |
| `POST /drivers/location` | تحديث موقع السائق (يُدفع للزبون مباشرة) |
| `GET /drivers/trips/open` | الطلبات المفتوحة ضمن 15 كم (الأقرب أولاً) |
| `GET /drivers/earnings` | أرباح السائق |
| `GET /payments/methods` | طرق الدفع المفعّلة |
| `POST /payments/init` | بدء دفعة (زين كاش → رابط دفع، FIB → رمز QR) |
| `WS /ws?token=` | تحديثات الرحلة الحية |

## تفعيل الدفع الحقيقي

الكود جاهز والتفعيل يحتاج فقط وضع مفاتيح التاجر في `.env`:

1. **زين كاش**: وقّع عقد تاجر مع زين العراق ← تستلم `MSISDN` + `MERCHANT_ID` + `SECRET`. جرّب أولاً على بيئة `test.zaincash.iq`.
2. **FIB**: سجّل كتاجر لدى المصرف العراقي الأول ← تستلم `CLIENT_ID` + `CLIENT_SECRET`. بيئة التجربة `fib.stage.fib.iq`.
3. **سوبر كي (Qi)**: يتطلب اتفاقية مع شركة كي كارد — الهيكل جاهز في `app/payments/qi.py`.
4. **باي بال**: غير متاح للتجار في العراق — البطاقات الدولية تمر عبر بوابة مرخصة محلياً.

بدون مفاتيح، تظهر هذه الطرق «غير مفعّلة» في التطبيق ويبقى الدفع النقدي يعمل.

## أمان الإنتاج (إلزامي قبل الإطلاق)

- `SECRET_KEY` عشوائي 32+ بايت، و`OTP_ECHO=false`، و`DRIVER_AUTO_APPROVE=false`.
- شغّل خلف HTTPS فقط (Caddy أو Nginx + Let's Encrypt).
- اربط مزود SMS عراقي في `app/sms.py` (مجمّعات آسياسيل/زين/كورك).
- بدّل SQLite بـ PostgreSQL في `DATABASE_URL`.
