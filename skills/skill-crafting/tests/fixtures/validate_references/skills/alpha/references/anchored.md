# Anchored

<!-- SCENARIO: cross-file anchor targets + ambiguous slug (WARN) -->

## Real Heading

Cross-file anchor `anchored.md#real-heading` resolves here.

Jump to the [ambiguous section](#duplicate) -- this link targets an
anchor that slugifies to the same value as two different headings below,
which the validator must flag as WARN (ambiguous-slug class).

## Duplicate

First occurrence of a heading that slugifies to `duplicate`.

## Duplicate

Second occurrence with identical text -- slugifier must disambiguate to
`duplicate-1`. A validator should flag the link above as WARN so authors
know which anchor actually resolves.
