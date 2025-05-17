Here’s a more polished, developer-friendly **README.md** that’s structured, detailed, and ready for production:

````markdown
# 🚀 Growth-Hacker LinkedIn Automation Stack

> Fully self-hosted, AI-driven LinkedIn growth toolkit, featuring:
> - **Keyword Mining:** Google Trends RSS + Transformers NER  
> - **Content Generation:** Dynamic hook styles + ChatGPT integration  
> - **Orchestration & Scheduling:** n8n workflows, cron triggers  
> - **Engagement Capture:** Automated stats collection via LinkedIn API  
> - **Analytics & Dashboards:** PostgreSQL + Metabase  
> - **Reinforcement Learning:** ε-greedy bandit adapts best hook style  

---

## 📋 Table of Contents

1. [Features](#features)  
2. [Prerequisites](#prerequisites)  
3. [Getting Started](#getting-started)  
4. [Architecture](#architecture)  
5. [Configuration](#configuration)  
6. [n8n Workflow](#n8n-workflow)  
7. [Advanced Usage](#advanced-usage)  
8. [Troubleshooting](#troubleshooting)  
9. [Contributing](#contributing)  
10. [License](#license)  

---

## 🔥 Features

- **AI-Powered Keywords**  
  - Fetch top “Trending Now” topics via public Google Trends RSS  
  - Extract entities with Hugging Face NER for deep insight  

- **Content Generation**  
  - ε-greedy bandit selects hook style: Question, Stat, Story, Quote  
  - ChatGPT crafts polished LinkedIn posts from hooks + keywords  

- **Automation**  
  - n8n handles HTTP requests, function logic, and LinkedIn posting  
  - Cron scheduling, retry logic, error handling  

- **Engagement & Analytics**  
  - Hourly pull of like/comment counts via LinkedIn SocialActions API  
  - Persist metrics in PostgreSQL  
  - Visualize trends in Metabase  

- **Adaptive Learning**  
  - Bandit updates hook-style weights based on post performance  
  - Drives continuous improvement in engagement rates  

---

## ⚙️ Prerequisites

- Docker & Docker Compose (v2)  
- Git  
- [LinkedIn Developer App](https://www.linkedin.com/developers/) with:  
  - **ugcPost** & **r_liteprofile** / **w_member_social** scopes  
- [OpenAI API key](https://platform.openai.com/) (optional, for ChatGPT)  
- Local machine or VPS with ≥2 GB RAM (t2.micro requires swap)  

---

## 🚀 Getting Started

```bash
# 1. Clone repo
git clone https://github.com/yourname/growth_hacker_stack.git
cd growth_hacker_stack

# 2. Configure
cp .env.example .env
# ✏️ Edit .env → fill in API keys, tokens, DB creds

# 3. Launch Postgres & init schema
docker compose up -d db
sleep 10                                       # give Postgres time to start
docker exec -i growth_hacker_stack-db-1 psql   \
  -U $POSTGRES_USER -d $POSTGRES_DB -f sql/init.sql

# 4. Bring up full stack
docker compose up -d --build

# 5. Access services
n8n UI:        http://localhost:5678  
Keyword API:  http://localhost:8000/keywords  
Metabase:      http://localhost:3000  
````

---

## 🏗️ Architecture

```text
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

---

## 🔧 Configuration

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

---

## ⚙️ n8n Workflow

1. **Import** `workflows/linkedin_workflow.json` via n8n **Settings → Import**.
2. **Verify** credentials (LinkedIn OAuth2 + OpenAI).
3. **Execute** and watch your LinkedIn feed light up!
4. **Schedule** as needed (daily, hourly, etc.).

---

## 🛠 Advanced Usage

* **Custom Hooks**: Extend `Select Hook Style` with new categories.
* **Metrics Dashboard**: Build custom Metabase charts on `post_stats`.
* **Scaling**: Split services onto multiple VPS / use RDS + EFS.
* **Alerts**: Add email/pagerduty via n8n if post engagement dips.

---

## ❗ Troubleshooting

* **Docker Warnings**: Remove `version:` from `docker-compose.yml`.
* **Port Conflicts**: Adjust mappings (`5678`, `8000`, `3000`).
* **Memory Limits**: Add swap on low-RAM hosts.
* **Auth Errors**: Verify `.env` values, recreate containers.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/xyz`)
3. Commit with clear messages (`git commit -m "feat: add X"`).
4. Open a pull request — we use semantic commits and code reviews.

---

## 📄 License

MIT © [Your Name](https://github.com/yourname)

```

This version adds:

- **Badges**-style headers and section anchors  
- A **Table of Contents** for quick navigation  
- Clear **Architecture diagram** ASCII  
- Detailed **Environment Variables** table  
- **Advanced** and **Troubleshooting** sections  
- **Contributing** guidelines with semantic-commit style  

Happy hacking! 🚀
```
