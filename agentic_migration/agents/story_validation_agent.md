# Story Validation Agent

> **Agent 1 of Workflow 1: Ingestion & Knowledge Building**

---

## Purpose

Ensure only meaningful, valid Telugu content enters the knowledge base. Acts as the first quality gate, rejecting malformed, empty, or non-Telugu content early to save processing costs.

---

## Why It Exists

| Problem | Solution |
|---------|----------|
| Non-Telugu content submitted | Script filters by Unicode range |
| Empty/too-short content | Script enforces minimum length |
| Meaningless text (random chars) | LLM validates coherence |
| Inappropriate content | LLM filters for children's appropriateness |
| Wasted LLM costs on bad input | Two-step validation reduces calls by 60-80% |

---

## Inputs

```json
{
    "story_text": "string",           // Required: Full story content
    "user_fields": {
        "author": "string | null",    // Optional: Known author
        "source_reference": "string", // Optional: Source info
        "content_type": "STORY | POEM | SERIAL | PUZZLE"
    }
}
```

---

## Outputs

### Success
```json
{
    "status": "valid",
    "validation_step": "llm",
    "validated_story": "Original story text passthrough",
    "user_fields": { /* passthrough */ },
    "validation_metadata": {
        "telugu_ratio": 0.92,
        "char_count": 2500,
        "script_checks_passed": ["unicode", "length", "ratio"]
    }
}
```

### Failure
```json
{
    "status": "invalid",
    "validation_step": "script",  // Where it failed
    "rejection_reason": "Telugu content ratio below 50% (found: 23%)",
    "rejection_code": "INSUFFICIENT_TELUGU"
}
```

---

## Processing Logic

### Step 1: Script-Based Validation (Cheap)

```python
def script_validation(story_text: str) -> ValidationResult:
    """Fast, cheap validation checks. No API calls."""
    
    # Check 1: Telugu Unicode presence
    telugu_chars = re.findall(r'[\u0C00-\u0C7F]', story_text)
    if len(telugu_chars) == 0:
        return fail("NOT_TELUGU", "No Telugu characters found")
    
    # Check 2: Minimum length
    if len(story_text.strip()) < 100:
        return fail("TOO_SHORT", "Story must be at least 100 characters")
    
    # Check 3: Not empty/whitespace
    if not story_text.strip():
        return fail("EMPTY", "Content is empty or whitespace only")
    
    # Check 4: Telugu ratio >= 50%
    total_alpha = len(re.findall(r'\w', story_text))
    telugu_ratio = len(telugu_chars) / max(total_alpha, 1)
    if telugu_ratio < 0.5:
        return fail("LOW_TELUGU_RATIO", f"Telugu ratio {telugu_ratio:.0%} below 50%")
    
    # Check 5: Valid Unicode (no malformed sequences)
    try:
        story_text.encode('utf-8').decode('utf-8')
    except UnicodeError:
        return fail("MALFORMED", "Contains invalid Unicode sequences")
    
    return pass_to_llm(telugu_ratio=telugu_ratio)
```

### Step 2: LLM-Based Validation (Deep)

Only executed if Step 1 passes.

**LLM Prompt:**
```
You are a content validator for a Telugu children's story archive.

Analyze this text and answer these questions:

TEXT:
{story_text}

QUESTIONS (answer YES or NO with brief reason):
1. Is this coherent narrative content (story, poem, article)?
2. Is the content meaningful and complete (not truncated/garbled)?
3. Is it appropriate for children's literature?
4. Would this add value to a story archive?

OUTPUT FORMAT (JSON only):
{
    "is_coherent": true/false,
    "is_meaningful": true/false,
    "is_appropriate": true/false,
    "is_valuable": true/false,
    "overall_valid": true/false,
    "rejection_reason": null or "specific reason"
}
```

---

## Failure Modes

| Failure Mode | Handling | User Impact |
|--------------|----------|-------------|
| Script rejection | Immediate return with reason | Fast feedback |
| LLM timeout | Retry 3x, then reject as "unavailable" | Delayed feedback |
| LLM says invalid | Return with LLM's reason | Quality feedback |
| LLM error | Log, reject as "processing error" | Retry later |

---

## Cost Considerations

| Scenario | LLM Calls | Notes |
|----------|-----------|-------|
| Script rejects | 0 | Majority of bad inputs |
| Script passes, LLM validates | 1 | Good content path |
| Script passes, LLM rejects | 1 | Edge cases |

**Estimated Savings:**
- 60-80% of invalid inputs caught by script
- Each script rejection saves 1 LLM call (~$0.001)
- ROI positive after 1000 rejections

---

## Reusability

| Workflow | Usage |
|----------|-------|
| **WF1: Ingestion** | Primary use case |
| **WF2: Generation** | Not used (prompts don't need validation) |

---

## Mapping to Existing Code

| Function | Existing Code | Status |
|----------|---------------|--------|
| Telugu detection | None | NEW: `src/utils/telugu_utils.py` |
| Unicode validation | None | NEW: Built-in Python |
| LLM call | `src/local_llm_multi.py` | REUSE |

---

## Configuration

```python
# src/agents/validation_agent.py

class ValidationAgentConfig:
    MIN_STORY_LENGTH = 100          # Characters
    TELUGU_RATIO_THRESHOLD = 0.50   # 50%
    LLM_TIMEOUT_SECONDS = 30
    LLM_MAX_RETRIES = 3
    
    # Feature flag
    ENABLED = config.FEATURE_FLAGS.get("use_validation_agent", False)
```

---

## Example Scenarios

### Scenario 1: Pure English Input
```
Input: "Once upon a time, there was a king..."
Step 1: FAIL - No Telugu characters
Output: {"status": "invalid", "rejection_code": "NOT_TELUGU"}
LLM Calls: 0
```

### Scenario 2: Valid Telugu Story
```
Input: "ఒకప్పుడు ఒక రాజ్యంలో..."
Step 1: PASS - 95% Telugu
Step 2: PASS - Coherent narrative
Output: {"status": "valid"}
LLM Calls: 1
```

### Scenario 3: Telugu Gibberish
```
Input: "అఆఇఈ ఉఊఋ ఌఎఏఐ..."
Step 1: PASS - 100% Telugu
Step 2: FAIL - Not coherent/meaningful
Output: {"status": "invalid", "rejection_code": "NOT_COHERENT"}
LLM Calls: 1
```
