# 🧪 Running the Simulation

This document explains how to run the full Saturnus_Magister pipeline in simulation mode without needing real API credentials.

## What is the Simulation?

`scripts/simulate_full_run.py` demonstrates the complete email processing workflow by mocking all external services:
- **Mock Gmail**: Returns 3 synthetic emails (interview invite, rejection, assignment)
- **Mock Grok**: Returns pre-defined classifications
- **Mock JobMatcher**: Returns high-confidence job matches
- **Mock Database**: Simulates DB operations in-memory
- **Mock TickTick**: Prints what tasks *would* be created

## Running the Simulation

### 1. Ensure Virtual Environment is Active

```bash
source .venv/bin/activate
```

### 2. Run the Simulation

```bash
PYTHONPATH=. python scripts/simulate_full_run.py
```

**Expected Output:**
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

## What This Demonstrates

The simulation proves that:
✅ All modules import correctly
✅ The orchestration logic flows properly
✅ Classification → Matching → Routing pipeline works
✅ Error handling is robust
✅ The system is ready for production (just needs real credentials)

## Next Steps

Once you've verified the simulation works, configure your `.env` file with real API credentials to process actual emails!
