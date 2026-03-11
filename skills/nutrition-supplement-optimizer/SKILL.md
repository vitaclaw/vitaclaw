---
name: nutrition-supplement-optimizer
description: "Evaluates dietary nutrition gaps and supplement safety by coordinating nutrition analysis, food alternatives, supplement interaction checks, adverse event screening, and effect tracking. Use when the user wants to optimize their supplement stack or check supplement safety."
version: 1.0.0
user-invocable: true
argument-hint: "[supplement list and diet overview]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"💊","category":"health-scenario"}}
---

# Nutrition and Supplement Optimizer

Scenario orchestration skill for evaluating dietary nutrition gaps and optimizing supplement regimens. Coordinates nutrition analysis, food alternative queries, supplement-supplement and supplement-drug interaction checks, adverse event screening, genetic personalization (optional), and effect tracking. Targets users who want a complete assess-identify-optimize-track pipeline for their supplement stack.

This skill does not perform analysis directly. It orchestrates multiple sub-skills in sequence.

## Medical Disclaimer

**This skill is for nutritional management reference only and does not constitute medical diagnosis or treatment advice.**

- Supplement adjustments do not replace medical nutrition therapy (MNT).
- Users currently on medication must check supplement-drug interactions (e.g., warfarin + vitamin K, thyroid medication + calcium/iron).
- High-dose supplements (exceeding UL) carry health risks and should only be used under physician guidance.
- Pregnant/breastfeeding individuals and patients with hepatic or renal impairment must have supplement plans designed by a physician.
- Discontinue use and seek medical attention immediately if any adverse reaction occurs.

## Skill Chain

| Step | Skill | Trigger | Purpose |
|------|-------|---------|---------|
| 1 | `nutrition-analyzer` | Every session | Dietary nutrient analysis, RDA achievement |
| 2 | `food-database-query` | Every session | Nutrient-rich food lookup, food-first alternatives |
| 3 | `tooluniverse-drug-drug-interaction` | Every session | Supplement-supplement and supplement-drug interactions |
| 4 | `tooluniverse-adverse-event-detection` | Every session | Adverse event signal detection |
| 5 | `nutrigx_advisor` | Optional (with genetic data) | Gene-nutrient metabolism personalization |
| 6 | `health-trend-analyzer` | When historical data exists | Supplement effect correlation analysis |
| 7 | `goal-analyzer` | Every session | Adherence tracking, goal assessment |
| 8 | `health-memory` | Every session | Data persistence |

## Workflow

### Phase 1: Dietary Nutrition Assessment

- [ ] **Step 1a -- Dietary nutrient analysis.** Invoke `nutrition-analyzer`. Analyze current dietary intake of each nutrient. Compare against RDA (Recommended Dietary Allowance) to assess achievement. Identify nutrients that are adequate vs deficient. Evaluate macronutrient ratios (carbohydrate/protein/fat).
- [ ] **Step 1b -- Food alternative lookup.** Invoke `food-database-query`. For each deficient nutrient, query foods rich in that nutrient. Provide "food-first" recommendations (e.g., "Calcium deficit -- 250ml milk + 100g tofu daily provides ~500mg calcium"). Compare feasibility of food supplementation vs pill supplementation.

### Phase 2: Supplement Safety Assessment

- [ ] **Step 2a -- Interaction check.** Invoke `tooluniverse-drug-drug-interaction`. Check supplement-supplement interactions (e.g., calcium and iron compete for absorption; vitamin D and calcium are synergistic; vitamin C enhances iron absorption). Check supplement-drug interactions (e.g., iron/calcium impair levothyroxine absorption; vitamin K antagonizes warfarin). Flag combinations that must be taken at separate times. Flag contraindicated combinations.
- [ ] **Step 2b -- Adverse event screening.** Invoke `tooluniverse-adverse-event-detection`. Retrieve known adverse event signals for each supplement. Assess risk level at current dosage. Flag high-dose risks (e.g., vitamin A hepatotoxicity, excess iron GI effects, high-dose zinc causing copper deficiency). Evaluate long-term use risks.

### Phase 3: Genetic Personalization (Optional)

- [ ] **Step 3 -- Gene-nutrient metabolism personalization.** Invoke `nutrigx_advisor` (requires genetic testing data). Assess MTHFR variant (methylfolate vs standard folic acid). Assess VDR gene (individual vitamin D requirements). Assess FADS1/FADS2 (omega-3 conversion efficiency). Assess HFE (iron metabolism abnormality risk). Assess COMT/CYP (caffeine/supplement metabolism variation).

### Phase 4: Effect Tracking and Goal Assessment

- [ ] **Step 4a -- Supplement effect correlation.** Invoke `health-trend-analyzer`. Analyze fish oil use vs lipid panel trends. Analyze vitamin D supplementation vs 25(OH)D level changes. Analyze iron supplementation vs hemoglobin/ferritin changes. Analyze melatonin use vs sleep quality improvement. Correlate supplement duration with observed effects.
- [ ] **Step 4b -- Goal achievement tracking.** Invoke `goal-analyzer`. Track supplement adherence (daily compliance). Evaluate health goal progress (bone density improvement, fatigue relief, etc.). Set 30-day re-evaluation timepoint.

### Phase 5: Data Persistence

- [ ] **Step 5 -- Persist data.** Invoke `health-memory`. Write supplement plan and assessment results to `memory/health/daily/{YYYY-MM-DD}.md`. Update `memory/health/items/supplements.md` (supplement list and change history). Update other relevant item files.

## Input Format

The user provides the following in natural language:

```
Current supplements:
- Vitamin D3 2000 IU daily after breakfast
- Fish oil 1000mg (EPA+DHA 600mg) daily after lunch
- Calcium 600mg daily after dinner
- Iron 60mg daily on empty stomach
- B-complex daily in the morning

Diet overview:
- Breakfast: milk + whole wheat bread + egg
- Lunch: rice + fish/meat + vegetables
- Dinner: congee + tofu + vegetables
- Occasional fruit, rarely nuts

Health goals: improve bone density, relieve fatigue
Current medications: levothyroxine 50mcg (morning, empty stomach)
```

## Output Format

Generate a 7-section supplement optimization report:

```markdown
# Supplement Optimization Report -- YYYY-MM-DD

## 1. Current Supplement Assessment

| Supplement | Dose | Verdict | Rationale |
|-----------|------|---------|-----------|
| Vitamin D3 | 2000 IU/day | Necessary | Dietary vitamin D insufficient; bone density is a health goal |
| Fish oil | 1000mg/day | Optional | Dietary fish intake is moderate; could replace with 3x/week fish |
| Calcium | 600mg/day | Necessary | Dietary calcium ~500mg/day; supplement brings total to ~1100mg, near RDA |
| Iron | 60mg/day | Needs recheck | Dose is high; check ferritin to confirm ongoing need |
| B-complex | Standard dose | Redundant | Dietary B-vitamins already meet RDA; no clear deficiency |

Verdict categories:
- **Necessary**: Diet cannot meet need + clear health requirement
- **Optional**: Diet mostly sufficient; supplement provides extra assurance
- **Redundant**: Diet already adequate; supplement adds no benefit
- **Needs recheck**: Lab test needed to confirm whether to continue
- **Risk**: Current plan has safety concerns

## 2. Interaction Warnings

### Supplement x Supplement
| Combination | Type | Notes |
|-------------|------|-------|
| Calcium + Iron | Absorption competition | Calcium inhibits iron absorption by 40-50%; must take separately (>= 2h apart) |
| Vitamin D + Calcium | Synergistic | Vitamin D enhances calcium absorption; take together |
| Vitamin C + Iron | Synergistic | Vitamin C enhances non-heme iron absorption; consider pairing |

### Supplement x Medication
| Combination | Type | Notes |
|-------------|------|-------|
| Iron + Levothyroxine | Absorption interference | Iron severely impairs thyroid hormone absorption; separate by >= 4 hours |
| Calcium + Levothyroxine | Absorption interference | Calcium impairs thyroid hormone absorption; separate by >= 4 hours |

## 3. Optimized Dosing Schedule

| Supplement | Recommended Time | With food? | Notes |
|-----------|-----------------|------------|-------|
| Levothyroxine | 06:30 | Empty stomach | Take first; separate from all supplements by 4h |
| Iron | 10:30 | Empty stomach | 4h after levothyroxine; best absorbed on empty stomach |
| Vitamin D3 + Calcium | 12:00 (lunch) | With meal | Fat-soluble vitamin D needs dietary fat; calcium is synergistic |
| Fish oil | 12:00 (lunch) | With meal | Fat-soluble; better absorbed with food |
| B-complex | (recommend discontinuing) | -- | Dietary intake already sufficient |

## 4. Food-First Alternatives

| Nutrient | Current Gap | Food Alternative | Can fully replace supplement? |
|----------|------------|-----------------|------------------------------|
| Calcium | ~500mg/day | 250ml milk (300mg) + 100g firm tofu (200mg) daily | Yes, if consistently maintained |
| Iron | Needs lab check | Liver or beef 2-3x/week + pair with vitamin C source | If ferritin is normal, food can replace |
| Vitamin D | Very hard to meet via diet | Salmon/mushrooms + 15 min daily sun exposure | Difficult to fully replace; continue supplement |
| Omega-3 | Slightly low | Deep-sea fish 3x/week (salmon/mackerel/sardines) | Can replace fish oil supplement |

## 5. Dosage Recommendations

| Supplement | Current | RDA | UL | Recommended | Notes |
|-----------|---------|-----|-----|-------------|-------|
| Vitamin D3 | 2000 IU | 600 IU | 4000 IU | 2000 IU (maintain) | Safe range; supports bone density goal |
| Calcium | 600mg | 1000mg | 2500mg | 600mg (reduce to 300mg if food intake improves) | Diet + supplement total should not exceed 1500mg |
| Iron | 60mg | 18mg (F) / 8mg (M) | 45mg | Check ferritin first | Current dose exceeds UL; not recommended for non-anemic individuals |
| Fish oil | 1000mg | No RDA | 3000mg EPA+DHA | Discontinue if food intake is sufficient | Safe range |

## 6. Genetic Personalization

(Requires genetic testing data. If available, the following analysis will be shown:)

- **MTHFR**: C677T/A1298C variant status -- determines folate form (methylfolate vs standard folic acid)
- **VDR**: Vitamin D receptor gene variant -- adjusts vitamin D dosage
- **FADS1/FADS2**: Omega-3 conversion efficiency -- determines need for preformed EPA/DHA
- **HFE**: Iron metabolism gene -- iron supplementation safety assessment

## 7. 30-Day Tracking Plan

| Timepoint | Action |
|-----------|--------|
| Day 1 | Adjust dosing schedule per new plan |
| Week 1 | Monitor for GI discomfort or other reactions |
| Week 2 | Assess adherence + subjective improvement (fatigue relief?) |
| Week 4 | Re-evaluate: ferritin check, adherence stats, goal progress |
| Week 8 (optional) | Check 25(OH)D level, lipid panel |

### Recommended Follow-Up Labs
- Ferritin + serum iron + TIBC (confirm whether iron is still needed)
- 25(OH)D (confirm vitamin D adequacy; target 30-50 ng/mL)
- Bone density (recheck in 6-12 months)
```

## Alert Rules

| Severity | Condition | Action |
|----------|-----------|--------|
| **High** | Contraindicated supplement-drug combination (e.g., vitamin K + warfarin) | Discontinue the supplement immediately; contact physician |
| **High** | Supplement dose exceeds UL | Recommend dose reduction or discontinuation; warn of overdose risk |
| **Medium** | Competing supplements not taken separately | Adjust dosing schedule |
| **Medium** | Suspected adverse reaction reported | Recommend stopping the suspected supplement and observing |
| **Low** | Redundant supplement (dietary intake already sufficient) | Suggest evaluating whether to continue |

## Data Persistence

All data is stored via the `health-memory` skill following its format conventions:

- **Daily records**: `memory/health/daily/YYYY-MM-DD.md` -- supplement assessment summary
- **Supplement longitudinal**: `memory/health/items/supplements.md` -- current regimen + change history
- **Medication records**: `memory/health/items/medications.md` -- medication list (for interaction checks)
