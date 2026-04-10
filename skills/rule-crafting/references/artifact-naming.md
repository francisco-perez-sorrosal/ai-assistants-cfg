# Artifact Naming Conventions

Naming conventions for context engineering artifacts: skills, agents, commands, rules, hooks, and MCP servers. Back to [SKILL.md](../SKILL.md).

## Universal Constraints

All artifact identifiers (directory names, filenames, `name` fields):

- Lowercase letters, numbers, and hyphens only
- No consecutive hyphens (`--`), no leading or trailing hyphens
- Kebab-case for multi-word names
- No generic names (`helper`, `utils`, `tools`, `stuff`, `misc`, `common`)

## Skills -- Directory Names

**Pattern**: `{domain}-{activity}` or `{artifact}-crafting` for meta-skills

The directory name is the skill's identity -- Claude Code infers the `name` from it. Names should communicate what domain the skill covers and what kind of work it enables.

**Semantic categories:**

| Category | Pattern | Examples |
|----------|---------|----------|
| Meta-crafting | `{artifact}-crafting` | `skill-crafting`, `agent-crafting`, `rule-crafting`, `command-crafting`, `mcp-crafting` |
| Domain + activity | `{domain}-{activity}` | `python-development`, `code-review`, `software-planning` |
| Domain + scope | `{domain}-{qualifier}` | `python-prj-mgmt` |
| Single activity | `{gerund}` | `refactoring` |

**Naming principles:**

- Prefer gerund forms (`refactoring`) or noun phrases (`code-review`) over bare nouns
- A bare noun (`documentation`) is too vague -- add a qualifier: `doc-management`, `doc-authoring`
- The name should answer "skill for doing what?" -- `python-development` (developing in Python), `code-review` (reviewing code)
- Abbreviations acceptable when the long form is unwieldy and the abbreviation is unambiguous: `python-prj-mgmt`

**Good and bad names:**

| Good | Bad | Why |
|------|-----|-----|
| `doc-management` | `documentation` | Activity vs. bare noun |
| `python-development` | `python` | Specifies the activity, not just the language |
| `code-review` | `review` | Scopes to code, avoids ambiguity |
| `skill-crafting` | `skills` | Describes what you do with it |

## Agents -- File Names

**Pattern**: `{role}.md` or `{domain}-{role}.md`

Agents are named for their role in the pipeline. The name should complete the sentence "this agent is a ___."

| Pattern | When to Use | Examples |
|---------|-------------|---------|
| Single role noun | Role is universally understood | `researcher`, `implementer`, `verifier`, `sentinel` |
| Domain-qualified role | Role needs scoping | `systems-architect`, `implementation-planner`, `context-engineer`, `doc-engineer` |
| Evocative noun | Role is conceptual, not functional | `promethean` |

**Naming principles:**

- Use role nouns, not verbs -- `researcher` (not `research`), `verifier` (not `verify`)
- Qualify when the bare role is ambiguous -- `systems-architect` (not `architect`)
- The filename must match the `name` field in frontmatter exactly
- Compound roles use the `{domain}-{role}` pattern, not `{role}-of-{domain}`

## Commands -- File Names

**Pattern**: `{verb}-{object}.md` or abbreviation

Commands are user-invoked actions. Names should read as imperative verbs.

| Pattern | When to Use | Examples |
|---------|-------------|---------|
| Verb-object | Default for all commands | `create-worktree`, `merge-worktree`, `add-rules`, `manage-readme` |
| Verb-qualifier-object | Object needs scoping | `create-simple-python-prj` |
| Abbreviation | High-frequency commands only | `co` (commit), `cop` (commit and push) |

**Naming principles:**

- Start with a verb in imperative mood -- `create`, `add`, `merge`, `manage`
- The filename (minus `.md`) becomes the `/slash-command` name
- Abbreviations are acceptable for high-frequency commands, but document the expansion
- Avoid noun-only names -- `/worktree` tells you nothing; `/create-worktree` tells you what it does

## Rules -- File Names and Directory Structure

**Pattern**: `{domain}-{intent}.md` inside `{category}/` directories

Rules are contextual knowledge loaded by relevance. The filename directly affects Claude's ability to match the rule to the right context.

| Level | Convention | Examples |
|-------|-----------|----------|
| Directory | Domain category (broad) | `swe/`, `writing/` |
| Subdirectory | Sub-domain (when needed) | `swe/vcs/` for version control rules |
| File | `{domain}-{intent}.md` | `coding-style.md`, `git-conventions.md` |

**Naming principles:**

- The domain prefix aids relevance matching -- `git-conventions.md` loads when Claude works on commits
- Be specific -- `git-conventions.md` (not `commit.md`)
- Domain-oriented, not action-oriented -- rules describe what to know, not what to do

## Hooks -- File Names

**Pattern**: `{event}-{purpose}.sh` or `{purpose}.sh`

Hooks are event-driven scripts triggered by lifecycle events (`PreToolUse`, `PostToolUse`, `Stop`, `SubagentStart`, `SubagentStop`).

| Pattern | When to Use | Examples |
|---------|-------------|---------|
| Purpose-first | Hook name describes its function | `send-event.sh`, `memory-gate.sh` |
| Event-qualified | Multiple hooks on the same event | `pre-tool-use-lint.sh`, `post-tool-use-format.sh` |

**Naming principles:**

- Use the function the hook performs, not the event it hooks into
- Kebab-case, `.sh` extension for shell scripts, `.py` for Python
- Hook filenames are internal to the plugin -- users do not invoke them directly
- Registration in `settings.json` maps the event to the script; the filename is for developer comprehension

## MCP Servers -- Package Names

**Pattern**: `{service}-{protocol}` or `{domain}-server`

MCP servers expose tools, resources, and prompts over the Model Context Protocol.

| Pattern | When to Use | Examples |
|---------|-------------|---------|
| Service name | Server wraps a specific service | `memory`, `task-chronograph` |
| Domain + server | Server covers a broader domain | `github-server`, `database-server` |

**Naming principles:**

- The name appears in `mcp.json` and `claude mcp add` commands -- keep it short and memorable
- Prefer the service or domain name alone when unambiguous
- Add `-server` suffix only when the bare name could be confused with a skill or command
- For bundles (`.mcpb`), the `name` field in `manifest.json` follows the same conventions

## Cross-Artifact Consistency

When a skill, agent, and command relate to the same domain, align their names:

| Concern | Skill | Agent | Command |
|---------|-------|-------|---------|
| Documentation | `doc-management` | `doc-engineer` | `manage-readme` |
| Code review | `code-review` | `verifier` | (none) |
| Planning | `software-planning` | `implementation-planner` | (none) |
| Memory | `memory` | (none) | `cajalogic` |

The names do not need to be identical -- each follows its own type's pattern -- but they should share enough vocabulary that the relationship is obvious.
