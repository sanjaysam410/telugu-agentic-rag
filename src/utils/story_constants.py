
# GENRE-SPECIFIC ADDITIONS (conditionally added based on genre)
GENRE_ADDITIONS = {
    "moral_story": """
==================================================
MORAL STORY GUIDELINES
==================================================
- Build toward a clear life lesson
- Let moral emerge from character actions
- State moral explicitly at end in ONE sentence
- Avoid preaching within the story
- Traditional folktale rhythm and pacing
""",

    "children_story": """
==================================================
CHILDREN'S STORY GUIDELINES
==================================================
- Simple vocabulary, rich imagery
- Clear good/bad distinction (if applicable)
- Age-appropriate themes and content
- Engaging rhythm that holds attention
- Optional: Include playful elements
""",

    "romance": """
==================================================
ROMANCE GUIDELINES
==================================================
- Focus on emotional connection and chemistry
- Build tension through obstacles/misunderstandings
- Show relationship development naturally
- Age-appropriate intimacy level
- Satisfying emotional payoff
""",

    "mystery": """
==================================================
MYSTERY GUIDELINES
==================================================
- Plant clues fairly for reader
- Build suspense through pacing
- Red herrings should be logical
- Solution must be earned, not random
- Reveal should satisfy setup
""",

    "comedy": """
==================================================
COMEDY GUIDELINES
==================================================
- Humor through character, situation, or wordplay
- Build comic timing through pacing
- Exaggeration should feel natural to story
- Avoid offensive stereotypes
- Land the punchlines/comic moments
""",

    "thriller": """
==================================================
THRILLER GUIDELINES
==================================================
- Maintain tension throughout
- Stakes must be clear and escalating
- Quick pacing with strategic slower moments
- Twist/surprises must be logical in hindsight
- Strong sense of danger/urgency
"""
}

# TONE-SPECIFIC ADDITIONS
TONE_ADDITIONS = {
    "traditional": "Use classic Telugu storytelling rhythm. Prefer timeless themes and archetypal characters.",
    "modern": "Contemporary language and settings. Modern social dynamics and realistic dialogue.",
    "mythological": "Maintain reverence for traditional stories. Epic scale and timeless themes.",
    "realistic": "Grounded in everyday life. Authentic character psychology and plausible events.",
    "fantastical": "Establish clear rules for magical elements. Internal consistency in fantasy logic."
}

# KEYWORD INTEGRATION LOGIC (SHARED)
KEYWORD_INTEGRATION_LOGIC = """
==================================================
KEYWORD INTEGRATION (CRITICAL WARNING)
==================================================
**DO NOT MECHANICALLY INCLUDE ALL KEYWORDS.**

Your task is to create a COHERENT story, not a checklist.

**IF YOU HAVE MULTIPLE KEYWORDS/CHARACTERS/SETTINGS:**

OPTION 1: Choose the 2-3 that fit together naturally
- Ignore keywords that don't serve the story
- It's better to skip a keyword than force it

OPTION 2: Find ONE unifying concept that connects them
- Ask: "What single story could naturally include these?"
- If you can't find one, go back to Option 1

**EXAMPLE - BAD APPROACH:**
Keywords: మోసం, సాహసం, శాపం
Characters: రాజు, మంత్రి, రైతు
Result: Throws all into one story → overstuffed, incoherent

**EXAMPLE - GOOD APPROACH:**
Keywords: మోసం, సాహసం, శాపం
Choose: సాహసం + శాపం (adventure + curse work together)
Skip: మోసం (doesn't fit naturally)
Or: మోసం causes శాపం, requires సాహసం to fix (connected)

**CHARACTERS:**
- If given 3+ characters, ask: "Does each have a CLEAR role?"
- If a character has no purpose, DON'T include them
- Better to have 2 well-developed characters than 4 doing nothing

**SETTINGS:**
- Don't visit all locations just because they're listed
- Only include settings that serve the plot
- Each location should have a PURPOSE in the story

**THE GOLDEN RULE:**
Story coherence > keyword inclusion
A simple story using 60% of keywords well
is MUCH BETTER than
a confused story forcing 100% of keywords badly
"""

# ANTI-REPETITION & HALLUCINATION RULES (SHARED)
ANTI_REPETITION_RULES = """
==================================================
STRICT WRITING RULES (ANTI-REPETITION)
==================================================
1. **NO REPETITIVE TAGS:**
   - STRICTLY AVOID repetitive dialogue tags like "అని అన్నది" (she said), "అని చెప్పాడు" (he said), "అని అడిగాడు" (he asked).
   - Use action beats instead.
     *Bad:* "వస్తావా?" అని అన్నాడు రాము.
     *Good:* రాము తల తిప్పి చూశాడు. "వస్తావా?"

2. **SENTENCE VARIETY:**
   - Do NOT start every sentence with a subject or name.
   - Vary sentence length. Mix short, punchy sentences with longer, flowing descriptions.

3. **NO ENGLISH WORDS:**
   - STRICT PROHIBITION: Do NOT use any English words. Use pure Telugu vocabulary.
   - Example: Instead of "Time ayindi", use "సమయం అయ్యింది".

4. **NO HALLUCINATIONS:**
   - Do not invent non-existent cultural details unless it's fantasy.
   - Keep character actions logically consistent.
"""
