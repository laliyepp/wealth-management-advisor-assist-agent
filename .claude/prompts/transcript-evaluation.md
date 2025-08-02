# Transcript Quality Control

## Task
Transform all transcripts in `data/transcript/` to meet generation standards.

## Process: 2 Cycles Per File

### Phase 1: Content Enhancement (Ignore timing related issue in this phase)
1. **Read** entire transcript
2. **Evaluate** against `.claude/prompts/transcript-generation.md` standards
3. **Fix** all content issues:
   - Add natural speech patterns (um, uh, restarts, interruptions)
   - Reduce natural speech patterns if too much
   - Insert advisor uncertainty and knowledge gaps
   - Reduce advisor uncertainty and knowledge gaps if too much
   - Include audio-to-text errors (homophones, mishearings)
   - Reduce audio-to-text errors (homophones, mishearings) if too much and does not make sense
4. **Verify** all content meets standards before proceeding

### Phase 2: Timing Correction
5. **Check** speech pacing using tool under `.claude/tools/webvtt_pacing_analyzer.py`
6. **Fix** any segments that are too fast or too slow (must be 2-3 words/second) using '.claude/tools/fix_speech_pacing.py'
7. **Run** `.claude/tools/check_overlaps.py` to find timestamp overlaps
8. **Fix** overlaps using `.claude/tools/fix_timestamps.py` or manual adjustment
   - Re-run tool after each fix to catch cascading overlaps
9. **Confirm** no overlaps remain
10. **Repeat** entire phase 2 to make sure **all** timing issues addressed.

### Repeat
Complete both phases twice per transcript file.

## Success Criteria
- Natural, realistic conversation flow
- All timestamps sequential (no overlaps)
- Proper speech pacing throughout
- Full compliance with generation standards
- Transcript maintains concise, meaningful dialogue