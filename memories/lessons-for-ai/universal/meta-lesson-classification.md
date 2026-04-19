# Scan existing folders before placing lessons

**[Rule](#rule)** • **[Process](#process)** • **[Mistake](#mistake)**

## Rule

**Always scan existing subfolders before creating or placing a lesson file.**

Three steps, all required:
1. **Classify**: universal (reusable pattern) vs project-specific (tied to codebase)
2. **Extract check**: if project-specific, can a universal version be stripped out?
3. **Scan**: check existing subfolders for matching category before placement

## Process

```
1. Classify the lesson:
   - Can it transfer to another project? → Universal
   - Does it mention project classes/files? → Project-specific

2. If project-specific, extraction check:
   - Can the core pattern be separated from project details?
   - Strip class names, file paths, configs → generic pattern remains?
   - Yes → create BOTH universal + project-specific versions
   - No → project-specific only

3. Scan existing subfolders:
   ls memories/lessons-for-ai/universal/
   → git/, testing/, messaging/, etc.

4. Place in existing subfolder if one fits
   → Only create new subfolder if none match

5. Project-specific → lessons-for-ai/ root (no subfolder)
```

## Extraction example

**Project-specific lesson:**
"FakeKafkaBroker must match our broker's `publish()` signature"

**Extracted universal (strip project specifics):**
"Test doubles must match real library signatures via `inspect.signature()`"

**Result:** Two files:
- `universal/testing/test-double-contract-validation.md` (generic pattern)
- `lessons-for-ai/fakekafkabroker-implementation.md` (our specifics)

Not always possible, but always worth checking.

## Classification quick test

| Question | Yes → | No → |
|----------|-------|------|
| Transfers to different project? | Universal | Project-specific |
| Mentions project classes/files? | Project-specific | Universal |
| Reusable pattern/algorithm? | Universal | Project-specific |

## Existing subfolders (scan these first)

Known categories under `universal/`:
- `git/` - commits, hooks, workflows
- `testing/` - mocking, fixtures, isolation, containers
- `messaging/` - Kafka, RabbitMQ, FastStream, brokers

**Check for new ones** - other agents may have created additional folders.

## Mistake that prompted this lesson

AI created a lesson about commit scope prioritization at:
`memories/lessons-for-ai/prioritize-user-intent-in-commits.md` (root)

**Problem:** This is a universal git pattern, not project-specific.

**Correct location:**
`memories/lessons-for-ai/universal/git/prioritize-user-intent-in-commits.md`

**Root cause:** Skipped classification step entirely. Defaulted to root
without checking if `universal/git/` already existed and was appropriate.

## Why scanning matters

Without scanning:
- Duplicate folders get created (`git-lessons/` vs existing `git/`)
- Universal lessons buried at project-specific root
- No awareness of existing categories

Scanning takes seconds. Wrong placement causes confusion across sessions.
