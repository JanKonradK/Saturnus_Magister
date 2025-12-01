# Simulation Mode

Demonstrates the complete processing pipeline without requiring real API credentials.

## What It Does

Mocks all external services (Gmail, AI agent, TickTick, PostgreSQL) and processes 3 synthetic emails through the classification → matching → routing workflow.

## Running

```bash
PYTHONPATH=. python scripts/simulate_full_run.py
```

## Expected Output

```
╭────────────────────────────────────────────╮
│ Saturnus_Magister Simulation               │
│ Running full pipeline with MOCKED services │
╰────────────────────────────────────────────╯
✓ Saturnus_Magister initialized

🚀 Starting Processing Cycle...

Fetching inbox emails...
📧 MockGmail: Fetching inbox...
  Classifying: Interview with TechCorp
🧠 MockGrok: Classifying 'Interview with TechCorp'...
🔗 MockMatcher: Linking 'Interview with TechCorp'...
  ✓ interview_invite (positive)
  ...

📊 Simulation Stats:
{'inbox_processed': 3, 'sent_processed': 0, 'errors': 0}

✨ Simulation Complete!
```

## Verification

Confirms:
- Module imports resolve correctly
- Classification → matching → routing pipeline functions
- Error handling works
- System ready for production deployment

Once simulation passes, configure `.env` with real credentials.
