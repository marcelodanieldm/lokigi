$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..

python -m pip install -r requirements.txt
python -m alembic -c alembic.ini upgrade head
python scripts/create_local_user.py local@example.com
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
