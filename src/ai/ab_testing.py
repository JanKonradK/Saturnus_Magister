"""
A/B Testing Framework for AI Prompts.
Allows running experiments to compare different classifier prompts.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from src.ai.classifier import EmailClassifier
from src.db.models import EmailModel, EmailClassification

@dataclass
class ExperimentResult:
    experiment_id: str
    timestamp: str
    total_samples: int
    success_count: int
    avg_confidence: float
    results: List[Dict[str, Any]]

class ABTester:
    """Runs A/B tests on classifier prompts."""

    def __init__(self, classifier: EmailClassifier):
        self.classifier = classifier
        self.results_dir = "experiments/results"
        os.makedirs(self.results_dir, exist_ok=True)

    async def run_experiment(
        self,
        name: str,
        emails: List[EmailModel],
        system_prompt_override: str = None
    ) -> ExperimentResult:
        """
        Run classification on a set of emails with a specific prompt.
        """
        print(f"🧪 Starting Experiment: {name}")
        print(f"   Samples: {len(emails)}")

        results = []
        success_count = 0
        total_confidence = 0.0

        # Override prompt if provided
        original_prompt = self.classifier.SYSTEM_PROMPT
        if system_prompt_override:
            self.classifier.SYSTEM_PROMPT = system_prompt_override

        try:
            for email in emails:
                start_time = datetime.now()
                classification = await self.classifier.classify(email)
                duration = (datetime.now() - start_time).total_seconds()

                is_success = classification.category != "unknown"
                if is_success:
                    success_count += 1
                    total_confidence += classification.confidence

                results.append({
                    "email_id": email.gmail_id,
                    "subject": email.subject,
                    "category": classification.category.value,
                    "confidence": classification.confidence,
                    "duration_seconds": duration,
                    "success": is_success
                })
                print(f"   - {email.subject[:30]}... -> {classification.category.value} ({classification.confidence:.2f})")

        finally:
            # Restore prompt
            self.classifier.SYSTEM_PROMPT = original_prompt

        # Calculate metrics
        avg_conf = total_confidence / success_count if success_count > 0 else 0.0

        experiment_result = ExperimentResult(
            experiment_id=name,
            timestamp=datetime.now().isoformat(),
            total_samples=len(emails),
            success_count=success_count,
            avg_confidence=avg_conf,
            results=results
        )

        self._save_results(experiment_result)
        return experiment_result

    def _save_results(self, result: ExperimentResult):
        """Save experiment results to JSON."""
        filename = f"{self.results_dir}/{result.experiment_id}_{int(datetime.now().timestamp())}.json"
        with open(filename, "w") as f:
            json.dump(asdict(result), f, indent=2)
        print(f"📝 Results saved to {filename}")

# Example usage script
if __name__ == "__main__":
    # This would be run to test new prompts
    pass
