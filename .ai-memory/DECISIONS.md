# Architecture Decision Records (ADRs)

---

## ADR-001: Use Gemini over Claude for content enrichment

**Date:** 2026-05-18
**Status:** Accepted

**Context:**
The pipeline needs an LLM to enrich RSS news summaries with executive-style analysis in Spanish.
Both Gemini and Claude are viable candidates.

**Decision:**
Use Google Gemini 2.5 Flash via the REST API (not the SDK).

**Rationale:**
- Gemini 2.5 Flash offers a generous free tier suitable for daily runs
- REST API approach avoids SDK version lock-in and is easier to test/mock
- The `generationConfig` parameter allows fine-tuned temperature (0.3) for factual outputs

**Consequences:**
- Requires `GEMINI_API_KEY` secret in GitHub Actions
- HTTP 429 handling implemented with exponential backoff (2s, 4s)
- On enrichment failure, pipeline falls back to raw RSS summaries (graceful degradation)

---

## ADR-002: Public repository

**Date:** 2026-05-18
**Status:** Accepted

**Context:**
The project uses GitHub Actions for scheduling and open-source dependencies.

**Decision:**
The repository is public. No secrets are hardcoded; all credentials are stored as GitHub Actions
secrets and loaded via `.env` locally.

**Rationale:**
- Public repo enables free GitHub Actions minutes
- `.gitignore` excludes `.env` to prevent accidental credential exposure
- `.env.example` documents required variables without exposing values

**Consequences:**
- Anyone can read the source code — no proprietary logic to protect
- `pip-audit` in CI catches known vulnerabilities in dependencies

---

## ADR-003: Stateless pipeline

**Date:** 2026-05-18
**Status:** Accepted

**Context:**
The pipeline runs once per day. No database or persistent storage was specified.

**Decision:**
The pipeline is fully stateless — no database, no cache, no deduplication of articles.

**Rationale:**
- Simplicity: no infrastructure to provision or maintain
- Each run fetches the latest 5 items per level; duplication across days is acceptable
- Reduces attack surface (no credentials for a database)

**Consequences:**
- Repeated items may appear in consecutive newsletters if RSS feeds don't update
- No historical record of sent newsletters (unless stored externally)
- Easy to deploy: just GitHub Actions + environment variables
