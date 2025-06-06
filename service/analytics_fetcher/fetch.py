import os
from datetime import datetime, UTC

# Third party libraries like ``requests`` or ``psycopg2`` aren't installed in
# the test environment. Import them lazily and provide simple stubs so that the
# tests can patch the expected attributes without the real dependencies being
# available.
try:  # pragma: no cover - executed only when deps are present
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed in CI
    class _RequestsStub:
        def get(self, *a, **k):
            raise ModuleNotFoundError("requests is required")

    requests = _RequestsStub()  # type: ignore

try:  # pragma: no cover
    import psycopg2  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class _Psycopg2Stub:
        def connect(self, *a, **k):
            raise ModuleNotFoundError("psycopg2 is required")

    psycopg2 = _Psycopg2Stub()  # type: ignore

TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
DB = dict(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)


def fetch_and_store():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("SELECT post_id FROM posts;")
    for (pid,) in cur.fetchall():
        url = f"https://api.linkedin.com/v2/socialActions/{pid}?projection=(commentCount,likeCount)"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        data = requests.get(url, headers=headers, timeout=10).json()
        cur.execute(
            "INSERT INTO post_stats (post_id, like_count, comment_count, fetched_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (
                pid,
                data.get("likeCount", 0),
                data.get("commentCount", 0),
                datetime.now(UTC),
            ),
        )
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    import schedule
    import time

    schedule.every().hour.do(fetch_and_store)
    while True:
        schedule.run_pending()
        time.sleep(30)
