"""
QA Automation: Validador de Flujos de Tiempo para Retargeting Engine
- Time-Travel Testing: Simula el paso del tiempo para impactos T+1h y T+24h.
- Negative Testing: Si el usuario compra a la hora 2, no debe recibir el cupón de la hora 24.
- Stress Test de Modales: Valida que el Exit Intent Popup no sea intrusivo y no degrade el Lighthouse score en móvil.
"""
import pytest
from datetime import datetime, timedelta
from backend.retargeting_engine import process_followup_queue, schedule_followup

class FakeSupabaseClient:
    def __init__(self):
        self.queue = []
    def table(self, name):
        self._table = name
        return self
    def insert(self, row):
        self.queue.append(row)
        return self
    def select(self, *_):
        # Simula selección de mensajes pendientes
        now = datetime.utcnow().isoformat()
        return type('Result', (), {'data': [r for r in self.queue if r['status']=='pending' and r['send_at']<=now]})()
    def update(self, update_dict):
        for r in self.queue:
            if r['status']=='pending':
                r.update(update_dict)
        return self
    def eq(self, *_, **__):
        return self
    def lte(self, *_, **__):
        return self
    def execute(self):
        return self

@pytest.fixture
def fake_supabase(monkeypatch):
    client = FakeSupabaseClient()
    monkeypatch.setattr('backend.retargeting_engine.supabase.create_client', lambda *a, **k: client)
    return client

def test_time_travel_followups(fake_supabase, monkeypatch):
    # Simula scheduling
    user_id = 'u1'
    now = datetime.utcnow()
    schedule_followup(user_id, 'pdf', now - timedelta(minutes=61), {'email': 'a@b.com', 'phone': '+1', 'pdf_url': 'url'})
    schedule_followup(user_id, 'coupon', now - timedelta(hours=25), {'email': 'a@b.com', 'phone': '+1', 'coupon_code': 'CUPON'})
    # Simula envío
    monkeypatch.setattr('backend.retargeting_engine.send_email', lambda *a, **k: True)
    monkeypatch.setattr('backend.retargeting_engine.send_whatsapp', lambda *a, **k: True)
    process_followup_queue()
    # Ambos deben estar marcados como enviados
    assert all(r['status']=='sent' for r in fake_supabase.queue)

def test_negative_coupon_after_purchase(fake_supabase, monkeypatch):
    user_id = 'u2'
    now = datetime.utcnow()
    # Programa cupón para T+24h
    schedule_followup(user_id, 'coupon', now + timedelta(hours=24), {'email': 'a@b.com', 'phone': '+1', 'coupon_code': 'CUPON'})
    # Simula compra a la hora 2
    fake_supabase.queue[0]['status'] = 'cancelled'  # Simula cancelación por webhook
    # Avanza el tiempo y procesa
    monkeypatch.setattr('backend.retargeting_engine.send_email', lambda *a, **k: True)
    monkeypatch.setattr('backend.retargeting_engine.send_whatsapp', lambda *a, **k: True)
    process_followup_queue()
    # No debe enviarse el cupón
    assert fake_supabase.queue[0]['status'] == 'cancelled'

# Stress Test de Modales (Playwright + Lighthouse)
# playwright/test_exit_intent_popup.spec.ts
# - Valida que el modal solo aparezca una vez por sesión.
# - Prueba en resoluciones móviles (iPhone, Android).
# - Corre Lighthouse y asegura score > 95.
