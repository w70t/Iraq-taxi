"""Admin panel and API: the owner runs the platform from the browser —
fees, tariffs, incentives, revenue stats, payments, complaints and driver
approval. Protected by the X-Admin-Token header (ADMIN_TOKEN env)."""
import hmac

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..models import Complaint, DriverProfile, Payment, Trip, User, now
from ..routers.complaints import complaint_dict
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


@router.get("/stats")
def stats(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    """Owner dashboard: how much the platform earned, and platform health."""
    now_ts = now()
    midnight = now_ts - (now_ts % 86400)

    completed = db.query(Trip).filter(Trip.status == "completed")
    completed_today = completed.filter(Trip.created_at >= midnight)

    by_method: dict = {}
    for trip in completed.all():
        entry = by_method.setdefault(trip.payment_method, {"count": 0, "amount": 0})
        entry["count"] += 1
        entry["amount"] += trip.fare_estimate

    return {
        "revenue_total": sum(t.commission for t in completed.all()),
        "revenue_today": sum(t.commission for t in completed_today.all()),
        "gross_total": sum(t.fare_estimate for t in completed.all()),
        "trips_completed": completed.count(),
        "trips_today": completed_today.count(),
        "trips_active": db.query(Trip).filter(
            Trip.status.in_(["requested", "accepted", "arrived", "in_progress"])
        ).count(),
        "riders": db.query(User).filter(User.role == "rider").count(),
        "drivers": db.query(User).filter(User.role == "driver").count(),
        "drivers_online": db.query(DriverProfile).filter(DriverProfile.is_online.is_(True)).count(),
        "drivers_pending": db.query(DriverProfile).filter(DriverProfile.approved.is_(False)).count(),
        "complaints_open": db.query(Complaint).filter(Complaint.status == "open").count(),
        "payments_by_method": by_method,
    }


@router.get("/complaints")
def list_complaints(
    only_open: bool = True,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)
    if only_open:
        query = query.filter(Complaint.status == "open")
    complaints = query.order_by(Complaint.created_at.desc()).limit(100).all()
    result = []
    for complaint in complaints:
        user = db.get(User, complaint.user_id)
        entry = complaint_dict(complaint)
        entry["user"] = {
            "phone": user.phone if user else "?",
            "name": user.name if user else "",
            "role": user.role if user else "?",
        }
        result.append(entry)
    return result


@router.post("/complaints/{complaint_id}/resolve")
def resolve_complaint(
    complaint_id: str,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    complaint.status = "resolved"
    complaint.resolved_at = now()
    db.commit()
    return complaint_dict(complaint)


@router.get("/payments")
def list_payments(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(100).all()
    return [
        {
            "id": p.id,
            "trip_id": p.trip_id,
            "provider": p.provider,
            "provider_ref": p.provider_ref,
            "amount": p.amount,
            "status": p.status,
            "created_at": p.created_at,
        }
        for p in payments
    ]


@router.get("/drivers")
def list_drivers(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    drivers = db.query(User).filter(User.role == "driver").order_by(User.created_at.desc()).limit(200).all()
    result = []
    for driver in drivers:
        profile = db.get(DriverProfile, driver.id)
        completed = db.query(Trip).filter(
            Trip.driver_id == driver.id, Trip.status == "completed"
        ).count()
        result.append({
            "id": driver.id,
            "phone": driver.phone,
            "name": driver.name,
            "approved": bool(profile and profile.approved),
            "online": bool(profile and profile.is_online),
            "car_model": profile.car_model if profile else "",
            "plate": profile.plate if profile else "",
            "trips_completed": completed,
        })
    return result


@router.post("/drivers/{driver_id}/approve")
def approve_driver(
    driver_id: str,
    body: dict = Body(...),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    profile = db.get(DriverProfile, driver_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Driver not found")
    profile.approved = bool(body.get("approved", True))
    if not profile.approved:
        profile.is_online = False  # suspended drivers go offline immediately
    db.commit()
    return {"approved": profile.approved}


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
  body{font-family:system-ui,'Segoe UI',Tahoma,sans-serif;background:#0a1729;color:#fff;margin:0;padding:16px;max-width:640px;margin-inline:auto}
  h1{font-size:1.2rem;color:#ffa22b;margin:6px 0 14px}
  .card{background:rgba(255,255,255,.08);border-radius:16px;padding:14px;margin-bottom:12px}
  label{display:block;font-size:.82rem;color:rgba(255,255,255,.7);margin-bottom:4px}
  input,textarea{width:100%;box-sizing:border-box;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:10px;color:#fff;padding:9px;font-size:.95rem;margin-bottom:8px}
  button{background:#ffa22b;color:#221400;border:0;border-radius:12px;padding:11px 14px;font-size:.95rem;font-weight:700;cursor:pointer}
  button.full{width:100%}
  button.small{padding:6px 12px;font-size:.82rem}
  button.green{background:#34d077;color:#00210e}
  button.red{background:#ff6b6b;color:#330606}
  .row{display:flex;gap:8px}.row>div{flex:1}
  .msg{padding:10px;border-radius:10px;margin:10px 0;display:none}
  .ok{background:rgba(52,208,119,.2);color:#34d077}
  .err{background:rgba(255,107,107,.2);color:#ff6b6b}
  h3{font-size:.95rem;margin:6px 0;color:#34d077}
  .tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
  .tabs button{background:rgba(255,255,255,.1);color:#fff;font-weight:600;padding:8px 12px;border-radius:10px;font-size:.85rem}
  .tabs button.active{background:#ffa22b;color:#221400}
  .stat{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.08);font-size:.92rem}
  .stat b{color:#34d077}
  .item{border-bottom:1px solid rgba(255,255,255,.1);padding:9px 0;font-size:.9rem}
  .muted{color:rgba(255,255,255,.55);font-size:.8rem}
  .chip{display:inline-block;padding:2px 9px;border-radius:99px;font-size:.75rem}
  .chip.open{background:rgba(255,162,43,.25);color:#ffa22b}
  .chip.done{background:rgba(52,208,119,.2);color:#34d077}
</style>
</head>
<body>
<h1>🚕 لوحة تحكم تكسي واحد عراق</h1>

<div class="card" id="login">
  <label>رمز الإدارة (ADMIN_TOKEN)</label>
  <input id="token" type="password" placeholder="الصق الرمز هنا">
  <button class="full" onclick="enter()">دخول</button>
</div>

<div id="app" style="display:none">
  <div class="tabs">
    <button data-tab="stats" class="active" onclick="openTab('stats')">📊 الإحصائيات</button>
    <button data-tab="fees" onclick="openTab('fees')">💰 الرسوم</button>
    <button data-tab="incentives" onclick="openTab('incentives')">🎁 الحوافز</button>
    <button data-tab="complaints" onclick="openTab('complaints')">🧾 الشكاوى</button>
    <button data-tab="payments" onclick="openTab('payments')">💳 الدفعات</button>
    <button data-tab="drivers" onclick="openTab('drivers')">🚗 السائقون</button>
  </div>

  <div id="tab-stats" class="tab"></div>

  <div id="tab-fees" class="tab" style="display:none">
    <div class="card">
      <h3>رسوم المنصة</h3>
      <label>نسبة العمولة من كل رحلة (%)</label>
      <input id="commission_percent" type="number" step="0.5" min="0" max="50">
      <label>رسوم الحجز الثابتة (د.ع تُضاف لكل رحلة وتعود لك)</label>
      <input id="booking_fee" type="number" step="250" min="0" max="10000">
    </div>
    <div class="card" id="tariffs"></div>
    <button class="full" onclick="saveFees()">💾 حفظ — يسري فوراً</button>
  </div>

  <div id="tab-incentives" class="tab" style="display:none">
    <div id="plans"></div>
    <button class="full" style="margin-bottom:8px;background:rgba(255,255,255,.15);color:#fff" onclick="addPlan()">➕ إضافة خطة</button>
    <button class="full" onclick="savePlans()">💾 حفظ الحوافز</button>
  </div>

  <div id="tab-complaints" class="tab" style="display:none"></div>
  <div id="tab-payments" class="tab" style="display:none"></div>
  <div id="tab-drivers" class="tab" style="display:none"></div>
</div>

<div id="msg" class="msg"></div>

<script>
const TIERS = {economy:'اقتصادي', family:'عائلي', premium:'بريميوم'};
let settings = null, plans = [];
const fmt = n => (n||0).toLocaleString('en') + ' د.ع';
const when = ts => new Date(ts*1000).toLocaleString('ar-IQ');

function show(text, ok){
  const el = document.getElementById('msg');
  el.textContent = text; el.className = 'msg ' + (ok ? 'ok' : 'err');
  el.style.display = 'block';
  setTimeout(()=>{el.style.display='none'}, 4000);
}

async function api(method, path, body){
  const res = await fetch(path, {
    method,
    headers: {'X-Admin-Token': document.getElementById('token').value,
              'Content-Type': 'application/json'},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if(!res.ok) throw new Error(data.detail || res.status);
  return data;
}

async function enter(){
  try{
    settings = await api('GET','/admin/settings');
    document.getElementById('login').style.display='none';
    document.getElementById('app').style.display='block';
    fillFees(); plans = settings.incentive_plans || []; renderPlans();
    openTab('stats');
  }catch(e){ show('فشل الدخول: '+e.message, false); }
}

function openTab(name){
  document.querySelectorAll('.tab').forEach(t=>t.style.display='none');
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.toggle('active', b.dataset.tab===name));
  document.getElementById('tab-'+name).style.display='block';
  if(name==='stats') loadStats();
  if(name==='complaints') loadComplaints();
  if(name==='payments') loadPayments();
  if(name==='drivers') loadDrivers();
}

async function loadStats(){
  try{
    const s = await api('GET','/admin/stats');
    let methods = '';
    for(const [m, v] of Object.entries(s.payments_by_method))
      methods += `<div class="stat"><span>${ {cash:'نقدي',zaincash:'زين كاش',fib:'FIB',qi:'سوبر كي'}[m]||m }</span><b>${v.count} رحلة — ${fmt(v.amount)}</b></div>`;
    document.getElementById('tab-stats').innerHTML = `
      <div class="card"><h3>💵 أرباحك (العمولات المحصّلة)</h3>
        <div class="stat"><span>اليوم</span><b>${fmt(s.revenue_today)}</b></div>
        <div class="stat"><span>الإجمالي</span><b>${fmt(s.revenue_total)}</b></div>
        <div class="stat"><span>إجمالي قيمة الرحلات</span><b>${fmt(s.gross_total)}</b></div></div>
      <div class="card"><h3>🚕 الرحلات</h3>
        <div class="stat"><span>مكتملة اليوم</span><b>${s.trips_today}</b></div>
        <div class="stat"><span>مكتملة إجمالاً</span><b>${s.trips_completed}</b></div>
        <div class="stat"><span>نشطة الآن</span><b>${s.trips_active}</b></div></div>
      <div class="card"><h3>👥 المستخدمون</h3>
        <div class="stat"><span>الزبائن</span><b>${s.riders}</b></div>
        <div class="stat"><span>السائقون</span><b>${s.drivers}</b></div>
        <div class="stat"><span>سائقون متصلون الآن</span><b>${s.drivers_online}</b></div>
        <div class="stat"><span>بانتظار الاعتماد</span><b>${s.drivers_pending}</b></div>
        <div class="stat"><span>شكاوى مفتوحة</span><b>${s.complaints_open}</b></div></div>
      <div class="card"><h3>💳 الرحلات حسب طريقة الدفع</h3>${methods || '<div class="muted">لا رحلات بعد</div>'}</div>`;
  }catch(e){ show(e.message,false); }
}

function fillFees(){
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
}

async function saveFees(){
  try{
    const tariffs = {};
    for(const tier of Object.keys(TIERS)){
      tariffs[tier] = {
        base:+document.getElementById(tier+'_base').value,
        per_km:+document.getElementById(tier+'_per_km').value,
        minimum:+document.getElementById(tier+'_minimum').value,
      };
    }
    settings = await api('PUT','/admin/settings',{
      commission_percent:+document.getElementById('commission_percent').value,
      booking_fee:+document.getElementById('booking_fee').value,
      tariffs,
    });
    show('تم الحفظ — يسري على الرحلات القادمة فوراً ✅', true);
  }catch(e){ show('فشل الحفظ: '+e.message,false); }
}

function renderPlans(){
  const box = document.getElementById('plans');
  box.innerHTML = '';
  plans.forEach((p,i)=>{
    const steps = p.steps.map(s=>s.trips+':'+s.bonus).join('، ');
    box.innerHTML += `<div class="card">
      <label>عنوان الخطة</label><input id="p${i}_title" value="${p.title||''}">
      <label>الوصف</label><input id="p${i}_desc" value="${p.description||''}">
      <label>الدرجات (رحلات:مكافأة مفصولة بفواصل — مثال: 1:2000، 3:5000، 6:12000)</label>
      <input id="p${i}_steps" value="${steps}">
      <button class="small red" onclick="plans.splice(${i},1);renderPlans()">حذف الخطة</button>
    </div>`;
  });
}

function addPlan(){ plans.push({title:'', description:'', steps:[{trips:1,bonus:2000}]}); renderPlans(); }

async function savePlans(){
  try{
    const out = plans.map((p,i)=>({
      id: p.id || ('plan-'+(i+1)),
      title: document.getElementById('p'+i+'_title').value,
      description: document.getElementById('p'+i+'_desc').value,
      steps: document.getElementById('p'+i+'_steps').value
        .split(/[,،]/).map(s=>s.trim()).filter(Boolean)
        .map(pair=>{const [t,b]=pair.split(':');return {trips:+t, bonus:+b};}),
    }));
    settings = await api('PUT','/admin/settings',{incentive_plans: out});
    plans = settings.incentive_plans; renderPlans();
    show('تم حفظ خطط الحوافز — تظهر للسائقين فوراً ✅', true);
  }catch(e){ show('فشل الحفظ: '+e.message,false); }
}

async function loadComplaints(){
  try{
    const list = await api('GET','/admin/complaints?only_open=false');
    const box = document.getElementById('tab-complaints');
    if(!list.length){ box.innerHTML = '<div class="card muted">لا شكاوى بعد 🎉</div>'; return; }
    box.innerHTML = '<div class="card">' + list.map(c=>`
      <div class="item">
        <span class="chip ${c.status==='open'?'open':'done'}">${c.status==='open'?'مفتوحة':'محلولة'}</span>
        <b>${c.user.role==='driver'?'سائق':'زبون'}: ${c.user.name||c.user.phone}</b>
        <div>${c.text}</div>
        <div class="muted">${when(c.created_at)}</div>
        ${c.status==='open'?`<button class="small green" onclick="resolve('${c.id}')">✔ تمت المعالجة</button>`:''}
      </div>`).join('') + '</div>';
  }catch(e){ show(e.message,false); }
}

async function resolve(id){
  try{ await api('POST','/admin/complaints/'+id+'/resolve'); loadComplaints(); show('تم حل الشكوى ✅',true);}
  catch(e){ show(e.message,false); }
}

async function loadPayments(){
  try{
    const list = await api('GET','/admin/payments');
    const box = document.getElementById('tab-payments');
    if(!list.length){ box.innerHTML = '<div class="card muted">لا دفعات إلكترونية بعد — الدفعات النقدية تظهر في الإحصائيات.</div>'; return; }
    box.innerHTML = '<div class="card">' + list.map(p=>`
      <div class="item">
        <span class="chip ${p.status==='paid'?'done':'open'}">${ {paid:'مدفوعة',pending:'معلّقة',failed:'فاشلة'}[p.status]||p.status }</span>
        <b>${ {zaincash:'زين كاش',fib:'FIB',qi:'سوبر كي'}[p.provider]||p.provider } — ${fmt(p.amount)}</b>
        <div class="muted">رحلة ${p.trip_id.slice(0,8)} · ${when(p.created_at)}</div>
      </div>`).join('') + '</div>';
  }catch(e){ show(e.message,false); }
}

async function loadDrivers(){
  try{
    const list = await api('GET','/admin/drivers');
    const box = document.getElementById('tab-drivers');
    if(!list.length){ box.innerHTML = '<div class="card muted">لا سائقين مسجلين بعد.</div>'; return; }
    box.innerHTML = '<div class="card">' + list.map(d=>`
      <div class="item">
        <b>${d.name||d.phone}</b> ${d.online?'<span class="chip done">متصل</span>':''}
        <span class="chip ${d.approved?'done':'open'}">${d.approved?'معتمد':'بانتظار الاعتماد'}</span>
        <div class="muted">${d.phone} · ${d.car_model} ${d.plate} · ${d.trips_completed} رحلة</div>
        <button class="small ${d.approved?'red':'green'}" onclick="approve('${d.id}', ${!d.approved})">
          ${d.approved?'⏸ إيقاف السائق':'✔ اعتماد السائق'}</button>
      </div>`).join('') + '</div>';
  }catch(e){ show(e.message,false); }
}

async function approve(id, approved){
  try{ await api('POST','/admin/drivers/'+id+'/approve',{approved}); loadDrivers(); show('تم التحديث ✅',true);}
  catch(e){ show(e.message,false); }
}
</script>
</body>
</html>"""
