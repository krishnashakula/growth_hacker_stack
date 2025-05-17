import os, time, requests, psycopg2, schedule
from datetime import datetime

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
                datetime.utcnow(),
            ),
        )
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    schedule.every().hour.do(fetch_and_store)
    while True:
        schedule.run_pending()
        time.sleep(30)
