---
name: v1-shared-language
description: Use when extracting a domain glossary or canonical terminology from a conversation. Triggers on "build a glossary", "ubiquitous language", or "define the domain terms".
---
# Ubiquitous Language

Turn the domain terms in this conversation into a glossary, and write it to a
local file.

## Process

1. **Resolve the glossary owner.** Use the user's supplied path or the glossary
   named by project instructions. Otherwise reuse an existing project glossary
   (`GLOSSARY.md` or `LANGUAGE.md`); if several exist without a clear owner, ask
   which one governs this domain. Create `LANGUAGE.md` in the working directory
   only when no glossary exists. Read the selected file before writing and
   preserve its format and unrelated content.
2. **Scan the conversation** for domain-relevant nouns, verbs, and concepts
3. **Identify problems**:
   - Same word used for different concepts (ambiguity)
   - Different words used for the same concept (synonyms)
   - Vague or overloaded terms
4. **Propose a canonical glossary** with opinionated term choices
5. **Update the selected glossary.** Use the format below for a new file;
   incorporate terms into an existing owner's format instead of creating a
   competing file.
6. **Output a summary** inline, including the path updated and any unresolved
   terminology or write failure.

## Output Format

For a new `LANGUAGE.md`, use this structure. Preserve an existing glossary's
organization when updating it:

```md
# Language

## Order lifecycle

| Term        | Definition                                              | Aliases to avoid      |
| ----------- | ------------------------------------------------------- | --------------------- |
| **Order**   | A customer's request to purchase one or more items      | Purchase, transaction |
| **Invoice** | A request for payment sent to a customer after delivery | Bill, payment request |

## People

| Term         | Definition                                  | Aliases to avoid       |
| ------------ | ------------------------------------------- | ---------------------- |
| **Customer** | A person or organization that places orders | Client, buyer, account |
| **User**     | An authentication identity in the system    | Login, account         |

## Relationships

- An **Invoice** belongs to exactly one **Customer**
- An **Order** produces one or more **Invoices**

## Example dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed. A single **Order** can produce multiple **Invoices** if items ship in separate **Shipments**."
> **Dev:** "So if a **Shipment** is cancelled before dispatch, no **Invoice** exists for it?"
> **Domain expert:** "Exactly. The **Invoice** lifecycle is tied to the **Fulfillment**, not the **Order**."

## Flagged ambiguities

- "account" was used to mean both **Customer** and **User** — these are distinct concepts: a **Customer** places orders, while a **User** is an authentication identity that may or may not represent a **Customer**.
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others as aliases to avoid.
- **Flag conflicts explicitly.** If a term is used ambiguously in the conversation, call it out in the "Flagged ambiguities" section with a clear recommendation.
- **Only include terms relevant for domain experts.** Skip the names of modules or classes unless they have meaning in the domain language.
- **Keep definitions tight.** One sentence max. Define what it IS, not what it does.
- **Show relationships.** Use bold term names and express cardinality where obvious.
- **Only include domain terms.** Skip generic programming concepts (array, function, endpoint) unless they have domain-specific meaning.
- **Group terms by natural clusters** (e.g. subdomain, lifecycle, or actor) while preserving the established glossary's format. In a new or table-based glossary, each group gets a heading and table. One cohesive domain can stay in one group.
- **Write an example dialogue.** A short conversation (3-5 exchanges) between a dev and a domain expert that demonstrates how the terms interact naturally. The dialogue should clarify boundaries between related concepts and show terms being used precisely.

<example>

## Example dialogue

> **Dev:** "How do I test the **sync service** without Docker?"

> **Domain expert:** "Provide the **filesystem layer** instead of the **Docker layer**. It implements the same **Sandbox service** interface but uses a local directory as the **sandbox**."

> **Dev:** "So **sync-in** still creates a **bundle** and unpacks it?"

> **Domain expert:** "Exactly. The **sync service** doesn't know which layer it's talking to. It calls `exec` and `copyIn` — the **filesystem layer** just runs those as local shell commands."

</example>

## Re-running

When invoked again in the same conversation:

1. Read the selected glossary again; keep the established owner
2. Incorporate any new terms from subsequent discussion
3. Update definitions if understanding has evolved
4. Re-flag any new ambiguities
5. Rewrite the example dialogue to incorporate new terms

## Inline term update

The steps above write a full glossary in one pass. This mode does the
opposite: upsert **one** term the moment it is resolved, without rescanning
the conversation or rewriting the file. Use this so a stateful interview (see
`v1-interview-me`'s with-docs mode) can record terms as they settle instead of
losing them.

Given a single term — its canonical name, one-sentence definition, and optional
group and aliases-to-avoid — do exactly this and nothing more:

1. Resolve and read the glossary owner using Process step 1, including any path
   supplied by the caller. Only a new default glossary starts with `# Language`.
2. Find the term's group and definition entry. Follow the existing format
   (table row, definition list, or prose entry); use the default table above
   when the file has no established format.
3. **Upsert the single term:** update its definition and aliases in place if it
   exists; otherwise append one entry to its group. Match on the canonical name.
4. Leave every other term, table, relationship, ambiguity note, and example
   dialogue untouched. Do not re-scan the conversation or regenerate the file.
5. Report the path and term updated, or the write failure. The caller retains
   its interview and overall completion responsibility.

Keep the same tight, opinionated definition style as the batch mode (one
sentence, define what it IS). The upsert is idempotent: calling it again with an
evolved definition updates the row in place rather than duplicating it. Only
promote a term inline once it is actually resolved — a term still under
discussion is not ready to write.
