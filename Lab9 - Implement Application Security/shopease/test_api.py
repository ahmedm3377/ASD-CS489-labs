import os
import time
import threading

from . import seed


def run_server():
    # run uvicorn programmatically
    import uvicorn

    uvicorn.run("shopease.app:app", host="127.0.0.1", port=8080)


def main():
    # seed data into sqlite db
    db_url = os.environ.get("DATABASE_URL") or "sqlite:///./shopease.db"
    seed.seed_all(db_url)

    # start server in background thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)

    import requests

    resp = requests.get("http://127.0.0.1:8080/adsweb/api/v1/tickets")
    print("Status:", resp.status_code)
    print(resp.json())


if __name__ == "__main__":
    main()
