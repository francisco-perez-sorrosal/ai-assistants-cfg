---
validate-references: off
---

# Ignored via frontmatter

<!-- SCENARIO: file-level opt-out suppresses ALL findings in this file -->

Every link below would normally FAIL. The file-level frontmatter
`validate-references: off` suppresses them all.

- [broken intra](references/nope.md)
- [broken sibling](../zeta/SKILL.md)
- [broken anchor](#missing)
- [broken cross-file](references/nope.md#anything)
