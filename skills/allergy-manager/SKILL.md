---
name: allergy-manager
description: "Manages allergy profiles including food, environmental, and drug allergies. Tracks reactions, identifies cross-reactivity risks, provides seasonal allergy forecasts, and warns about allergen exposure. Use when the user reports allergies, asks about cross-reactions, or needs allergen avoidance guidance."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🤧","category":"health"}}
---

# Allergy Manager

Comprehensive allergy profile management, reaction tracking, cross-reactivity identification, seasonal forecasting, and allergen avoidance guidance.

## Capabilities

### 1. Allergy Profile Recording

Maintain a structured allergy profile for the user. Each allergy entry includes the following fields:

| Field | Description | Allowed Values |
|---|---|---|
| `allergen` | Name of the allergen | Free text (e.g., "Peanuts", "Penicillin", "Birch pollen") |
| `type` | Category of allergen | `food`, `environmental`, `drug`, `insect`, `contact` |
| `severity` | Severity classification | `mild`, `moderate`, `severe`, `anaphylaxis` |
| `diagnosed_by` | How the allergy was identified | `self`, `doctor`, `allergy-test` (skin prick, blood IgE, patch test) |
| `date_diagnosed` | Date of diagnosis or first known reaction | ISO 8601 date |
| `notes` | Additional context | Free text |

#### Common Allergen Categories with Examples

**Food Allergens (Top 9 + common others):**
- Peanuts, tree nuts (almond, walnut, cashew, pistachio, pecan, hazelnut, macadamia, Brazil nut)
- Milk (cow, goat, sheep), eggs, wheat, soy, fish, shellfish (shrimp, crab, lobster, clam, mussel)
- Sesame, mustard, celery, lupin, mollusks, corn, nightshades

**Environmental Allergens:**
- Tree pollen (birch, oak, cedar, maple, elm, ash, pine)
- Grass pollen (timothy, bermuda, ryegrass, bluegrass)
- Weed pollen (ragweed, sagebrush, pigweed, lamb's quarters)
- Mold spores (Alternaria, Aspergillus, Cladosporium, Penicillium)
- Dust mites (Dermatophagoides pteronyssinus, D. farinae)
- Pet dander (cat, dog, horse, rabbit, rodents)
- Cockroach particles, feathers

**Drug Allergens:**
- Penicillin and beta-lactam antibiotics (amoxicillin, ampicillin)
- Sulfonamides (sulfamethoxazole)
- NSAIDs (aspirin, ibuprofen, naproxen)
- Anticonvulsants (carbamazepine, phenytoin, lamotrigine)
- Opioids, local anesthetics, contrast dyes, biologics

**Insect Allergens:**
- Bee venom (honeybee, bumblebee)
- Wasp venom (yellowjacket, hornet, paper wasp)
- Fire ant venom
- Mosquito saliva (Skeeter syndrome)

**Contact Allergens:**
- Nickel, cobalt, chromium
- Latex (natural rubber)
- Fragrances (balsam of Peru, cinnamic aldehyde)
- Preservatives (formaldehyde, methylisothiazolinone)
- Hair dyes (paraphenylenediamine / PPD)
- Topical antibiotics (neomycin, bacitracin)

---

### 2. Reaction Logging

Record individual allergic reactions with detailed context for pattern analysis.

| Field | Description | Allowed Values |
|---|---|---|
| `date` | Date and time of reaction | ISO 8601 datetime |
| `trigger` | Suspected or confirmed allergen | Free text |
| `symptoms` | List of symptoms observed | See symptom categories below |
| `severity` | Reaction severity score | `1` (minor) to `5` (life-threatening) |
| `onset_time` | Time from exposure to first symptom | Duration (e.g., "5 minutes", "2 hours") |
| `duration` | Total duration of the reaction | Duration (e.g., "30 minutes", "3 days") |
| `treatment_used` | Medications or interventions applied | Free text |
| `outcome` | How the reaction resolved | `resolved_spontaneously`, `resolved_with_treatment`, `required_ER`, `hospitalized` |

#### Symptom Categories

**Skin Reactions:**
- Hives (urticaria), angioedema (deep tissue swelling)
- Eczema flare (atopic dermatitis)
- Contact dermatitis (redness, blistering, itching)
- Flushing, pruritus (generalized itching)

**Respiratory Reactions:**
- Sneezing, rhinorrhea (runny nose), nasal congestion
- Wheezing, cough, shortness of breath
- Throat tightness, stridor, laryngeal edema
- Asthma exacerbation

**Gastrointestinal Reactions:**
- Nausea, vomiting
- Abdominal cramping, diarrhea
- Oral allergy syndrome (itching/tingling of lips, mouth, throat)

**Ocular Reactions:**
- Itchy, watery eyes (allergic conjunctivitis)
- Eyelid swelling

**Cardiovascular / Systemic Reactions:**
- Anaphylaxis (multi-system involvement)
- Hypotension, tachycardia, dizziness, syncope
- Sense of impending doom

#### Severity Scale Reference

| Score | Label | Description |
|---|---|---|
| 1 | Minor | Localized symptoms, no treatment needed (e.g., mild itching) |
| 2 | Mild | Localized symptoms requiring OTC treatment (e.g., hives in one area) |
| 3 | Moderate | Multiple symptom categories or widespread involvement (e.g., hives + GI upset) |
| 4 | Severe | Respiratory compromise or significant systemic involvement |
| 5 | Life-threatening | Anaphylaxis, cardiovascular collapse, loss of consciousness |

---

### 3. Cross-Reactivity Database

When a user reports an allergy, check for known cross-reactivity risks and proactively warn them.

#### Latex-Fruit Syndrome
Latex allergy is associated with IgE cross-reactivity to certain fruit and vegetable proteins (hevein-like domains):
- **High risk:** Banana, avocado, chestnut, kiwi
- **Moderate risk:** Apple, carrot, celery, papaya, potato, tomato, melon
- **Lower risk:** Pear, mango, fig, pineapple, passion fruit

#### Oral Allergy Syndrome (OAS) / Pollen-Food Allergy Syndrome
Cross-reactivity between inhaled pollen proteins and structurally similar proteins in raw fruits, vegetables, and nuts:

| Pollen Allergy | Cross-Reactive Foods |
|---|---|
| **Birch** | Apple, pear, cherry, peach, plum, apricot, kiwi, carrot, celery, hazelnut, almond, soybean |
| **Ragweed** | Melon (watermelon, cantaloupe, honeydew), banana, zucchini, cucumber, sunflower seeds |
| **Grass** | Tomato, potato, melon, orange, peanut, Swiss chard |
| **Mugwort** | Celery, carrot, parsley, coriander, fennel, anise, sunflower, chamomile, pepper, mustard |
| **Alder** | Apple, cherry, peach, pear, parsley, celery, almond, hazelnut |
| **Plane tree** | Hazelnut, apple, lettuce, corn, chickpea, peanut |

*Note: Cooking typically denatures the offending proteins and eliminates OAS symptoms. Allergy to the cooked form suggests a separate, potentially more serious, food allergy.*

#### Shellfish Cross-Reactivity
Tropomyosin is the major allergen shared across crustaceans and some other invertebrates:
- **Crustaceans:** Shrimp, crab, lobster, crayfish, prawns (high cross-reactivity, ~75%)
- **Mollusks:** Clam, mussel, oyster, scallop, squid, octopus, snail (moderate cross-reactivity)
- **Insects:** Cockroach, dust mites (tropomyosin homology)
- **Dust mite to shrimp:** Individuals allergic to dust mites may react to shrimp and vice versa due to shared tropomyosin

#### Tree Nut Cross-Reactivity Patterns
- **Walnut and pecan** share high cross-reactivity (~90%)
- **Cashew and pistachio** share high cross-reactivity (~70%)
- **Almond** is botanically a stone fruit; lower cross-reactivity with other tree nuts
- **Hazelnut** cross-reacts with birch pollen (OAS) and other tree nuts
- **Coconut** is botanically not a tree nut; cross-reactivity is rare but possible
- **Peanut** is a legume, not a tree nut, but co-allergy is common (~25-40%)

#### Drug Cross-Reactivity
- **Penicillin → Cephalosporins:** ~2% cross-reactivity risk (historically overestimated). First-generation cephalosporins (cephalexin) carry higher risk than third-generation (ceftriaxone).
- **Penicillin → Carbapenems:** ~1% cross-reactivity risk.
- **Sulfonamide antibiotics → Non-antibiotic sulfonamides:** Cross-reactivity is NOT established. Sulfa antibiotic allergy does NOT contraindicate furosemide, thiazides, or celecoxib.
- **NSAID cross-reactivity:** Aspirin-sensitive patients may react to ibuprofen and naproxen. COX-2 inhibitors (celecoxib) are often tolerated.
- **Local anesthetic cross-reactivity:** Esters (procaine, benzocaine) may cross-react with each other. Amides (lidocaine, bupivacaine) rarely cross-react with esters.

#### Additional Cross-Reactivity Groups
- **Red meat allergy (alpha-gal syndrome):** Triggered by Lone Star tick bites; cross-reactivity with mammalian meat (beef, pork, lamb), gelatin, dairy (in some cases), and the drug cetuximab.
- **Legume family:** Peanut, soy, lentil, chickpea, pea. Clinical cross-reactivity is lower (~5%) than serological cross-reactivity.
- **Seed cross-reactivity:** Sesame, poppy, sunflower, and flaxseed may share some protein homology, but clinical cross-reactivity is uncommon.

---

### 4. Seasonal Allergy Calendar

Month-by-month guide to predominant airborne allergens in the **Northern Hemisphere**. Actual timing varies by latitude, climate, and local flora.

| Season | Months | Primary Allergens | Notes |
|---|---|---|---|
| **Late Winter** | Feb - Mar | Tree pollen begins (cedar, juniper, alder, elm) | Earliest tree pollens; varies by region |
| **Spring** | Mar - May | Tree pollen peaks (birch, oak, maple, ash, hickory, walnut, sycamore) | Highest tree pollen counts; rain temporarily reduces airborne pollen |
| **Late Spring** | May - Jun | Grass pollen begins (timothy, bermuda, ryegrass, bluegrass, fescue) | Overlaps with late tree pollen |
| **Summer** | Jun - Aug | Grass pollen peaks; outdoor mold spores rise (Alternaria, Cladosporium) | Hot, humid conditions favor mold growth |
| **Late Summer** | Aug - Sep | Ragweed season begins; mold spores remain high | A single ragweed plant can produce ~1 billion pollen grains |
| **Fall** | Sep - Nov | Ragweed peaks then fades; leaf mold increases; burning bush, sagebrush | First frost typically ends ragweed season |
| **Winter** | Dec - Feb | Indoor allergens dominate: dust mites, pet dander, indoor mold, cockroach | Heating systems circulate indoor allergens; dry air irritates airways |

#### Tips by Season
- **Spring:** Monitor local pollen counts. Shower after outdoor activity. Keep windows closed on high-pollen days. Use HEPA filters.
- **Summer:** Minimize outdoor activity on high-humidity days. Watch for thunderstorm asthma (pollen grains burst in moisture).
- **Fall:** Rake leaves with a mask. Watch for mold in damp leaf piles. Start preventive antihistamines before ragweed season if historically affected.
- **Winter:** Use allergen-proof bedding encasements. Maintain humidity at 30-50% to reduce dust mites. Clean HVAC filters monthly.

---

### 5. Food Label Scanner Guidance

Many allergens appear under unfamiliar names on ingredient labels. Use this reference to identify hidden allergens.

#### Milk (Dairy)
Casein, caseinate (sodium/calcium/magnesium), whey, lactalbumin, lactoglobulin, lactulose, ghee, curds, hydrolysates, recaldent, rennet casein, tagatose. May be in: caramel color, chocolate, nougat, "natural flavoring," baked goods, deli meats, hot dogs.

#### Egg
Albumin (albumen), globulin, lysozyme, ovalbumin, ovomucin, ovomucoid, ovovitellin, meringue, surimi, lecithin (sometimes egg-derived). May be in: pasta, marshmallows, baked goods, foam toppings, vaccines (influenza, yellow fever).

#### Wheat
Durum, einkorn, emmer, kamut, semolina, spelt, triticale, bulgur, couscous, farro, seitan, fu (gluten). May be in: soy sauce, modified food starch, hydrolyzed vegetable protein, malt (sometimes), surimi.

#### Soy
Edamame, miso, natto, tempeh, tofu, soy protein isolate/concentrate, textured vegetable protein (TVP), soy lecithin, soybean oil (often tolerated). May be in: bouillon, vegetable broth, "natural flavoring."

#### Peanut
Arachis oil (peanut oil), beer nuts, ground nuts, mandelonas, monkey nuts, arachis hypogaea. May be in: chili, egg rolls, enchilada sauce, marzipan (sometimes), nougat, ice cream.

#### Tree Nuts
Specific nut flours, butters, oils, extracts, milks, pastes (e.g., praline, marzipan/almond paste, nougat, gianduja, mortadella). Coconut is classified as a tree nut by the FDA but is botanically a fruit.

#### Fish
Surimi, Worcestershire sauce, Caesar dressing, caponata, bouillabaisse, fish sauce (nam pla), fish gelatin, omega-3 supplements (fish-derived).

#### Shellfish
Surimi (may contain shellfish extract), glucosamine (often shrimp-derived), bouillabaisse, cuttlefish ink, shrimp paste.

#### Sesame
Tahini, halvah, hummus, za'atar, sesame oil, benne seeds, gingelly oil, til. May be in: bread, bagels, sushi, tempeh.

#### Major Allergen Lookup Table

| Hidden Name | Allergen Source |
|---|---|
| Casein, caseinate | Milk |
| Albumin, albumen | Egg (or sometimes milk) |
| Lysozyme | Egg |
| Semolina, spelt, kamut | Wheat |
| Lecithin (soy) | Soy |
| Arachis oil | Peanut |
| Tahini | Sesame |
| Surimi | Fish and/or shellfish |
| Glucosamine | Shellfish |
| Carmine, cochineal | Insect (red dye from beetles) |
| Shellac, confectioner's glaze | Insect (lac bug secretion) |
| Gelatin | Beef/pork (alpha-gal concern) |
| Isinglass | Fish (used in some beers/wines) |
| Ghee | Milk (trace casein possible) |
| Natural flavoring | May contain any allergen |
| Hydrolyzed vegetable protein | May be soy or wheat |
| Modified food starch | May be wheat or corn |

---

### 6. Severity Assessment and Action Plans

#### Mild Reaction (Severity 1-2)
- **Symptoms:** Localized hives, mild itching, sneezing, watery eyes, mild oral tingling.
- **Actions:**
  1. Remove exposure to the allergen if identifiable.
  2. Take an oral antihistamine (e.g., cetirizine, loratadine, fexofenadine).
  3. Apply cool compresses for skin symptoms.
  4. Monitor for 1-2 hours for progression.
  5. Log the reaction.
- **Follow-up:** If reactions are recurring, consider allergy testing referral.

#### Moderate Reaction (Severity 3)
- **Symptoms:** Widespread hives, facial swelling (without airway compromise), moderate GI symptoms, multiple symptom categories.
- **Actions:**
  1. Remove allergen exposure immediately.
  2. Take an antihistamine. Consider a second-generation H1 blocker + H2 blocker (e.g., cetirizine + famotidine).
  3. If prescribed, consider oral corticosteroids per doctor's instructions.
  4. Monitor closely for 4-6 hours for progression to severe.
  5. Seek medical evaluation if symptoms do not improve within 1 hour.
  6. Log the reaction in detail.
- **Follow-up:** Schedule allergist appointment. Discuss whether an epinephrine auto-injector prescription is warranted.

#### Severe Reaction (Severity 4-5)
- **Symptoms:** Throat tightness, difficulty breathing, wheezing, significant swelling, hypotension, dizziness, loss of consciousness.
- **Actions:**
  1. **USE EPINEPHRINE AUTO-INJECTOR IMMEDIATELY** (if prescribed and available).
  2. **CALL EMERGENCY SERVICES (911 / 112 / 999).**
  3. Lie down with legs elevated (unless vomiting or having difficulty breathing).
  4. A second dose of epinephrine may be given after 5-15 minutes if no improvement.
  5. Do NOT rely on antihistamines alone for anaphylaxis.
  6. After ER treatment, monitor for biphasic reaction (second wave can occur 1-72 hours later).
- **Follow-up:** Allergist referral is mandatory. Obtain epinephrine prescription if not already on hand. Consider medical alert identification (bracelet/necklace).

#### Anaphylaxis Action Plan Template

```
╔══════════════════════════════════════════════════════════════╗
║              ANAPHYLAXIS EMERGENCY ACTION PLAN              ║
╠══════════════════════════════════════════════════════════════╣
║ Name: [User name]                                           ║
║ Known Allergens: [List]                                     ║
║ Epinephrine Location: [Where auto-injector is kept]         ║
║                                                             ║
║ SIGNS OF ANAPHYLAXIS (any ONE of these):                    ║
║  • Difficulty breathing, wheezing, stridor                  ║
║  • Swelling of tongue or throat                             ║
║  • Persistent dizziness or collapse                         ║
║  • Pale and floppy (in children)                            ║
║  • Abdominal pain with vomiting (after insect sting/drug)   ║
║                                                             ║
║ ACTION:                                                     ║
║  1. Give epinephrine auto-injector into outer mid-thigh     ║
║  2. Call emergency services (911 / 112 / 999)               ║
║  3. Lay person flat; elevate legs (if breathing permits)    ║
║  4. If no improvement in 5-15 min, give 2nd epinephrine     ║
║  5. Stay with person until paramedics arrive                ║
║                                                             ║
║ Emergency Contact: [Name, phone]                            ║
║ Allergist: [Name, phone]                                    ║
║ Hospital: [Preferred hospital]                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

### 7. Pattern Analysis

When sufficient reaction data has been logged, perform the following analyses:

#### Seasonal Patterns
- Correlate reaction dates with pollen calendars and weather data.
- Identify months or seasons where reactions cluster.
- Flag likely seasonal allergies that may benefit from prophylactic treatment.

#### New Sensitivities
- Detect new allergens appearing in the reaction log that are not in the allergy profile.
- Prompt the user to add newly identified triggers to their profile.
- Check cross-reactivity database to see if the new trigger is related to a known allergy.

#### Improving or Worsening Trends
- Track severity scores over time for each allergen.
- Flag allergens where average severity is increasing (potential worsening sensitization).
- Note allergens where tolerance appears to be developing (decreasing severity, especially relevant for children outgrowing allergies).

#### Trigger Correlations
- **Weather:** High pollen days, humidity changes, temperature shifts, thunderstorms.
- **Stress:** Correlate reactions with reported stress levels or life events (stress can amplify allergic responses via mast cell activation).
- **Food combinations:** Some reactions may require co-factors (e.g., exercise-induced food allergy: wheat + exercise = anaphylaxis).
- **Medication changes:** Starting or stopping medications (e.g., beta-blockers can worsen anaphylaxis risk; ACE inhibitors increase angioedema risk).
- **Hormonal cycles:** Some individuals experience worsened allergies premenstrually or during pregnancy.

#### Analysis Output
When reporting patterns, provide:
- Summary of identified patterns with confidence level (strong, moderate, suggestive).
- Supporting data points (specific dates, reactions, severity scores).
- Actionable recommendations (prophylactic treatment, avoidance strategies, specialist referral).

---

## Output Formats

### Daily Log Entry
When recording a reaction in the daily log, use this format:

```markdown
### Allergy Reaction - [Time]
- **Trigger:** [Allergen]
- **Symptoms:** [Comma-separated list]
- **Severity:** [1-5] ([label])
- **Onset:** [Duration from exposure]
- **Duration:** [How long symptoms lasted]
- **Treatment:** [What was taken/done]
- **Outcome:** [How it resolved]
- **Notes:** [Any additional context]
```

### Profile Summary
When presenting the allergy profile, format as:

```markdown
## Allergy Profile Summary

### Food Allergies
| Allergen | Severity | Diagnosed By | Date | Notes |
|---|---|---|---|---|
| [name] | [level] | [method] | [date] | [notes] |

### Environmental Allergies
| Allergen | Severity | Diagnosed By | Date | Notes |
|---|---|---|---|---|

### Drug Allergies
| Allergen | Severity | Diagnosed By | Date | Notes |
|---|---|---|---|---|

### Cross-Reactivity Alerts
- [Allergen] → Watch for: [cross-reactive items]
```

### Alert Format
When a cross-reactivity or exposure risk is detected:

```markdown
> ⚠️ **ALLERGY ALERT**
> [Description of the risk]
> **Known allergy:** [Allergen]
> **Risk factor:** [Cross-reactive substance or exposure scenario]
> **Recommended action:** [What to do]
```

For anaphylaxis-level warnings:

```markdown
> 🚨 **ANAPHYLAXIS RISK**
> [Description]
> **Carry epinephrine at all times.**
> **If symptoms occur: Use epi-pen → Call emergency services → Do NOT delay.**
```

---

## Data Persistence

### Daily Log Files
Reaction events are recorded in the user's daily log file at the standard daily log path. Each reaction is appended under the appropriate date with full details.

### Allergy Profile File
The master allergy profile is stored at:

```
items/allergies.md
```

This file contains:
- The complete allergy profile table (all known allergens, types, severities, diagnosis info).
- Active cross-reactivity alerts.
- Current action plan (including epinephrine status and emergency contacts).
- Last-updated timestamp.

When updating the allergy profile:
1. Read the existing `items/allergies.md` file.
2. Merge new information (do not duplicate entries; update existing entries if severity or notes change).
3. Regenerate cross-reactivity alerts based on the updated profile.
4. Write the updated file.

---

## Alerts and Safety

### Medical Emergency: Anaphylaxis

**Anaphylaxis is a life-threatening medical emergency.** If the user describes symptoms consistent with anaphylaxis (difficulty breathing, throat swelling, rapid drop in blood pressure, widespread hives with systemic symptoms), immediately advise:

1. **Use epinephrine auto-injector NOW** if available.
2. **Call emergency services immediately** (911 in the US, 112 in EU, 999 in UK).
3. **Do not wait** to see if symptoms improve on their own.
4. **Do not substitute antihistamines** for epinephrine in anaphylaxis.

### Important Safety Reminders

- **This tool is NOT a substitute for professional allergy testing.** Skin prick tests, specific IgE blood tests, and oral food challenges conducted by a board-certified allergist are the gold standard for allergy diagnosis.
- **Always carry prescribed epinephrine** if you have a history of anaphylaxis or severe allergic reactions. Check expiration dates regularly (typically every 12-18 months).
- **Wear medical alert identification** (bracelet or necklace) listing severe allergies, especially for drug allergies and anaphylaxis history.
- **Inform healthcare providers** about all allergies before any medical procedure, new prescription, or vaccination.
- **When in doubt, avoid the trigger** and consult a healthcare professional.
- Cross-reactivity information represents population-level risk. Individual reactions vary. A negative cross-reaction for most people does not guarantee safety for a specific individual.

### Medical Disclaimer

> **This allergy management tool provides informational guidance only and does not constitute medical advice, diagnosis, or treatment.** Allergy management decisions, including medication use, allergen avoidance strategies, and emergency action plans, should be developed in partnership with a qualified healthcare provider such as a board-certified allergist/immunologist. Never delay seeking emergency medical care based on information from this tool. If you believe you are experiencing a severe allergic reaction, call emergency services immediately.
