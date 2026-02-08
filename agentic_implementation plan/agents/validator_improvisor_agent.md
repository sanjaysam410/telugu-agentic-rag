# Validator & Improvisor Agent

> **Agent 4 of Workflow 2: Story Generation**

---

## Purpose

Quality gate ensuring only high-quality Telugu stories reach users. Evaluates generated stories, provides structured feedback for regeneration, and performs grammar polishing on approved stories.

---

## Why It Exists

| Problem | Solution |
|---------|----------|
| LLM outputs vary in quality | Structured evaluation |
| No feedback for improvement | Specific regeneration guidance |
| Grammar/spelling errors | Final polish pass |
| User gets bad stories | Quality threshold gating |
| No quality metrics | Trackable scores |

---

## Inputs

```json
{
    "draft_story": "Title: వినయశీలుడు\n\nఒకప్పుడు...",
    "original_prompt": "రాజు వినయం నేర్చుకున్న కథ",
    "expected_elements": {
        "genre": "MORAL_STORY",
        "keywords": ["రాజు", "వినయం"],
        "tone": "traditional"
    },
    "attempt_number": 1,
    "max_attempts": 3
}
```

---

## Outputs

### Pass
```json
{
    "status": "success",
    "final_story": "Title: వినయశీలుడు\n\n[Polished story...]",
    "quality_score": 7.5,
    "evaluation": {
        "coherence": 8,
        "telugu_quality": 7,
        "prompt_adherence": 8,
        "engagement": 7,
        "cultural_authenticity": 8
    },
    "attempts": 1,
    "polish_applied": true
}
```

### Fail (Retry)
```json
{
    "status": "retry",
    "attempt_number": 2,
    "quality_score": 4.5,
    "feedback": {
        "issues": [
            "Ending feels rushed",
            "Moral not clearly stated",
            "Character motivation unclear"
        ],
        "specific_fixes": [
            "Expand the resolution scene to at least 3 paragraphs",
            "Add explicit moral statement at end",
            "Show why the king changes his mind"
        ]
    }
}
```

### Max Retries Exhausted
```json
{
    "status": "success_with_warning",
    "final_story": "[Best attempt from all tries]",
    "quality_score": 5.2,
    "warning": "Story may not fully meet quality standards",
    "attempts": 3,
    "best_attempt_number": 2
}
```

---

## Processing Logic

### Step 1: Quality Evaluation (LLM)

**Evaluation Prompt:**
```
You are a Telugu story quality evaluator for a children's magazine.

STORY TO EVALUATE:
{draft_story}

ORIGINAL USER REQUEST:
{original_prompt}

EXPECTED ELEMENTS:
- Genre: {genre}
- Keywords: {keywords}
- Tone: {tone}

EVALUATION CRITERIA (score 1-10 each):

1. COHERENCE
   - Does the plot make logical sense?
   - Are there plot holes or contradictions?
   - Is the ending earned by the story?

2. TELUGU QUALITY
   - Is the Telugu natural and fluent?
   - Are there English words mixed in?
   - Is vocabulary appropriate for children?

3. PROMPT ADHERENCE
   - Does it match what the user asked for?
   - Are expected keywords/themes present?
   - Is the genre correct?

4. ENGAGEMENT
   - Is it interesting to read?
   - Would children enjoy this?
   - Is the pacing good?

5. CULTURAL AUTHENTICITY
   - Does it feel like a Chandamama story?
   - Are cultural elements accurate?
   - Does it fit traditional storytelling patterns?

OUTPUT FORMAT (JSON only):
{
    "scores": {
        "coherence": X,
        "telugu_quality": X,
        "prompt_adherence": X,
        "engagement": X,
        "cultural_authenticity": X
    },
    "overall_score": X,
    "issues": ["Specific issue 1", "Specific issue 2"],
    "specific_fixes": ["Exact fix 1", "Exact fix 2"]
}
```

### Step 2: Decision Logic

```python
def evaluate_and_decide(evaluation: dict, attempt: int, max_attempts: int) -> dict:
    """Decide: pass, retry, or return best effort."""
    
    overall_score = evaluation["overall_score"]
    
    if overall_score >= PASS_THRESHOLD:  # 6.0
        # PASS - proceed to polish
        return {"action": "polish", "evaluation": evaluation}
    
    elif attempt < max_attempts:
        # RETRY - generate feedback
        return {
            "action": "retry",
            "feedback": {
                "issues": evaluation["issues"],
                "specific_fixes": evaluation["specific_fixes"]
            }
        }
    
    else:
        # MAX RETRIES - return best attempt
        return {
            "action": "best_effort",
            "warning": "Story may not fully meet quality standards"
        }
```

### Step 3: Grammar Polish (LLM, Conditional)

Only executed if story passes threshold.

**Polish Prompt:**
```
You are a Telugu grammar and style editor.

STORY:
{draft_story}

TASK:
1. Fix any grammatical errors
2. Improve sentence flow
3. Correct spelling mistakes
4. DO NOT change the story content, plot, or meaning
5. Keep the same title
6. Return the full polished story

OUTPUT: The complete polished story (no explanations)
```

---

## Quality Thresholds

| Score Range | Action | Notes |
|-------------|--------|-------|
| 8-10 | Pass immediately | High quality |
| 6-7.9 | Pass with polish | Good enough |
| 4-5.9 | Retry | Fixable issues |
| 0-3.9 | Retry | Significant problems |

**Threshold Configuration:**
```python
PASS_THRESHOLD = 6.0
NEEDS_POLISH_THRESHOLD = 8.0  # Above this, skip polish
```

---

## Failure Modes

| Failure Mode | Handling | User Impact |
|--------------|----------|-------------|
| Evaluation timeout | Skip validation, return draft | Warning shown |
| Polish timeout | Return unpolished | Minor quality loss |
| All retries fail | Return best attempt | Warning shown |
| Invalid JSON from LLM | Retry evaluation | Delay |

---

## Cost Considerations

| Scenario | LLM Calls | Notes |
|----------|-----------|-------|
| Pass on first try | 2 | Evaluate + Polish |
| Fail, retry once | 4 | 2 evaluations + 1 polish |
| All 3 tries | 6 | 3 evaluations (polish on best) |

---

## Best Attempt Tracking

```python
class BestAttemptTracker:
    """Track best story across regeneration attempts."""
    
    def __init__(self):
        self.best_score = 0
        self.best_story = None
        self.best_attempt = 0
    
    def update(self, story: str, score: float, attempt: int):
        if score > self.best_score:
            self.best_score = score
            self.best_story = story
            self.best_attempt = attempt
    
    def get_best(self) -> dict:
        return {
            "story": self.best_story,
            "score": self.best_score,
            "attempt": self.best_attempt
        }
```

---

## Reusability

| Workflow | Usage |
|----------|-------|
| **WF1: Ingestion** | Not used (stories already validated) |
| **WF2: Generation** | Primary use case |

---

## Mapping to Existing Code

| Function | Existing Code | Status |
|----------|---------------|--------|
| LLM call | `src/local_llm_multi.py` | REUSE |
| Streaming | N/A (evaluation is non-streaming) | N/A |

---

## Configuration

```python
# src/agents/validator_agent.py

class ValidatorAgentConfig:
    PASS_THRESHOLD = 6.0
    NEEDS_POLISH_THRESHOLD = 8.0
    MAX_RETRIES = 3
    
    EVALUATION_TIMEOUT_SECONDS = 45
    POLISH_TIMEOUT_SECONDS = 30
    
    # Feature flag
    ENABLED = config.FEATURE_FLAGS.get("use_story_validation", False)
```

---

## Example Scenarios

### Scenario 1: High Quality Pass
```
Input: Well-crafted story, score 8.5

Evaluation:
  coherence: 9, telugu_quality: 8, prompt_adherence: 8
  engagement: 8, cultural_authenticity: 9
  overall: 8.4

Decision: Pass (skip polish - above 8.0)

Output: {"status": "success", "quality_score": 8.4}
LLM Calls: 1 (evaluation only)
```

### Scenario 2: Good Story Needs Polish
```
Input: Good story with minor grammar issues, score 6.5

Evaluation:
  coherence: 7, telugu_quality: 6, prompt_adherence: 7
  engagement: 6, cultural_authenticity: 7
  overall: 6.6

Decision: Pass with polish

Polish: Fix grammar, return polished story

Output: {"status": "success", "quality_score": 6.6, "polish_applied": true}
LLM Calls: 2 (evaluation + polish)
```

### Scenario 3: Needs Regeneration
```
Input: Story with plot holes, score 4.2

Evaluation:
  coherence: 3, telugu_quality: 6, prompt_adherence: 4
  engagement: 4, cultural_authenticity: 5
  overall: 4.4
  issues: ["Plot holes in middle", "Abrupt ending"]
  fixes: ["Connect scene 2 to scene 3", "Add resolution"]

Decision: Retry (attempt 1 of 3)

Output: {"status": "retry", "feedback": {...}}
LLM Calls: 1 (evaluation only)
```
