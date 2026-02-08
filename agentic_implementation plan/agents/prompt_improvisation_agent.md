# Prompt Improvisation & Telugu Optimization Agent

> **Agent 1 of Workflow 2: Story Generation**

---

## Purpose

Transform user prompts (in any language) into optimized Telugu prompts ready for RAG-based story generation. Expands vague requests while strictly preserving user intent.

---

## Why It Exists

| Problem | Solution |
|---------|----------|
| Users may not speak Telugu | Translate to Telugu |
| Vague prompts give poor results | Intelligent expansion |
| RAG works better with rich queries | Query optimization |
| User intent may be lost | Strict preservation |
| Inconsistent prompt quality | Standardized output |

---

## Inputs

```json
{
    "user_prompt": "string",           // Any language
    "language_detected": "string",     // Auto-detected or user-specified
    "facets": {
        "genre": "string | null",
        "keywords": ["array"],
        "characters": ["array"],
        "locations": ["array"],
        "tone": "traditional | modern | mythological"
    }
}
```

---

## Outputs

```json
{
    "original_prompt": "Write a story about a clever farmer",
    "original_language": "English",
    "telugu_prompt": "తెలివైన రైతు కథ. ఒక పేద రైతు తన బుద్ధి చాతుర్యంతో దుష్ట జమీందారును ఓడించి గ్రామాన్ని రక్షిస్తాడు.",
    "expansion_applied": true,
    "facets_integrated": ["రైతు", "తెలివి", "న్యాయం"],
    "intent_preserved": true,
    "confidence": 0.95
}
```

---

## Processing Logic (LLM Required)

### Main LLM Prompt

```
You are a Telugu story prompt optimizer for the Chandamama children's magazine archive.

USER INPUT: {user_prompt}
INPUT LANGUAGE: {language_detected}
SELECTED FACETS: 
- Genre: {genre or "Not specified"}
- Keywords: {keywords or "None"}
- Characters: {characters or "None"}
- Locations: {locations or "None"}
- Tone: {tone or "Traditional"}

YOUR TASKS:

1. **TRANSLATE** (if not Telugu):
   - Convert to natural, fluent Telugu
   - Preserve exact meaning
   - Use vocabulary appropriate for children's literature

2. **EXPAND** (if vague):
   - Add narrative elements consistent with the request
   - Suggest plot direction without changing user's idea
   - Make it suitable for semantic search
   
3. **PRESERVE INTENT** (CRITICAL):
   - The user's core request MUST remain unchanged
   - Do NOT add unrelated themes
   - Do NOT change the fundamental story idea
   
4. **INTEGRATE FACETS**:
   - Naturally incorporate any provided facets
   - Don't force-fit if they conflict with prompt

EXAMPLES:

Input: "a funny story"
Output: "హాస్యం నిండిన కథ. తమాషా సంఘటనలు, నవ్వు పుట్టించే పాత్రలు, సరదా ముగింపుతో ఒక సంతోషకరమైన కథ."

Input: "राजा की कहानी" (Hindi)
Output: "రాజు కథ. ఒక గొప్ప రాజు తన రాజ్యాన్ని, ప్రజలను కాపాడే ధైర్య సాహసాల కథ."

Input: "Write about అడవి జంతువులు"
Output: "అడవి జంతువుల కథ. అడవిలో నివసించే జంతువుల స్నేహం, సాహసాలు, వాటి జీవన విధానం గురించిన ఆసక్తికరమైన కథ."

OUTPUT FORMAT:
Return ONLY the optimized Telugu prompt. No explanations.
```

### Post-Processing

```python
def post_process(llm_output: str, original_prompt: str) -> dict:
    """Validate and structure the output."""
    
    # Ensure Telugu content
    telugu_ratio = count_telugu_chars(llm_output) / len(llm_output)
    if telugu_ratio < 0.5:
        raise ValueError("Output not sufficiently Telugu")
    
    # Extract keywords for facet integration tracking
    facets_integrated = extract_keywords(llm_output)
    
    return {
        "original_prompt": original_prompt,
        "telugu_prompt": llm_output.strip(),
        "expansion_applied": len(llm_output) > len(original_prompt) * 1.5,
        "facets_integrated": facets_integrated,
        "intent_preserved": True  # Assumed if no errors
    }
```

---

## Failure Modes

| Failure Mode | Handling | User Impact |
|--------------|----------|-------------|
| LLM timeout | Retry 2x, then use original | Degraded quality |
| Intent drift detected | Flag for user confirmation | Interactive |
| Unsupported language | Fallback to English prompt | Degraded quality |
| Telugu check fails | Retry with stronger prompt | Retry delay |

---

## Cost Considerations

| Scenario | LLM Calls | Notes |
|----------|-----------|-------|
| Any prompt | 1 | Always required |
| LLM retry | +1 | On failure |

**Optimization Notes:**
- Single call handles translation + expansion
- Caching possible for common prompts (future)
- Short prompts = lower token cost

---

## Reusability

| Workflow | Usage |
|----------|-------|
| **WF1: Ingestion** | Not used |
| **WF2: Generation** | Primary use case |

---

## Mapping to Existing Code

| Function | Existing Code | Status |
|----------|---------------|--------|
| LLM call | `src/local_llm_multi.py` | REUSE |
| Telugu detection | None | NEW: `src/utils/telugu_utils.py` |
| Language detection | None | NEW: Use langdetect library |

---

## Configuration

```python
# src/agents/prompt_agent.py

class PromptAgentConfig:
    LLM_TIMEOUT_SECONDS = 30
    MAX_RETRIES = 2
    MIN_TELUGU_RATIO = 0.5
    MAX_EXPANSION_RATIO = 3.0  # Don't expand more than 3x
    
    SUPPORTED_LANGUAGES = [
        "te", "en", "hi", "ta", "kn", "ml"  # Telugu, English, Hindi, Tamil, Kannada, Malayalam
    ]
    
    # Feature flag
    ENABLED = config.FEATURE_FLAGS.get("use_prompt_improvisation", False)
```

---

## Example Scenarios

### Scenario 1: English → Telugu
```
Input:
  user_prompt: "A story about a brave girl"
  language: "English"
  facets: {genre: "Adventure"}

Processing:
  → Translate + Expand
  → Integrate genre

Output:
  telugu_prompt: "ధైర్యశాలి అమ్మాయి సాహస కథ. ఒక చిన్న అమ్మాయి తన ధైర్యంతో అడవిలో తప్పిపోయిన తన తమ్ముడిని వెతికి రక్షిస్తుంది."
  expansion_applied: true

LLM Calls: 1
```

### Scenario 2: Already Telugu
```
Input:
  user_prompt: "తెనాలి రామకృష్ణుడి తెలివి కథ"
  language: "Telugu"
  facets: {keywords: ["తెలివి", "హాస్యం"]}

Processing:
  → Minor expansion only
  → Integrate keywords

Output:
  telugu_prompt: "తెనాలి రామకృష్ణుడి తెలివి కథ. రాజు సభలో ఒక క్లిష్టమైన సమస్యను రామకృష్ణుడు తన హాస్య చతురతతో పరిష్కరించే సరదా కథ."
  expansion_applied: true

LLM Calls: 1
```

### Scenario 3: Vague Prompt
```
Input:
  user_prompt: "nice story"
  language: "English"
  facets: {}

Processing:
  → Heavy expansion needed
  → Maintain generic but rich

Output:
  telugu_prompt: "మంచి కథ చెప్పు. నీతి, ధర్మం, స్నేహం వంటి విలువలతో, పిల్లలకు నచ్చే పాత్రలతో, సంతోషకరమైన ముగింపుతో ఒక హృద్యమైన కథ."
  expansion_applied: true

LLM Calls: 1
```

---

## Intent Preservation Rules

> [!CAUTION]
> **These rules are CRITICAL for user satisfaction:**

1. **Never change the subject**
   - "king story" must remain about a king
   - "animal story" must remain about animals

2. **Never add conflicting themes**
   - "happy story" should not become sad
   - "simple story" should not become complex

3. **Never impose specific plots**
   - "adventure story" → OK to say "brave hero"
   - "adventure story" → NOT OK to specify exact events

4. **Preserve cultural context**
   - "Indian festival story" must stay culturally accurate
   - Regional specifics must be maintained
