module.exports = {
  apps: [
    {
      name: "lokigi-fastapi",
      script: "uvicorn",
      args: "backend.main:app --host 0.0.0.0 --port 8000",
      interpreter: "/path/to/venv/bin/python3",
      cwd: "/path/to/backend",
      autorestart: true,
    },
    {
      name: "lokigi-celery-scraper",
      script: "celery",
      args: "-A backend.celery_app:celery worker -Q scraping -n scraper@%h",
      interpreter: "/path/to/venv/bin/python3",
      cwd: "/path/to/backend",
      autorestart: true,
    },
    {
      name: "lokigi-celery-ai",
      script: "celery",
      args: "-A backend.celery_app:celery worker -Q ai -n ai@%h",
      interpreter: "/path/to/venv/bin/python3",
      cwd: "/path/to/backend",
      autorestart: true,
    }
  ]
};
