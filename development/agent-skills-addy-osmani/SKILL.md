---
name: agent-skills-addy-osmani
description: "Use when building production-grade AI coding agent skills."
---

# Agent Skills (Addy Osmani) — Reverse-Engineering Analysis

GitHub: https://github.com/addyosmani/agent-skills
MIT, 104.7k stars, 25 skills for AI coding agents.

> **Полный разбор** (все 25 скиллов, паттерны): `/root/kb/projects/agent-skills-addy-osmani.md`

## Development Lifecycle

```
DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP
  /spec   /plan   /build   /test   /review  /ship
```

## 25 Skills

### Core Development
| Skill | Key Principle |
|-------|---------------|
| `api-and-interface-design` | Hyrum's Law: every observable behavior = contract. One-Version Rule. Idempotency Key: claim atomically, guard payload |
| `frontend-ui-engineering` | Anti-AI Aesthetic (no purple/indigo, no rounded-2xl, no gradient hero). Design system adherence. WCAG 2.1 AA |
| `git-workflow-and-versioning` | Trunk-based development. Atomic commits |
| `code-review-and-quality` | Beyonce Rule (test pyramid), change sizing, review speed |
| `code-simplification` | Chesterton's Fence: understand why before removing |
| `test-driven-development` | RED → GREEN → REFACTOR |
| `debugging-and-error-recovery` | 4-phase root cause debugging |
| `constraint-driven-development` | Constraints → creativity |
| `spec-driven-development` | PRD → implementation |
| `source-driven-development` | Read docs, don't guess |
| `doubt-driven-development` | Challenge your own assumptions |

### Quality & Operations
| Skill | Key Principle |
|-------|---------------|
| `production-readiness` | Observability, rollback, feature flags |
| `security-first-development` | Shift Left, threat modeling |
| `ci-cd-and-automation` | Feature flags, trunk-based, automated deploys |
| `browser-testing-with-devtools` | DevTools Protocol, Lighthouse |
| `quality-audits` | Metrics, coverage, lint |

### Communication & Process
| Skill | Key Principle |
|-------|---------------|
| `context-engineering` | Token budget, compaction |
| `deprecation-and-migration` | Code as liability, migration path |
| `documentation-and-adrs` | Architecture Decision Records |
| `idea-refine` | Requirements interrogation |
| `pattern-based-development` | Don't reinvent the wheel |
| `using-agent-skills` | Auto-activation by context |

## Key Patterns Worth Stealing

1. **Hyrum's Law** — every observable behavior = contract. Deprecate at design time.
2. **Idempotency Key** — claim atomically (unique constraint), guard payload, retention > retry path.
3. **Anti-AI Aesthetic** — checklist against AI look in UI.
4. **Skill quality bar** — specific, verifiable, battle-tested, minimal.
5. **Slash commands → lifecycle** — /spec → /plan → /build → /test → /review → /ship.
6. **Container/Presentation split** — data fetching separate from rendering.
7. **Accessibility baked in** — WCAG 2.1 AA in every UI skill.
8. **ADR (Architecture Decision Records)** — documenting decisions.
9. **Deprecation as liability** — stale code = debt.
10. **/build auto** — plan once, implement all, pause on failures.

## Anti-AI Aesthetic Checklist

| AI Default | Problem | Production |
|------------|---------|------------|
| Purple/indigo | Every app looks same | Project's real palette |
| Excessive gradients | Visual noise | Flat or subtle |
| Rounded-2xl everywhere | Ignores hierarchy | Design system radii |
| Generic hero | No content connection | Content-first |
| Oversized padding | Destroys hierarchy | Consistent spacing scale |
| Stock card grids | Ignores priority | Purpose-driven layouts |

## Component Structure

```
src/components/TaskList/
  TaskList.tsx           # Implementation
  TaskList.test.tsx      # Tests
  TaskList.stories.tsx   # Storybook
  use-task-list.ts       # Custom hook (complex state)
  types.ts               # Types
```

- Prefer composition over configuration
- Container/Presentation split
- Prop drilling max 3 levels
- State order: local → lifted → context → URL → server → global

## Installation

```bash
npx skills add addyosmani/agent-skills
# Claude Code: /plugin marketplace add addyosmani/agent-skills
# Cursor: copy skills/ to .cursor/skills/
```