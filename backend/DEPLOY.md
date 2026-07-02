# نشر الخادم — من Raspberry Pi 5 إلى السحابة 🚀

الفكرة المعمارية: **كل شيء داخل حاويات، وكل الحالة في وحدات تخزين PostgreSQL/Redis،
وكل ما يخص البيئة في `.env`**. النتيجة: نفس الملفات تشغّل الخادم على
Raspberry Pi 5 اليوم وعلى أي خادم سحابي غداً — الانتقال مجرد نسخ احتياطي واستعادة،
بلا أي تغيير في الكود.

## 1) تجهيز Raspberry Pi 5 (8GB)

1. **نظام التشغيل**: Raspberry Pi OS Lite **64-bit** (أو Ubuntu Server 24.04 arm64).
2. **التخزين — مهم جداً**: استخدم **SSD عبر USB 3** وليس بطاقة SD.
   بطاقات SD تتلف بسرعة تحت كتابات قاعدة البيانات المستمرة، وسرعتها ضعيفة.
   (اجعل النظام كاملاً يقلع من الـ SSD عبر `rpi-eeprom` boot order.)
3. **دوكر**:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER   # ثم أعد تسجيل الدخول
   ```

## 2) الإعداد

```bash
git clone https://github.com/w70t/Iraq-taxi.git
cd Iraq-taxi/backend
cp .env.example .env
nano .env
```

القيم الإلزامية في `.env` للإنتاج:

| المتغير | القيمة |
|---|---|
| `SECRET_KEY` | `python3 -c "import secrets;print(secrets.token_hex(32))"` |
| `ADMIN_TOKEN` | `python3 -c "import secrets;print(secrets.token_urlsafe(24))"` |
| `POSTGRES_PASSWORD` | `python3 -c "import secrets;print(secrets.token_urlsafe(24))"` |
| `DOMAIN` | نطاقك، مثل `api.taxi-one.iq` |
| `OTP_ECHO` | `false` |
| `DRIVER_AUTO_APPROVE` | `false` |

> لا تعدّل `DATABASE_URL` ولا `REDIS_URL` — ملف `docker-compose.prod.yml`
> يضبطهما تلقائياً على PostgreSQL وRedis داخل الشبكة الداخلية.

## 3) الوصول من الإنترنت — طريقان

### أ) منفذ مباشر (إن كان لديك IP عام)
وجّه سجل `A` في DNS نطاقك إلى IP منزلك، وافتح المنفذين 80 و443 في الراوتر
نحو الـ Pi. Caddy سيصدر شهادة HTTPS تلقائياً عند أول تشغيل.

### ب) Cloudflare Tunnel (الأنسب في العراق — يعمل خلف CGNAT)
أغلب مزودي الإنترنت العراقيين لا يمنحون IP عاماً حقيقياً (CGNAT)، والحل:

```bash
# على الـ Pi
docker run -d --restart unless-stopped --network backend_default \
  cloudflare/cloudflared:latest tunnel --no-autoupdate run --token <TOKEN>
```

أنشئ النفق من لوحة Cloudflare Zero Trust ووجّهه إلى `http://api:8000`
(أو `http://caddy:80`). لا حاجة لفتح أي منفذ في الراوتر.

## 4) التشغيل

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

ما يحدث تلقائياً: بناء صورة الخادم ← انتظار جاهزية PostgreSQL ←
`alembic upgrade head` (إنشاء/ترقية الجداول) ← تشغيل عاملَي uvicorn ←
Caddy يصدر الشهادة ويبدأ الاستقبال.

**تحقق**: `curl https://نطاقك/health` → `{"ok": true}`،
ثم افتح `https://نطاقك/admin` بلوحة التحكم.

## 5) النسخ الاحتياطي — يومي وإلزامي

```bash
# أضف إلى crontab -e (نسخة كل ليلة 3:17 فجراً، الاحتفاظ بآخر 14)
17 3 * * * cd ~/Iraq-taxi/backend && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U taxi taxi | gzip > ~/backups/taxi-$(date +\%F).sql.gz && ls -t ~/backups/taxi-*.sql.gz | tail -n +15 | xargs -r rm
```

يُنصح بمزامنة `~/backups` خارج المنزل (مثلاً `rclone` إلى أي تخزين سحابي) —
النسخة التي تسكن بجانب الخادم ليست نسخة احتياطية حقيقية.

## 6) التحديث عند صدور كود جديد

```bash
cd ~/Iraq-taxi && git pull
cd backend && docker compose -f docker-compose.prod.yml up -d --build
```

الترحيلات (migrations) تُطبَّق تلقائياً عند الإقلاع. للرجوع عن إصدار:
`git checkout <tag>` ثم نفس أمر التشغيل.

## 7) الانتقال إلى خادم سحابي لاحقاً — 4 خطوات، صفر تغيير كود

1. **على الخادم الجديد** (أي VPS بـ Docker): نفس خطوات القسم 2 (استنساخ + نسخ `.env` نفسه).
2. **آخر نسخة من قاعدة البيانات**:
   ```bash
   # على الـ Pi
   docker compose -f docker-compose.prod.yml exec -T db pg_dump -U taxi taxi | gzip > final.sql.gz
   # على الخادم الجديد بعد `up -d` أولي
   gunzip -c final.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U taxi taxi
   ```
3. **DNS**: وجّه `DOMAIN` إلى الخادم الجديد (أو انقل نفق Cloudflare).
4. أوقف الـ Pi. التطبيقات لا تتأثر — عنوان الخادم فيها هو النطاق، لا الجهاز.

> Redis يخزّن أحداثاً لحظية فقط (لا بيانات دائمة) — لا يحتاج نقلاً.

## 8) حدود الـ Pi ومتى تنتقل

Pi 5 بـ 8GB يخدم مئات الرحلات اليومية براحة (الخادم I/O-خفيف: JSON صغير
وWebSocket). انتقل للسحابة عندما ترى أياً من:
- استهلاك ذاكرة ثابت فوق ~6GB أو swap مستمر،
- زمن استجابة `/health` فوق 200ms من داخل الشبكة،
- انقطاعات كهرباء/إنترنت تؤثر على السائقين (الأهم في العراق — UPS يؤجل
  المشكلة لكن لا يحلها).
