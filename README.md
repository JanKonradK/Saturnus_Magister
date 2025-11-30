# Saturnus_Magister

> **"Master of Time"** - Autonomous email orchestration system for job application management

Saturnus_Magister monitors your Gmail, classifies emails with Grok AI, matches them to your [Nyx_Venatrix](https://github.com/JanKonradK/Nyx_Venatrix) job applications, and intelligently routes everything to TickTick using the Eisenhower Matrix.

## 🎯 What It Does

```
Gmail Inbox → Grok Classification → Job Matching → TickTick Routing → Analytics
     ↓              ↓                      ↓                ↓              ↓
 Monitors      Categories          Links to Jobs    Eisenhower     Tracks All
 24/7          14 types            (Nyx_Venatrix)   + Calendar     Responses
```

## ✨ Key Features

- 🤖 **AI-Powered**: Grok 4.1 Fast classification with sentiment analysis
- 🎯 **Smart Matching**: Multi-signal fuzzy matching to job applications
- 📊 **Eisenhower Matrix**: Automatic task prioritization (Q1-Q4)
- 📅 **Calendar Sync**: Auto-creates events for interviews and deadlines
- 📈 **Analytics**: Tracks ALL responses (positive + negative) for insights
- 🔍 **Manual Review**: Queue for uncertain matches with interactive TUI

## 🚀 Quick Start

```bash
# 1. Install
pip install -e .

# 2. Setup
cp .env.example .env
# Edit .env with your credentials

# 3. Run migrations
psql $DATABASE_URL -f src/db/migrations/001_initial.sql
psql $DATABASE_URL -f src/db/migrations/002_add_countdown.sql

# 4. Authenticate
python scripts/ticktick_oauth.py   # TickTick OAuth
python -m src.cli.setup             # Get project IDs

# 5. Run
python -m src.main
```

**First run**: Gmail OAuth opens in browser → authenticate → system starts monitoring

## 📚 Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get running in 10 minutes
- **[Implementation Details](docs/IMPLEMENTATION.md)** - Architecture and design
- **[Production Deployment](docs/PRODUCTION_READY.md)** - Deployment checklist
- **[Complete Summary](docs/DEPLOYMENT_SUMMARY.md)** - Everything in one place

### Folder-Specific Documentation

Each major directory contains its own README explaining its purpose:

- [`src/`](src/README.md) - Core application code
- [`src/ai/`](src/ai/README.md) - AI classification and job matching
- [`src/clients/`](src/clients/README.md) - External API integrations
- [`src/db/`](src/db/README.md) - Database models and migrations
- [`src/services/`](src/services/README.md) - Business logic orchestration
- [`src/cli/`](src/cli/README.md) - Command-line tools
- [`tests/`](tests/README.md) - Test suite
- [`scripts/`](scripts/README.md) - Setup and utility scripts
- [`docker/`](docker/README.md) - Containerization configs

## 🏗️ Architecture

```
saturnus_magister/
├── src/
│   ├── ai/              # Grok classification + job matching
│   ├── clients/         # Gmail, TickTick, Google Calendar APIs
│   ├── db/              # PostgreSQL models, repository, migrations
│   ├── services/        # Email processor, task router, job linker
│   ├── cli/             # Manual review TUI, setup tools
│   ├── config.py        # Pydantic settings
│   └── main.py          # Entry point
├── tests/               # Unit tests
├── scripts/             # OAuth and utility scripts
├── docker/              # Docker + docker-compose
└── docs/                # Comprehensive documentation
```

## ⚙️ Requirements

- **Python 3.14+** (preferably free-threaded build)
- **PostgreSQL** (shared with Nyx_Venatrix)
- **Gmail API** access
- **TickTick** account with Eisenhower Matrix
- **xAI API key** (for Grok)

## 🔧 Configuration

Create `.env` with:

```env
# Database (shared with Nyx_Venatrix)
DATABASE_URL=postgresql://user:password@host:5432/database

# xAI / Grok
XAI_API_KEY=xai-your-key-here

# TickTick
TICKTICK_ACCESS_TOKEN=...
TICKTICK_CLIENT_ID=...
TICKTICK_CLIENT_SECRET=...
TICKTICK_Q1_PROJECT=...  # Get from `saturnus-setup`
TICKTICK_Q2_PROJECT=...
TICKTICK_Q3_PROJECT=...
TICKTICK_Q4_PROJECT=...
TICKTICK_WORK_PROJECT=...
```

See [`.env.example`](.env.example) for all options.

## 📊 Email Processing Pipeline

1. **Fetch** emails from Gmail (inbox + sent)
2. **Classify** with Grok (category + sentiment + data extraction)
3. **Match** to Nyx_Venatrix jobs (fuzzy matching + AI disambiguation)
4. **Route** to TickTick (Eisenhower + Work + Calendar + Countdown)
5. **Record** analytics (all responses tracked)
6. **Queue** uncertain matches for manual review

## 🎯 Eisenhower Matrix Routing

| Quadrant | When | Examples |
|----------|------|----------|
| **Q1** Urgent + Important | Interview invites, offers | High priority, immediate action |
| **Q2** Not Urgent + Important | Assignments, follow-ups | Schedule properly, important work |
| **Q3** Urgent + Not Important | Quick acknowledgments | Delegate or handle quickly |
| **Q4** Not Urgent + Not Important | Low-effort rejections | Record only, minimal action |

## 🛠️ CLI Tools

```bash
saturnus              # Main email processor
saturnus-review       # Manual review queue (interactive TUI)
saturnus-setup        # Get TickTick project IDs
```

## 🐳 Docker

```bash
# Standalone
docker-compose -f docker/docker-compose.yml up -d

# With Nyx_Venatrix network
docker-compose -f docker/docker-compose.yml up saturnus -d
```

See [`docker/README.md`](docker/README.md) for details.

## 📈 Analytics

Saturnus_Magister records **all** email responses (positive + negative) for:

- Success rate by company
- Average response time by stage
- Rejection patterns
- Effort vs. outcome correlation
- Company blocklist suggestions

## 🔄 Integration with Nyx_Venatrix

Shares PostgreSQL database and reads from `applied_jobs` table:
- Links emails to job applications
- Tracks effort levels
- Analyzes application outcomes

## 🚧 Roadmap

- **Phase 2**: Cloud migration (AWS Lambda / GCP Cloud Run)
- **Phase 3**: Auto-reply capability
- **Phase 4**: Full calendar scheduling automation

## 🧪 Testing

```bash
pytest                 # Run tests
mypy src              # Type checking
ruff check src        # Linting
```

## 📝 License

MIT License

## 🔗 Related Projects

- [Nyx_Venatrix](https://github.com/JanKonradK/Nyx_Venatrix) - Autonomous job application agent

---

**Built for Python 3.14 free-threading** | **Production-ready** | **~3,000 lines of code**
