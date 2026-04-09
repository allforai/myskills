# Consumer Maturity Patterns

> Extracted from product-design-skill: experience-map.md, skill-commons.md

---

## A. 11 Mature Product Patterns

When `experience_priority.mode = consumer` or `mixed`, the experience map must meet consumer maturity standards -- not just "feature exists" but "feels like a mature product". LLM must evaluate each pattern below for applicability.

### 1. Onboarding Wizard

**What it is**: New users don't go directly to the home screen. They walk through a guided flow: goal setting, preference collection, personalized content generation.

**When to apply**: Any product where the first experience determines retention. Products with personalization, learning paths, or content recommendations.

**When NOT to apply**: Simple utility tools where onboarding adds friction without value. Products where users already know exactly what they want (e.g., calculator apps).

**Downstream implications**: Dedicated onboarding screens (3-5 steps), preference storage entities, personalization engine integration, skip/resume capability.

**Screen types**: `onboarding wizard`

---

### 2. Personalized Mainline

**What it is**: Home screen dynamically shows the next step based on user state -- not a static feature list. "Here's what happened, here's what to do now, here's what's next."

**When to apply**: Products with ongoing user journeys (education, fitness, habit tracking, content consumption). Any product where the answer to "what should I do?" changes daily.

**When NOT to apply**: Products where all features are equally important at all times. Reference tools where users always start fresh.

**Downstream implications**: Smart home / today feed screen, user state tracking, recommendation algorithm, dynamic content assembly.

**Screen types**: `smart home` / `today feed`

---

### 3. Process Experience (Ceremony/Ritual)

**What it is**: Core operations are not just "submit form" -- they have progress indicators, real-time feedback, staged results. Fitness = live tracking. Education = interactive challenges. Creation = live preview.

**When to apply**: When the core value is delivered during the process, not just the outcome. Learning, creation, fitness, shopping, cooking.

**When NOT to apply**: Simple transactional operations where speed matters more than experience (e.g., quick transfers, simple lookups).

**Downstream implications**: Live tracking / interactive challenge / step-by-step screens, progress indicators, real-time state updates, animation/transition design.

**Screen types**: `live tracking` / `interactive challenge` / `step-by-step`

---

### 4. Completion Ceremony

**What it is**: After completing a core operation, there's celebration, review, sharing, and next-step recommendation -- not just returning to a list.

**When to apply**: Any product where completing a task should feel rewarding. Education, fitness, creative tools, shopping.

**When NOT to apply (with caution)**: Medical apps (completion = reassurance, not celebration). Financial apps (completion = confirmation and security, not confetti). The tone must match the product context.

**Downstream implications**: Completion / review / share screens, achievement recording, social sharing integration, recommendation engine for next steps.

**Screen types**: `completion` / `review` / `share`

---

### 5. Streaks / Achievements

**What it is**: Consecutive usage days, milestones, achievements, levels. Gives users a reason to come back tomorrow.

**When to apply**: Products that benefit from daily/regular usage habits. Education, fitness, language learning, habit trackers.

**When NOT to apply**: Medical apps ("7-day medication streak badge" undermines seriousness). Financial apps (gamification can feel inappropriate). Products where forced daily usage is harmful.

**Downstream implications**: Streak / achievements screens, streak tracking entities, milestone definitions, push notification integration.

**Screen types**: `streak` / `achievements`

---

### 6. Smart Reminders

**What it is**: Behavior-based push notifications -- not manually configured fixed-time reminders. The system observes usage patterns and nudges at the right moment.

**When to apply**: Products where forgetting leads to churn. Habit products, subscription renewals, content updates.

**When NOT to apply**: Products where notifications would be intrusive or anxiety-inducing. Products with inherent urgency (users come on their own).

**Downstream implications**: Notification center screen, behavior analytics, notification preference settings, notification history.

**Screen types**: `notification center`

---

### 7. Social Layer

**What it is**: Follow, activity feeds, comparisons, challenges. Users stay because of other people, not just the product.

**When to apply**: Products where peer motivation enhances value. Fitness, learning, creative platforms, marketplaces with community aspects.

**When NOT to apply**: Privacy-sensitive products (medical, financial). Products where social comparison causes harm. Solo-focused tools.

**Downstream implications**: Social feed / challenge screens, follow/unfollow entities, activity feed generation, privacy controls.

**Screen types**: `social feed` / `challenge`

---

### 8. Progress Dashboard

**What it is**: Long-term goal progress visualization -- weekly/monthly reports, trend charts, milestones over time.

**When to apply**: Products with measurable long-term goals. Education, fitness, investment, skill development.

**When NOT to apply**: Products without meaningful long-term metrics. Short-session utility tools.

**Downstream implications**: Progress dashboard screens, data aggregation for reports, chart/visualization components, export capability.

**Screen types**: `progress dashboard`

---

### 9. Immersive Consumption

**What it is**: Full-screen, distraction-free content experience (reading, video, audio, learning). Has progress bar and gesture controls.

**When to apply**: Products where content consumption is the core value. Reading apps, video platforms, audio players, learning platforms.

**When NOT to apply**: Products where content is supplementary, not primary. Dashboard-heavy admin tools.

**Downstream implications**: Immersive reader / player screens, gesture controls, progress tracking, bookmark/resume capability, reading/viewing settings.

**Screen types**: `immersive reader` / `player`

---

### 10. Creation Tools

**What it is**: Users create content within the product -- canvas, editor, recorder. Has real-time preview and undo capability.

**When to apply**: Products where user-generated content is part of the value loop. Social platforms, design tools, note-taking, recording apps.

**When NOT to apply**: Pure consumption products. Products where creation happens outside the app.

**Downstream implications**: Canvas / editor / recorder screens, auto-save, version history, undo/redo stack, draft management, export/share.

**Screen types**: `canvas` / `editor` / `recorder`

---

### 11. Decision Funnel

**What it is**: Multi-step decision process (shopping, booking, investing). Each step provides positive feedback ("you saved X", "Y% closer", "estimated result Z") to reduce abandonment.

**When to apply**: Products with multi-step conversion funnels. E-commerce, booking, financial products, subscription services.

**When NOT to apply**: Products with single-action decisions. Products where the decision doesn't benefit from staged reassurance.

**Downstream implications**: Cart -> checkout -> confirmation screens, progress indication across steps, positive feedback at each step, abandonment recovery.

**Screen types**: `cart -> checkout -> confirmation`

---

## B. Anti-Patterns

### The Compressed Admin Panel

**Do not make a mobile app look like a compressed admin panel.** This is the most common failure mode. Signs:
- All screens are list -> detail -> edit (CRUD trilogy)
- No guided flow, no personalization
- Home screen is a feature menu grid
- No state awareness ("what did I do last time?")
- No forward momentum ("what should I do next?")

### The Concept Demo

**Do not make a user-facing app look like a concept demo.** Signs:
- Features exist but feel disconnected
- No persistent state between sessions
- No reason to return tomorrow
- "Technically works" but doesn't feel like a product people use daily

### Feature Checklist Design

**Do not design by checking off feature requirements.** Signs:
- Every feature gets exactly one screen
- No consideration of user flow between features
- Screens don't reference each other
- No information hierarchy -- everything equally prominent

---

## C. Consumer Maturity Scoring

### How to Evaluate Maturity

The key question is not "does the feature exist?" but "does it meet the bar of a mature consumer product?"

**Evaluation Criteria** (when `experience_priority.mode = consumer` or `mixed`):

1. **Does the home screen have a clear mainline?** Not a feature entry grid
2. **Does each core screen tell the user**: what just happened, what to do now, what to do next?
3. **Do empty/loading/error/success states form a unified system?** Not ad-hoc per screen
4. **Are there persistent usage triggers?** Progress, reminders, history, recommendations, subscriptions, continuous feedback
5. **Does the mobile path fit**: single-hand, low-attention, fragmented-time usage?

### Applicability Judgment Principles

- Some patterns in certain domains are **not just unnecessary but harmful**. Ask: "If the user sees this pattern, would they think the product is more professional or less credible?"
- The pattern's **tone** must match the product context. "Completion ceremony" in games = celebration; in medical = reassurance and next steps; in finance = confirmation and security
- When uncertain about a pattern's applicability, ask: **"Do mature competitors in this domain have this pattern?"**

### Consumer-Specific Verification Checklist

When validating experience maps, additionally check:

- Is the mainline clear? (not a feature entry grid)
- Is there rhythm continuity between pages?
- Are core actions sufficiently prominent?
- Is there next-step guidance after each action?
- Are there return-visit reasons?

These checks are structural and interaction maturity -- they do not wait until ui-design.
