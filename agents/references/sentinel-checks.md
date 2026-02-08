# Sentinel Check Catalog

Reference file for the sentinel agent's Pass 1 (automated) and Pass 2 (LLM judgment) checks across eight audit dimensions.

**Convention:** Each check has a unique ID, type classification, rule statement, and concrete pass condition. The sentinel loads this file at the start of Pass 1 and works through each dimension sequentially.

---

## Completeness

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| C01 | auto | Every skill directory has a `SKILL.md` | `Glob skills/*/SKILL.md` count matches `Glob skills/*/` directory count |
| C02 | auto | Every `SKILL.md` has `description` in frontmatter | `Grep ^description:` in YAML block of each `SKILL.md` |
| C03 | auto | Every agent `.md` has `name`, `description`, `tools` in frontmatter | `Grep` for each field in YAML block of each `agents/*.md` |
| C04 | auto | Every command has a `description` field or header comment | `Read` each command file, check for description |
| C05 | auto | `plugin.json` lists all agents by explicit file path | Agent count in `plugin.json` matches file count in `agents/*.md` (excluding README) |
| C06 | llm | Skill descriptions are specific enough for activation | Could Claude decide when to load this skill based on description alone? Vague descriptions fail |
| C07 | llm | Agent descriptions enable correct delegation | Could Claude select the right agent based on description alone? Overlapping or thin descriptions fail |
| C08 | llm | No unfilled `[CUSTOMIZE]` sections without justification | `Grep \[CUSTOMIZE\]` in all artifacts; each must be either filled or have a comment explaining why it is left as template |

## Consistency

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| N01 | auto | Skill directories follow naming conventions | All skill directory names use lowercase kebab-case; crafting skills end in `-crafting`; language skills end in `-development` |
| N02 | auto | Agent files follow naming conventions | All agent filenames use lowercase kebab-case `.md` |
| N03 | auto | Frontmatter field names use valid keys per spec | No unrecognized fields in YAML frontmatter (compare against crafting specs) |
| N04 | llm | Terminology consistency across artifacts | Same concept uses the same name everywhere (e.g., "context artifact" not sometimes "context file") |
| N05 | llm | No contradictory instructions between rules and agent prompts | Compare agent boundary descriptions against rule definitions; flag conflicts |
| N06 | llm | Style consistency in descriptions | Agent table descriptions, skill descriptions, and command descriptions follow similar tone and structure |

## Freshness

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| F01 | auto | Referenced files still exist on disk | All file paths mentioned in artifact content resolve to existing files |
| F02 | auto | `references/` files listed in skill content exist | For each skill, paths to reference files mentioned in SKILL.md content exist |
| F03 | llm | Content references current tools and patterns | Skills and agents do not reference tools, APIs, or patterns the project has since replaced |
| F04 | llm | Agent prompts reflect current pipeline structure | Collaboration sections reference correct agent names, outputs, and pipeline stages |

## Spec Compliance

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| S01 | auto | `SKILL.md` frontmatter has `description` (required) | Field present and non-empty |
| S02 | auto | Agent frontmatter has `name`, `description`, `tools` (required) | All three fields present and non-empty |
| S03 | auto | Rule files start with a `##` heading | First non-blank line is a level-2 heading |
| S04 | auto | Command files have `$ARGUMENTS` when arguments are expected | Commands using argument substitution have `$ARGUMENTS` in content |
| S05 | llm | Skills follow progressive disclosure | Core content in SKILL.md, detail in references/; monolithic skills without references fail if over 400 lines |
| S06 | llm | Agent prompts follow structured phase approach | Agents have numbered phases with clear completion criteria |
| S07 | llm | Rules contain domain knowledge, not procedural steps | Rules that read like step-by-step procedures should be skills instead |

## Cross-Reference Integrity

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| X01 | auto | `plugin.json` agent paths resolve to files | Every path in `agents` array resolves to an existing `.md` file |
| X02 | auto | `plugin.json` skill/command directory paths contain expected files | `skills/` contains skill directories; `commands/` contains command files |
| X03 | auto | CLAUDE.md `## Structure` directories exist | Every directory mentioned in the Structure section exists on the filesystem |
| X04 | llm | Latest `IDEA_LEDGER_*.md` implemented ideas reference real artifacts | Ideas in the Implemented section should correspond to artifacts that exist in the codebase |
| X05 | auto | `software-agents-usage.md` agent table matches `agents/` | Agent names in Available Agents table match agent files (one-to-one) |
| X06 | auto | `agents/README.md` agent table matches `agents/` | Agent names in README table match agent files (one-to-one) |
| X07 | llm | README catalog entries match actual artifacts and descriptions | Descriptions in README tables are consistent with artifact frontmatter descriptions |
| X08 | llm | Agent collaboration sections reference correct counterparts | Cross-agent references (e.g., "invoke the context-engineer") name agents that actually exist |

## Token Efficiency

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| T01 | auto | Skill `SKILL.md` line count within guideline | Each SKILL.md is under 500 lines (warn at 400, fail at 600) |
| T02 | auto | Combined always-loaded content size | Total estimated tokens for CLAUDE.md + all rules under 6,000 (heuristic: chars / 3.5) |
| T03 | auto | Agent prompt size within range | Each agent `.md` under 400 lines (warn at 300, fail at 500) |
| T04 | auto | Individual reference file sizes | No single reference file exceeds 800 lines |
| T05 | llm | Content uses progressive disclosure where appropriate | Monolithic artifacts that could split core vs. reference material without losing coherence |
| T06 | llm | No significant redundancy across artifacts | Same information repeated in multiple places wastes tokens; flag duplicates |

## Pipeline Discipline

Checks in this dimension require Task Chronograph data. When Chronograph is unavailable, skip with a note.

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| P01 | auto | No delegation chains exceeding depth limit | Query Chronograph for delegation chains; none exceed depth 2 without user confirmation |
| P02 | auto | Interaction reports are complete | Every `delegation` interaction has a matching `result` interaction |
| P03 | auto | Agent events have matching start/stop pairs | Every `agent_start` event has a corresponding `agent_stop` |
| P04 | llm | Agents operate within declared scope | Agent outputs do not include actions outside their boundary (e.g., implementer making design decisions) |
| P05 | llm | Handoff documents have required sections | Pipeline documents (RESEARCH_FINDINGS.md, SYSTEMS_PLAN.md, etc.) contain their expected sections |

## Ecosystem Coherence

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| EC01 | auto | All agents in the pipeline diagram have corresponding agent files | Agent names in `agents/README.md` pipeline diagram match files in `agents/*.md` |
| EC02 | auto | No orphaned artifacts — every skill/command/rule is referenced by at least one agent or CLAUDE.md | Grep each artifact name across agents and CLAUDE.md; unreferenced artifacts flagged |
| EC03 | llm | Agent collaboration sections form a consistent network | Bidirectional references match — if agent A says "collaborates with B", agent B references A |
| EC04 | llm | Pipeline stages have complete handoff coverage | Every pipeline output document has a producing agent and a consuming agent; no dead-end documents |
| EC05 | llm | Ecosystem has no structural gaps for its stated purpose | Given the project's CLAUDE.md description and Future Paths, are there obvious missing artifact types? |

## Self-Verification

The sentinel includes itself in the audit. These checks apply to the sentinel's own artifacts.

| ID | Type | Rule | Pass Condition |
|----|------|------|----------------|
| V01 | auto | Sentinel is registered in `plugin.json` | `./agents/sentinel.md` appears in the agents array |
| V02 | auto | Sentinel is listed in `software-agents-usage.md` | Agent table contains a sentinel row |
| V03 | auto | Sentinel is listed in `agents/README.md` | Agent table contains a sentinel row |
| V04 | auto | Sentinel check catalog exists | This file (`agents/references/sentinel-checks.md`) exists and is non-empty |
