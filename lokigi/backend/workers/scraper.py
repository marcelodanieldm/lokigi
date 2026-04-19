from backend.celery_app import celery

if __name__ == "__main__":
    celery.worker_main(["worker", "-Q", "scraping", "-n", "scraper@%h"])
