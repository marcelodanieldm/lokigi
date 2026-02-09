"""
Script simple para probar login sin ejecutar servidor en background
"""
import subprocess
import time
import requests
import sys

print("🚀 Iniciando servidor FastAPI...")
print("="*60)

# Iniciar servidor en subprocess
process = subprocess.Popen(
    ["python", "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Esperar a que el servidor esté listo
print("⏳ Esperando a que el servidor esté listo...")
max_wait = 15
waited = 0
server_ready = False

while waited < max_wait:
    try:
        response = requests.get("http://127.0.0.1:8000/docs", timeout=1)
        if response.status_code == 200:
            server_ready = True
            print("✅ Servidor listo!\n")
            break
    except:
        pass
    
    time.sleep(1)
    waited += 1
    sys.stdout.write(f"\r⏳ Esperando... {waited}/{max_wait}s")
    sys.stdout.flush()

if not server_ready:
    print("\n❌ El servidor no arrancó a tiempo")
    process.terminate()
    sys.exit(1)

print("\n" + "="*60)
print("🔐 Probando login con credenciales...")
print("="*60)

# Test 1: ADMIN
print("\n1️⃣  TEST: Login como ADMIN")
try:
    response = requests.post(
        "http://127.0.0.1:8000/api/auth/login",
        json={"username": "admin@lokigi.com", "password": "admin123"},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login exitoso!")
        print(f"   - Usuario: {data['user']['email']}")
        print(f"   - Rol: {data['user']['role'].upper()}")
        print(f"   - Token: {data['access_token'][:40]}...")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: WORKER
print("\n2️⃣  TEST: Login como WORKER")
try:
    response = requests.post(
        "http://127.0.0.1:8000/api/auth/login",
        json={"username": "worker@lokigi.com", "password": "worker123"},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login exitoso!")
        print(f"   - Usuario: {data['user']['email']}")
        print(f"   - Rol: {data['user']['role'].upper()}")
        print(f"   - Token: {data['access_token'][:40]}...")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: CUSTOMER
print("\n3️⃣  TEST: Login como CUSTOMER")
try:
    response = requests.post(
        "http://127.0.0.1:8000/api/auth/login",
        json={"username": "cliente@example.com", "password": "cliente123"},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login exitoso!")
        print(f"   - Usuario: {data['user']['email']}")
        print(f"   - Rol: {data['user']['role'].upper()}")
        print(f"   - Token: {data['access_token'][:40]}...")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("🏁 Pruebas completadas")
print("="*60)

# Cerrar servidor
print("\n⏹️  Cerrando servidor...")
process.terminate()
process.wait(timeout=5)
print("✅ Servidor cerrado")
