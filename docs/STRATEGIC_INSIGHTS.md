# Strategic Insight Report — EV Brand GEO Visibility (1-page)

## Objective
Quantify how leading LLMs recommend EV brands and translate model behavior into practical GEO strategy.

Models analyzed:
- GPT-4o-mini
- Claude 3 Haiku (`claude-3-haiku-20240307`)

Dataset:
- 100 high-intent EV purchase prompts
- 200 raw model responses (100 prompts × 2 models)
- 200 structured judge evaluations

---

## Executive Summary

1. **Tesla dominates recommendation share overall**, especially in GPT-4o-mini outputs.
2. **Claude shows a more diversified recommendation mix** (higher Rivian + “Other” share than GPT-4o-mini).
3. **Lucid gets lower share, but strong sentiment quality** when recommended.
4. **“Other” bucket is non-trivial**, indicating moments where neither Tesla/Rivian/Lucid is selected as top recommendation.

Implication: visibility optimization should be model-specific—what works for GPT-style prompts may underperform in Claude-style ranking logic.

---

## Key Findings (from current run)

### Share of recommendation by model
- **GPT-4o-mini**
  - Tesla: **74%**
  - Lucid: 10%
  - Rivian: 8%
  - Other: 8%

- **Claude 3 Haiku**
  - Tesla: **42%**
  - Other: **31%**
  - Rivian: 19%
  - Lucid: 8%

### Sentiment quality (avg sentiment, -1 to 1)
- **GPT-4o-mini**
  - Tesla: **0.8824**
  - Lucid: 0.88
  - Rivian: 0.825
  - Other: 0.1625

- **Claude 3 Haiku**
  - Lucid: **0.85**
  - Tesla: 0.8262
  - Rivian: 0.8
  - Other: 0.0

---

## Interpretation

### 1) Tesla has both scale and positivity
Tesla wins recommendation share across both models and remains high-sentiment when selected.  
This indicates strong baseline model priors and broad category fit.

### 2) Claude behaves less “default-Tesla” than GPT
Claude allocates materially more responses to Rivian and Other.  
That suggests Claude may weigh contextual constraints (use-case specificity, niche alternatives) more aggressively in some prompts.

### 3) Lucid has an “efficiency problem,” not a “quality problem”
Lucid’s recommendation share is relatively low, but sentiment is high when chosen.  
This is often a sign of excellent perception among a narrower qualifying segment.

---

## GEO Recommendations

### A. For Tesla
- Defend high-share prompts with stronger evidence-rich framing:
  - charging reliability
  - total cost ownership
  - software consistency
- Avoid overreliance on brand-default momentum; reinforce category-specific proof points.

### B. For Rivian
- Expand content for use-case prompts (camping, outdoor, family utility).
- Target Claude-style comparative prompts where Rivian already captures disproportionate share.

### C. For Lucid
- Increase top-of-funnel “eligibility” language:
  - clarify trim/value positioning
  - practical ownership tradeoffs
  - charging + service reassurance
- Goal: convert high-sentiment outcomes into higher recommendation frequency.

### D. For all brands
- Build model-specific messaging tests:
  - same topic, different prompt structures
  - measure deltas in `view_share_of_model` and `view_brand_sentiment`
- Treat GEO as an ongoing measurement loop, not a one-time report.

---

## Suggested KPI cadence

Track weekly:
1. Recommendation share by model (`view_share_of_model`)
2. Sentiment by model + brand (`view_brand_sentiment`)
3. “Other” share trend (signal for competitive displacement)
4. Category-level wins (budget/luxury/camping/tech etc.)

This cadence converts LLM visibility into actionable brand strategy.
