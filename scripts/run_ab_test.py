"""
Script to run A/B tests on classifier prompts.
"""

import asyncio
from datetime import datetime
from src.ai.classifier import EmailClassifier
from src.ai.ab_testing import ABTester
from src.db.models import EmailModel

# Synthetic test data
TEST_EMAILS = [
    EmailModel(
        gmail_id="1", thread_id="1", subject="Interview Invite",
        sender_email="hr@google.com", recipient_email="me@me.com", received_at=datetime.now(),
        body_text="Can we schedule a chat for the SWE role?"
    ),
    EmailModel(
        gmail_id="2", thread_id="2", subject="Application Update",
        sender_email="no-reply@greenhouse.io", recipient_email="me@me.com", received_at=datetime.now(),
        body_text="Thank you for applying. Unfortunately we are not moving forward."
    ),
    EmailModel(
        gmail_id="3", thread_id="3", subject="Take home assignment",
        sender_email="eng@startup.com", recipient_email="me@me.com", received_at=datetime.now(),
        body_text="Here is the link to your coding challenge. Due in 48 hours."
    ),
]

# Challenger Prompt (Example: More concise)
CHALLENGER_PROMPT = """
You are an expert email classifier.
Analyze the email and return JSON with:
- category: [interview_invite, rejection, assignment, offer, info, unknown]
- sentiment: [positive, negative, neutral]
- confidence: 0.0 to 1.0
- extracted_data: {dates, deadlines}

Be strict. If unsure, use 'unknown'.
"""

async def main():
    classifier = EmailClassifier()
    tester = ABTester(classifier)

    print("🚀 Starting A/B Test Run\n")

    # 1. Run Baseline (Current System Prompt)
    print("--- Running Baseline ---")
    baseline_results = await tester.run_experiment(
        name="baseline_v1",
        emails=TEST_EMAILS
    )

    # 2. Run Challenger
    print("\n--- Running Challenger ---")
    challenger_results = await tester.run_experiment(
        name="challenger_concise_v1",
        emails=TEST_EMAILS,
        system_prompt_override=CHALLENGER_PROMPT
    )

    # Compare
    print("\n📊 Comparison:")
    print(f"Baseline Avg Confidence: {baseline_results.avg_confidence:.2f}")
    print(f"Challenger Avg Confidence: {challenger_results.avg_confidence:.2f}")

    if challenger_results.avg_confidence > baseline_results.avg_confidence:
        print("✅ Challenger performed better!")
    else:
        print("❌ Baseline performed better.")

if __name__ == "__main__":
    asyncio.run(main())
