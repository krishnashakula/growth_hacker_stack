# 🚀 Growth-Hacker LinkedIn Automation Stack

Fully self-hosted, AI-driven LinkedIn growth toolkit, featuring:

* **Keyword Mining:** Google Trends RSS + Transformers NER
* **Content Generation:** Dynamic hook styles + ChatGPT integration
* **Orchestration & Scheduling:** n8n workflows, cron triggers
* **Engagement Capture:** Automated stats collection via LinkedIn API
* **Analytics & Dashboards:** PostgreSQL + Metabase
* **Reinforcement Learning:** ε-greedy bandit adapts best hook style

## Table of Contents

1. Features

2. Prerequisites

3. Getting Started

4. Architecture

5. Configuration

6. n8n Workflow

7. Advanced Usage

8. Troubleshooting

9. Contributing

10. License

11. Features

---

* **AI-Powered Keywords**

  * Fetch top “Trending Now” topics via public Google Trends RSS
  * Extract entities with Hugging Face NER for deep insight

* **Content Generation**

  * ε-greedy bandit selects hook style: Question, Stat, Story, Quote
  * ChatGPT crafts polished LinkedIn posts from hooks + keywords

* **Automation**

  * n8n handles HTTP requests, function logic, and LinkedIn posting
  * Cron scheduling, retry logic, error handling

* **Engagement & Analytics**

  * Hourly pull of like/comment counts via LinkedIn SocialActions API
  * Persist metrics in PostgreSQL
  * Visualize trends in Metabase

* **Adaptive Learning**

  * Bandit updates hook-style weights based on post performance
  * Drives continuous improvement in engagement rates

2. Prerequisites

---

* Docker & Docker Compose (v2)
* Git
* LinkedIn Developer App with **ugcPost**, **r\_liteprofile**, **w\_member\_social** scopes
* OpenAI API key (optional, for ChatGPT integration)
* Local machine or VPS with ≥2 GB RAM (t2.micro requires swap)

3. Getting Started

---

```bash
# 1. Clone repo
git clone https://github.com/yourname/growth_hacker_stack.git
cd growth_hacker_stack

# 2. Configure
cp .env.example .env
# ✏️ Edit .env → fill in API keys, tokens, DB creds

# 3. Launch Postgres & init schema
docker compose up -d db
sleep 10
docker exec -i growth_hacker_stack-db-1 psql \
  -U $POSTGRES_USER -d $POSTGRES_DB -f sql/init.sql

# 4. Bring up full stack
docker compose up -d --build

# 5. Access services
#    • n8n UI:        http://localhost:5678  
#    • Keyword API:  http://localhost:8000/keywords  
#    • Metabase:      http://localhost:3000  
```

4. Architecture

---

```
┌───────────────────────┐
│     n8n (Orchestrator)│
│ ┌──────────┐           │
│ │Fetch RSS │──┐        │
│ └──────────┘  │        │
│ ┌──────────┐  │        │
│ │ Bandit   │──┼──▶ ChatGPT (Optional) ──▶ LinkedIn API
│ └──────────┘  │        │
│ ┌──────────┐  │        │
│ │Post Stats│◀─┘        │
│ └──────────┘           │
└──┬────────────────────┬┘
   │                    │
   ▼                    ▼
Postgres           Trending Service
(Metrics & Hooks)  (Google Trends RSS)
```

5. Configuration

---

All secrets are managed in **`.env`**:

| Variable                 | Description                                 |
| ------------------------ | ------------------------------------------- |
| `LINKEDIN_CLIENT_ID`     | LinkedIn App Client ID                      |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn App Client Secret                  |
| `LINKEDIN_ACCESS_TOKEN`  | 60-day LinkedIn OAuth2 token                |
| `LINKEDIN_PERSON_URN`    | Your profile URN (e.g. `urn:li:person:XXX`) |
| `OPENAI_API_KEY`         | Optional for ChatGPT post generation        |
| `POSTGRES_*`             | DB host, port, name, user, password         |
| `SWAP_SIZE_GB`           | (Optional) on t2.micro, e.g. `1`            |

6. n8n Workflow

---

1. Import `workflows/linkedin_workflow.json` via **Settings → Import**.

2. Verify credentials (LinkedIn OAuth2 + OpenAI).

3. Execute to post a test LinkedIn update.

4. Schedule triggers (daily, hourly, etc.) as needed.

5. Advanced Usage

---

* **Custom Hooks:** Extend `Select Hook Style` with new categories.
* **Metrics Dashboard:** Build Metabase charts on `post_stats`.
* **Scaling:** Split services across multiple hosts or use RDS/EFS.
* **Alerts:** Add email or PagerDuty notifications via n8n on low engagement.

8. Troubleshooting

---

* **Remove** obsolete `version:` from `docker-compose.yml`.
* **Adjust** port mappings if conflicts occur (5678, 8000, 3000).
* **Add** swap on low-RAM hosts (`SWAP_SIZE_GB=1`).
* **Recreate** containers after `.env` changes to load new vars.

9. Contributing

---

1. Fork the repo

2. Create a feature branch (`git checkout -b feat/xyz`)

3. Commit with semantic messages (`git commit -m "feat: add XYZ"`)

4. Open a Pull Request for review

5. License

---

MIT © [Krishna Shakula](https://github.com/krishnashakula)

Enjoy autonomous growth! 🚀
ECHO is on.
