# Product Concept Capability

> From-scratch product definition. Bootstrap may include this when the user is building
> a new product (not replicating an existing one).

## Purpose

Discover product vision, target users, core problems, and competitive positioning
before any technical work. Output: product-concept.json defining what to build and why.

## Protocol

1. Problem discovery: What problem does this solve? Who has this problem?
2. Target user profiling: Demographics, behaviors, pain points
3. Competitive landscape: What alternatives exist? What's the differentiator?
4. Value proposition: One sentence — why this product?
5. Core feature brainstorm: Must-have vs nice-to-have (ruthless prioritization)
6. Success metrics: How do we know this product is working?

Output: `.allforai/product-concept/concept.json`

## Rules (Must Preserve)

1. **Problem-first, not solution-first**: Define the problem before proposing features.
2. **User language**: Describe everything from the user's perspective, not technical terms.
3. **Ruthless prioritization**: Must-have features only for v1. Everything else is post-launch.
4. **Falsifiable metrics**: Success metrics must be measurable numbers, not vague goals.

## Backtrack Triggers

Other nodes may trigger a backtrack to this node when:
- **product-analysis-core** encounters ambiguous or incomplete requirements that cannot be resolved from code or domain knowledge alone → concept needs to clarify scope or detail.

On re-execution: **refine, don't restart**. Read the existing concept.json, identify what downstream flagged as ambiguous, and supplement the specific section. Do not discard previous decisions that weren't flagged.

## Composition Hints

### Single Node (default)
Most projects: one concept node at the very start.

### Skip Entirely
When replicating an existing product (code-replicate flow), concept already exists in the source. Skip this capability.

### Merge with Analysis
For very small projects: concept + product-analysis in one node.
