# Example Interview Transcript

**Scenario**: User wants to add webhook notifications to their SaaS product.

---

**Opening (depth calibration + first question):**

> Claude: "Are you looking for a full spec or initial analysis? And what workaround are people using today for getting notified about events?"

> User: "Full spec. Right now customers poll our API every few minutes. Some of them are hammering us with requests."

**Decision tree mapping:**

> Claude: "I see three key decisions to resolve: (1) push model -- webhooks vs SSE vs WebSockets, (2) delivery guarantees -- at-least-once vs best-effort, (3) auth model for webhook endpoints. Let me start with the push model since the other two depend on it."

**Round 1 -- resolving the push model:**

> Claude: "You mentioned polling is the problem. Webhooks are the standard answer, but SSE would let you avoid customers needing to host endpoints. What's your customer base like -- do most of them have infrastructure to receive webhooks?"

> User: "Yeah, these are B2B customers, they all have backends. Webhooks make sense."

> Claude: "Decision resolved: webhooks. Now for delivery guarantees -- at-least-once means you need a retry queue and idempotency keys. Best-effort is simpler but customers lose events on downtime. Given that polling customers are clearly worried about missing data, I'd guess they need at-least-once?"

> User: "Definitely at-least-once. We can't have customers missing events."

**Progressive synthesis checkpoint:**

> Claude: "Here's what I'm hearing so far: webhooks with at-least-once delivery for B2B customers who currently poll. The main driver is reducing API load while guaranteeing customers don't miss events. Does this track?"

> User: "Yes, but it's not just about API load -- customers also want lower latency. Some of them are polling every 10 seconds."

> Claude: "Good correction -- latency is a co-equal driver with load reduction. Noted."

**Constructive challenge:**

> Claude: "One thing worth addressing: at-least-once delivery means customers receive duplicates. Their endpoints need to be idempotent. Are you planning to provide idempotency keys in the payload, or leave that to customers to figure out?"

> User: "Hmm, I hadn't thought about that. We should include an event ID they can deduplicate on."

**Round 2 -- auth model and failure handling:**

> Claude: "For webhook auth -- HMAC signing is standard. Customers verify the signature to confirm the event came from you. The alternative is mTLS, which is more secure but much harder for customers to set up. Given your B2B audience, which direction?"

> User: "HMAC. We want low friction."

> Claude: "Decision resolved: HMAC signing. Last major branch -- what happens when a customer's endpoint is down? Exponential backoff with a dead letter queue? And what's the retry window before you give up?"

> User: "It depends on the customer tier, actually."

> Claude: "What tiers exist and what would the retry behavior look like for each?"

> User: "Enterprise gets 72 hours of retries, standard gets 24 hours. After that, events go to a dead letter queue they can replay from."

**Final synthesis:**

> Claude: "Full picture: webhook notifications with HMAC signing and at-least-once delivery. Payloads include an event ID for deduplication. Exponential backoff retries -- 72h for enterprise, 24h for standard -- with a dead letter queue + replay API for expired events. Driven by both latency (customers polling at 10s intervals) and API load reduction. Ready to write the spec?"

---

# Quick Reference: Question Progression

**Round 1 - Current State & Foundational:**
- "What workaround are people using today?"
- "Who is the primary user, and what's their mental model coming into this?"
- "What's the cost of getting this wrong vs. shipping slowly?"

**Round 2 - Constraints & Depth Calibration:**
- "What technical constraints from the existing system affect this?"
- "For this project scope, are you looking for full design or initial analysis?"
- "What's the minimum viable version vs. the full vision?"

**Round 3 - Integration & Risk:**
- "How does this interact with [specific related feature]?"
- "If this work isn't done, what breaks first? Rank by impact."
- "Who needs to be notified and when?"

**Round 4 - Edge Cases & Validation:**
- "What happens with concurrent operations?"
- "What's the smallest experiment to validate this approach?"
- "How do we handle the 'undo' scenario?"

**Round 5 - Evolution & Wrap-up:**
- "What's the migration story for existing data/users?"
- "What are we intentionally deferring?"
- "Is there anything we haven't covered that should be captured?"

---

# Recommended Answers in Practice

Every question leads with a proposed answer so the user reacts to a concrete
lean instead of a blank prompt. In AskUserQuestion, the recommended option is
first and labeled `(Recommended)`; the reasoning comes from the context already
gathered.

**Weak (blank prompt):**

> "What delivery guarantee do you want for webhooks?"

**Strong (recommended answer, from context):**

> "You said customers currently poll because they can't miss events. Delivery guarantee?"
> - **At-least-once with retries + idempotency keys (Recommended)** — matches "can't miss events"; costs a retry queue and dedup on the customer side.
> - Best-effort — simpler, but customers lose events on downtime.
> - Exactly-once — strongest, but expensive and rarely needed here.

The recommendation is accepted with one word when right and corrected fast when
wrong — either beats an open question. When you genuinely have no lean, say so
and present balanced options rather than a hollow "recommended" pick.
