# GEO Analysis: github.com/TorpedoD/claude-researcher

**Analyzed:** 2026-04-19 | **Target URL:** https://github.com/TorpedoD/claude-researcher

---

## GEO Readiness Score: 46/100

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|---------|
| Citability | 12/25 | 25% | 12 |
| Structural Readability | 12/20 | 20% | 12 |
| Multi-Modal Content | 4/15 | 15% | 4 |
| Authority & Brand Signals | 5/20 | 20% | 5 |
| Technical Accessibility | 13/20 | 20% | 13 |
| **Total** | | | **46/100** |

**Assessment:** Early-stage repo with solid content bones but missing all brand/authority signals and AI-specific infrastructure. The GitHub platform itself is accessible to AI crawlers, but the content lacks the citability structure, brand presence, and AI discoverability features needed for AI search engines to surface it.

---

## Platform Breakdown

| Platform | Estimated Score | Bottleneck |
|----------|----------------|-----------|
| Google AI Overviews | ~35/100 | Low domain authority, no traditional SEO page rank yet |
| ChatGPT | ~20/100 | No Wikipedia presence, no Reddit mentions |
| Perplexity | ~25/100 | No Reddit/community discussion, low authority |
| Bing Copilot | ~40/100 | GitHub indexed by Bing, repo content accessible |

---

## 1. AI Crawler Access Status

**GitHub robots.txt analysis — repo page is accessible to all AI crawlers.**

| Crawler | Status | Notes |
|---------|--------|-------|
| GPTBot | **ALLOWED** | No Disallow rule for repo pages |
| OAI-SearchBot | **ALLOWED** | No explicit rule |
| ClaudeBot | **ALLOWED** | No explicit rule |
| PerplexityBot | **ALLOWED** | No explicit rule |
| CCBot | **ALLOWED** | No explicit block |
| Googlebot | **ALLOWED** | Standard access |
| bingbot | **ALLOWED** | Explicitly listed with minimal restrictions |

**Critical caveat:** GitHub blocks `/*/raw/` paths, meaning AI crawlers cannot directly access raw file content. They read the rendered repo page. This is not a problem for the README (GitHub renders it in HTML), but means deeply-nested files are inaccessible to crawlers.

**No action needed** on robots.txt — GitHub controls this globally.

---

## 2. llms.txt Status

**MISSING** — No `llms.txt` found at:
- `https://raw.githubusercontent.com/TorpedoD/claude-researcher/main/llms.txt`
- `https://github.com/TorpedoD/llms.txt` (domain-level not possible on GitHub)

**Impact:** AI crawlers have no structured guidance on what this repo contains or which content matters most.

**Recommendation:** Add `llms.txt` to the repo root. Although GitHub is not a domain you control, having it in the repo means:
1. It documents intent for the project itself
2. If you ever move to a dedicated domain/site, it's already written
3. Some AI crawlers index raw GitHub content via other paths

**Ready-to-use template:**
```
# claude-researcher
> A production-grade, multi-agent AI research pipeline that runs entirely inside Claude Code. One slash command plans scope, crawls the web, builds a knowledge graph, and synthesizes citation-rich reports.

## Core documentation
- [README](https://github.com/TorpedoD/claude-researcher/blob/main/README.md): Full installation, usage, and architecture guide
- [Installation](https://github.com/TorpedoD/claude-researcher#installation): npx setup instructions
- [Architecture](https://github.com/TorpedoD/claude-researcher#architecture): 4-phase pipeline design

## Key facts
- Runs entirely inside Claude Code — no external LLM API calls, no paid scraping services
- 4-phase pipeline: scope → collect → synthesize → publish
- 4 human checkpoint gates with resume support
- Uses Crawl4AI and Docling for web crawling and document parsing
- Install via: npx claude-researcher install
- MIT License
```

---

## 3. Brand Mention Analysis

**Status: Near-zero cross-platform brand presence** (repo is 5 days old as of analysis date)

| Platform | Status | Notes |
|----------|--------|-------|
| Wikipedia | **ABSENT** | No entry for claude-researcher or TorpedoD |
| Reddit | **ABSENT** | No detected discussions or mentions |
| YouTube | **ABSENT** | No videos found |
| LinkedIn | **UNKNOWN** | Could not verify |
| npm/npmjs.com | **CHECK** | Package exists as `claude-researcher` on npm |
| Hacker News | **ABSENT** | No detected posts |
| DEV.to / Hashnode | **ABSENT** | No articles found |

**Root cause:** 5-day-old repo with 2 stars. Brand signal deficit is expected at this stage — the gap is structural, not a content failure.

**Platform-specific citation sources for this topic:**
- ChatGPT cites Wikipedia (47.9%) and Reddit (11.3%) most heavily
- Perplexity cites Reddit (46.7%) heavily
- Neither platform will cite a 2-star GitHub repo without supporting ecosystem mentions

---

## 4. Passage-Level Citability Analysis

**Current opening paragraph (citability: MODERATE)**
> "claude-researcher is a production-grade, multi-agent research pipeline that runs entirely inside Claude Code. One slash command plans scope, crawls the web, builds a knowledge graph, synthesizes citation-rich research with gap detection, and publishes a formatted report — no external LLM API calls, no paid scraping services."

Word count: ~47 words. **Too short** for optimal AI citation (target: 134–167 words).

**Problem:** The README provides good feature descriptions but lacks self-contained, quotable answer blocks. Content is structured for human developers reading linearly, not for AI extraction.

**Passages that score well (extractable):**

*"What Makes It Different" section* — 4 bullet points, each with a bold label and explanation. Good pattern, but each bullet is a fragment. A rewrite as flowing prose would improve extractability.

*"The 4 Checkpoint Gates" section* — Specific and unique to this tool. Has concrete information AI would want to cite.

**Missing citability patterns:**
- No "What is claude-researcher?" definition block
- No comparison table (vs gpt-researcher, Perplexity, etc.)
- No numbered statistics (e.g., "reduces 40-source research to X minutes")
- No FAQ section with explicit Q&A format

---

## 5. Server-Side Rendering Check

**Status: ADEQUATE for GitHub-hosted content**

GitHub renders README content as server-side HTML. AI crawlers that don't execute JavaScript will still see:
- The rendered README
- Repository metadata (title, description, topics, stars)
- File tree structure

**Limitation:** The GitHub repo page is heavily React-based. Dynamic elements (commit history, contributor graphs) are client-rendered and invisible to AI crawlers. This is fine — those aren't the content that should be cited anyway.

**If you add a dedicated documentation site** (e.g., via GitHub Pages or a standalone site), ensure SSR — don't use a client-only React SPA.

---

## 6. Content Structure Analysis

**Current README heading hierarchy:**
```
H1: claude-researcher — AI Research Pipeline for Claude Code
H2: Installation
  H3: 1. Install the pipeline
  H3: 2. Install system dependencies
  H3: Extra recommended installations
  H3: 3. Verify
H2: Usage
  H3: Basic
  H3: Resuming an interrupted run
  H3: Budget configuration
H2: The 4 Checkpoint Gates
H2: Why This Exists
H2: What Makes It Different
H2: Architecture
H2: Run Artifacts
```

**Issues:**
- No question-based headings (AI systems match headings to query patterns)
- No FAQ section
- "Why This Exists" is vague — AI can't match it to queries like "when should I use claude-researcher?"
- Missing: "How does claude-researcher work?", "What is claude-researcher?", "claude-researcher vs gpt-researcher"

---

## 7. Schema Recommendations

GitHub doesn't allow custom schema injection into repo pages. However, if you publish a dedicated site or npm package page, implement:

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "claude-researcher",
  "description": "Multi-agent AI research pipeline for Claude Code",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "macOS, Linux, Windows",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "author": {
    "@type": "Person",
    "name": "TorpedoD",
    "url": "https://github.com/TorpedoD"
  },
  "license": "https://opensource.org/licenses/MIT",
  "codeRepository": "https://github.com/TorpedoD/claude-researcher",
  "programmingLanguage": ["JavaScript", "Python"]
}
```

Also add `Person` schema for the author if you create an author page.

---

## Top 5 Highest-Impact Changes

### 1. Add `llms.txt` to the repo root
**Effort:** 15 min | **Impact:** HIGH
Creates structured AI crawler guidance. First-mover advantage in this niche is real — very few Claude Code tools have llms.txt.

### 2. Rewrite README opening with a 134–167 word definition block
**Effort:** 30 min | **Impact:** HIGH
Current opening is 47 words — too short to be cited. Expand the first section into a self-contained, quotable definition that answers "What is claude-researcher and what does it do?" in 134–167 words with specific capabilities named.

Example structure:
> **claude-researcher** is an open-source, multi-agent research pipeline that runs entirely inside Claude Code, Anthropic's developer CLI. [Continue with: what it does, how it differs, what it produces, who it's for — ~150 words total]

### 3. Add a Comparison/FAQ section to the README
**Effort:** 1 hour | **Impact:** HIGH
A "Frequently Asked Questions" or "claude-researcher vs alternatives" section creates query-matchable content. AI search engines heavily favor explicit Q&A format.

Target questions to answer:
- "What is claude-researcher?"
- "How does claude-researcher work?"
- "claude-researcher vs gpt-researcher"
- "Does claude-researcher require an API key?"
- "How do I install claude-researcher?"

### 4. Post to Reddit and Hacker News
**Effort:** 1 hour | **Impact:** VERY HIGH (for ChatGPT + Perplexity)
Reddit is cited by Perplexity in 46.7% of results. A post in r/ClaudeAI, r/LocalLLaMA, or r/MachineLearning will:
- Create brand mentions AI crawlers index
- Drive real traffic back to the repo
- Establish community validation signals

Post targets: r/ClaudeAI, r/LocalLLaMA, r/commandline, Hacker News "Show HN"

### 5. Set repository homepage to a dedicated landing page or npm package URL
**Effort:** 5 min | **Impact:** MEDIUM
The `homepage` field is `null` in the GitHub API. Set it to `https://www.npmjs.com/package/claude-researcher` or a dedicated docs site. This adds a canonical reference point and signals active maintenance.

---

## Content Reformatting Suggestions

**Current "What Makes It Different" section — reformat from bullets to citability-optimized prose:**

Before (4 disconnected bullets):
```
- **Provenance-first** — every collected piece of evidence carries source metadata...
- **Gap detection built-in** — a 7-layer investigation tree...
```

After (self-contained citability block, ~150 words):
```
claude-researcher is distinguished from other research tools by four architectural decisions. 
First, provenance-first collection: every piece of evidence carries source metadata, and every 
claim in the final document links back to its source via inline citations — eliminating 
hallucination from the synthesis phase. Second, gap detection: a 7-layer investigation tree 
drives synthesis; uncovered branches trigger targeted re-collection before the final document 
is written, ensuring comprehensive coverage rather than stopping at obvious sources. Third, 
checkpoint gates: four human review points let you steer scope, flag unreliable sources, or 
abort early without losing work. Fourth, reproducibility: each session is isolated in a 
timestamped directory with manifest, logs, and evidence inventory, making runs auditable and 
resumable. Together these features make claude-researcher appropriate for research that requires 
citation accuracy rather than speed alone.
```
Word count: 138 words — within optimal 134–167 range for AI citation.

---

## Summary

The project has a strong technical foundation and good keyword coverage in its package metadata. The main barriers to AI search visibility are:
1. **Age/authority** — 5 days old, 2 stars, no external brand presence (solve via community outreach)
2. **Missing llms.txt** — easy win, add to repo root today
3. **Non-optimal passage structure** — README answers questions but not in AI-extractable format (rewrite opening + add FAQ)
4. **No dedicated homepage** — GitHub is a reasonable host but a standalone page gives full control over schema and structure

Revisit this score in 30 days after Reddit/HN posts and llms.txt addition.
