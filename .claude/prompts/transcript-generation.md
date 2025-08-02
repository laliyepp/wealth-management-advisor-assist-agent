# Mock Meeting Transcript Generation

Generate a realistic WebVTT format transcript of a financial advisory meeting between a financial advisor and client(s). The transcript should simulate an authentic audio-to-text conversion with natural imperfections.

## Core Requirements

**Format & Structure:**
- WebVTT format with speaker labels: SPEAKER_00, SPEAKER_01, SPEAKER_02, etc.
- Duration: Close to 15 minutes (around 12-20 minutes total)
- Irregular timing intervals (avoid uniform 30-second segments)
- **Sequential timestamps**: Each timestamp must start after the previous one ends (no overlapping time intervals)

**Content Focus:**
- Assume clients & advisors are Canadian Resident
- Primary topics: Investment strategies, tax implications, retirement planning, risk assessment
- Information density: One or two main topic per transcript, discussed in detail
- Include specific numbers, percentages, dollar amounts, and current market situations
- Reference real financial scenarios and concrete examples
- Natural conversation flow with topic transitions

## Realism Guidelines

**Speaker Behavior:**
- Financial advisor should have knowledge gaps and occasionally need to research or follow up
- Include natural hesitations, "um," "uh," "let me think about that"
- Show advisor asking clarifying questions or admitting uncertainty

**Transcript Authenticity:**
- Include common audio-to-text errors (misheard words, homophones)
- Add natural speech patterns: interruptions, incomplete sentences, restarts
- Include small talk, greetings, brief off-topic moments
- Show speech disfluencies and natural pauses
- **Realistic speech timing**: Allow 2-3 words per second on average, with natural pauses between speakers

**Conversation Dynamics:**
- Varying speaker engagement levels
- Natural back-and-forth dialogue
- Realistic pacing with some rushed or slow sections
- Client questions that require thoughtful responses

**Formatting Notes:**
- Use only "SPEAKER_XX" labels in webvtt format (no names or role descriptions)
- Names or roles can exist in dialogue
- No explanatory text outside the transcript
- Maintain conversational, not scripted, tone throughout