# `src/ai/` - AI-Powered Classification and Matching

This module contains the AI components for email classification and job matching.

## Components

### `classifier.py` - Email Classification

Uses **Grok 4.1 Fast** from xAI to classify emails with high accuracy.

**Purpose**: Determine email category, sentiment, and extract structured data.

**Categories** (14 total):
- **Inbound**: `interview_invite`, `assignment`, `rejection`, `offer`, `info`, `follow_up_needed`, `unknown`
- **Outbound**: `sent_application`, `sent_availability`, `sent_follow_up`, `sent_documents`, `info`

**Sentiment**: `positive`, `negative`, `neutral`

**Extraction**: Dates, deadlines, interviewer names, meeting links, salary mentions

**Design**:
```python
class EmailClassifier:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.xai_api_key)

    async def classify(self, email: EmailModel) -> EmailClassification:
        # Uses few-shot prompting with system instructions
        # Returns structured JSON with category, sentiment, confidence
        # Extracts actionable data (dates, deadlines, etc.)
```

**Why Grok**:
- Fast inference (4.1 Fast variant)
- Strong reasoning for email context
- Structured output support
- Cost-effective for high-volume processing

### `job_matcher.py` - Job Matching Logic

Matches emails to Nyx_Venatrix job applications using multiple signals.

**Purpose**: Link incoming emails to specific job applications with confidence scoring.

**Matching Signals** (with weights):
1. **Company Name Fuzzy** (40%) - Uses RapidFuzz ratio matching
2. **Email Domain** (20%) - Exact domain matching (e.g., `@google.com`)
3. **Position Title Fuzzy** (30%) - Fuzzy match on job title
4. **Timeline Proximity** (10%) - Linear decay over 90-day window

**Thresholds**:
- **≥ 0.85**: Auto-match (high confidence)
- **0.50-0.84**: Queue for manual review
- **< 0.50**: No match (still recorded)

**AI Disambiguation**:
When multiple jobs have similar scores, Grok re-ranks candidates by analyzing:
- Company name mentions in email body
- Position title references
- Email domain vs. company domain
- Application timeline (recent = more likely)
- Unique identifiers (job IDs, application numbers)

**Design**:
```python
class JobMatcher:
    def __init__(self, repository: DatabaseRepository):
        self.repository = repository
        self.client = AsyncOpenAI(...)

    async def find_matches(self, email: EmailModel) -> List[JobMatchCandidate]:
        # 1. Fetch recent jobs from Nyx_Venatrix (90 days)
        # 2. Calculate fuzzy scores for each signal
        # 3. Weight and combine scores
        # 4. Return ranked candidates

    async def disambiguate_with_ai(
        self, email: EmailModel, candidates: List[JobMatchCandidate]
    ) -> Optional[JobMatchCandidate]:
        # Uses Grok to re-rank when scores are close
```

## Why This Architecture?

### Fuzzy + AI Hybrid Approach

**Fuzzy matching first** (fast, deterministic):
- Handles exact/near-exact matches
- Low latency
- No API costs for clear cases

**AI disambiguation second** (smart, contextual):
- Only for ambiguous cases
- Analyzes email content deeply
- Provides reasoning for audit trail

### Signal Weighting Rationale

| Signal | Weight | Reasoning |
|--------|--------|-----------|
| Company Name | 40% | Strongest signal (e.g., "Google" in email → likely Google job) |
| Position Title | 30% | Important but less reliable (generic titles like "Engineer") |
| Email Domain | 20% | Strong when matches, but often @greenhouse.io or @lever.co |
| Timeline | 10% | Weak signal, but helps break ties (recent apps more likely) |

### Timeline Window (90 days)

**Why 90 days?**
- Typical application lifecycle: Apply → response in 1-12 weeks
- Balance between recall (catch all relevant jobs) and precision (avoid old jobs)
- Configurable via `TIMELINE_WINDOW_DAYS` in code

## Data Flow

```
Email (EmailModel)
  ↓
EmailClassifier.classify()
  ↓
EmailClassification (category, sentiment, extracted_data)
  ↓
JobMatcher.find_matches()
  ↓
List[JobMatchCandidate] (scored)
  ↓
If ambiguous: JobMatcher.disambiguate_with_ai()
  ↓
Best match + needs_review flag
```

## Configuration

```env
# AI
XAI_API_KEY=xai-...
XAI_MODEL=grok-4-1-fast  # Default

# Matching
AUTO_MATCH_THRESHOLD=0.85
REVIEW_THRESHOLD=0.50
```

## Usage Examples

### Classification
```python
from src.ai.classifier import EmailClassifier
from src.db.models import EmailModel

classifier = EmailClassifier()
email = EmailModel(...)

classification = await classifier.classify(email)
print(f"Category: {classification.category}")
print(f"Sentiment: {classification.sentiment}")
print(f"Confidence: {classification.confidence}")
print(f"Extracted: {classification.extracted_data}")
```

### Job Matching
```python
from src.ai.job_matcher import JobMatcher

matcher = JobMatcher(db_repository)
candidates = await matcher.find_matches(email)

for candidate in candidates:
    print(f"{candidate.company_name}: {candidate.match_score:.2f}")

# With disambiguation
best_match, needs_review = await matcher.match_email_to_job(email)
```

## Testing

See [`tests/test_classifier.py`](../../tests/test_classifier.py) and [`tests/test_matcher.py`](../../tests/test_matcher.py).

**Note**: Tests mock the OpenAI client to avoid API costs during testing.

## Future Enhancements

1. **Fine-tuning**: Train custom model on historical classifications
2. **Multi-model**: Use cheaper models for low-confidence, expensive for high-stakes
3. **Caching**: Cache classifications for similar emails
4. **Active Learning**: Feed manual review corrections back to improve matching
