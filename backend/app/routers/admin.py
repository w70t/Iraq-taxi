"""Admin panel and API: the owner sets commission %, booking fee and tariffs
at runtime. Protected by the X-Admin-Token header (ADMIN_TOKEN env)."""
import hmac

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..settings_store import SettingsError, get_settings, update_settings

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_token: str = Header(default="")) -> None:
    if not config.ADMIN_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access is disabled: set ADMIN_TOKEN")
    if not hmac.compare_digest(x_admin_token, config.ADMIN_TOKEN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Wrong admin token")


@router.get("/settings")
def read_settings(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    return get_settings(db)


@router.put("/settings")
def write_settings(
    patch: dict = Body(...),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return update_settings(db, patch)
    except SettingsError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def panel():
    return HTMLResponse(PANEL_HTML)


PANEL_HTML = """<!doctype html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>لوحة تحكم تكسي واحد عراق</title>
<style>
  body{font-family:system-ui,'Segoe UI',Tahoma,sans-serif;background:#0a1729;color:#fff;margin:0;padding:20px;max-width:560px;margin-inline:auto}
  h1{font-size:1.3rem;color:#ffa22b}
  .card{background:rgba(255,255,255,.08);border-radius:16px;padding:16px;margin-bottom:14px}
  label{display:block;font-size:.85rem;color:rgba(255,255,255,.7);margin-bottom:4px}
  input{width:100%;box-sizing:border-box;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:10px;color:#fff;padding:10px;font-size:1rem;margin-bottom:10px}
  button{width:100%;background:#ffa22b;color:#221400;border:0;border-radius:12px;padding:13px;font-size:1rem;font-weight:700;cursor:pointer}
  .row{display:flex;gap:8px}.row>div{flex:1}
  .msg{padding:10px;border-radius:10px;margin:10px 0;display:none}
  .ok{background:rgba(52,208,119,.2);color:#34d077}
  .err{background:rgba(255,107,107,.2);color:#ff6b6b}
  h3{font-size:1rem;margin:8px 0;color:#34d077}
</style>
</head>
<body>
<h1>لوحة تحكم تكسي واحد عراق — الرسوم والتسعير</h1>

<div class="card">
  <label>رمز الإدارة (ADMIN_TOKEN)</label>
  <input id="token" type="password" placeholder="الصق الرمز هنا">
  <button onclick="load()">دخول وتحميل الإعدادات</button>
</div>

<div id="form" style="display:none">
  <div class="card">
    <h3>رسوم المنصة</h3>
    <label>نسبة العمولة من كل رحلة (%)</label>
    <input id="commission_percent" type="number" step="0.5" min="0" max="50">
    <label>رسوم الحجز الثابتة (د.ع تُضاف لكل رحلة وتعود للمنصة)</label>
    <input id="booking_fee" type="number" step="250" min="0" max="10000">
  </div>

  <div class="card" id="tariffs"></div>

  <button onclick="save()">💾 حفظ التغييرات — تسري فوراً</button>
</div>

<div id="msg" class="msg"></div>

<script>
const TIERS = {economy:'اقتصادي', family:'عائلي', premium:'بريميوم'};
let settings = null;

function show(text, ok){
  const el = document.getElementById('msg');
  el.textContent = text; el.className = 'msg ' + (ok ? 'ok' : 'err');
  el.style.display = 'block';
}

async function api(method, body){
  const res = await fetch('/admin/settings', {
    method,
    headers: {'X-Admin-Token': document.getElementById('token').value,
              'Content-Type': 'application/json'},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if(!res.ok) throw new Error(data.detail || res.status);
  return data;
}

async function load(){
  try{
    settings = await api('GET');
    document.getElementById('commission_percent').value = settings.commission_percent;
    document.getElementById('booking_fee').value = settings.booking_fee;
    const box = document.getElementById('tariffs');
    box.innerHTML = '<h3>تعرفة الفئات (د.ع)</h3>';
    for(const [tier, name] of Object.entries(TIERS)){
      const t = settings.tariffs[tier];
      box.innerHTML += `<label>${name}: أساس / لكل كم / حد أدنى</label>
        <div class="row">
          <div><input id="${tier}_base" type="number" value="${t.base}"></div>
          <div><input id="${tier}_per_km" type="number" value="${t.per_km}"></div>
          <div><input id="${tier}_minimum" type="number" value="${t.minimum}"></div>
        </div>`;
    }
    document.getElementById('form').style.display = 'block';
    show('تم تحميل الإعدادات الحالية ✅', true);
  }catch(e){ show('فشل الدخول: ' + e.message, false); }
}

async function save(){
  try{
    const tariffs = {};
    for(const tier of Object.keys(TIERS)){
      tariffs[tier] = {
        base: +document.getElementById(tier+'_base').value,
        per_km: +document.getElementById(tier+'_per_km').value,
        minimum: +document.getElementById(tier+'_minimum').value,
      };
    }
    settings = await api('PUT', {
      commission_percent: +document.getElementById('commission_percent').value,
      booking_fee: +document.getElementById('booking_fee').value,
      tariffs,
    });
    show('تم الحفظ — الأسعار والعمولة الجديدة تسري على الرحلات القادمة فوراً ✅', true);
  }catch(e){ show('فشل الحفظ: ' + e.message, false); }
}
</script>
</body>
</html>"""
