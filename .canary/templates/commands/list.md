---
description: List top priority CANARY requirements with filtering and sorting
---


## User Input

```text
$ARGUMENTS
```

## Outline

List CANARY requirements with priority-based ordering and comprehensive filtering options.

1. **Parse arguments**:
   - Check for filtering flags (--status, --aspect, --phase, --owner)
   - Check for limit (--limit N)
   - Check for custom ordering (--order-by)
   - Check for output format (--json)

2. **Run canary list command**:
   ```bash
   canary list [flags]
   ```

   **Filtering flags:**
   - `--status <value>`: Filter by status (STUB, IMPL, TESTED, BENCHED, REMOVED)
   - `--aspect <value>`: Filter by aspect (CLI, API, Engine, Storage, Security, Docs, etc.)
   - `--phase <value>`: Filter by phase (Phase0, Phase1, Phase2, Phase3)
   - `--owner <name>`: Filter by owner
   - `--spec-status <value>`: Filter by spec status (draft, approved, in-progress, completed, archived)

   **Output control:**
   - `--limit N`: Maximum results (0 = unlimited, default: 10 for agent context)
   - `--order-by <clause>`: Custom SQL ORDER BY clause
   - `--json`: Output as JSON for parsing
   - `--include-hidden`: Show test files, templates, and examples (hidden by default)

   **Default behavior:**
   - Hides test files, templates, and AI agent directories
   - Orders by: priority ASC, updated_at DESC
   - Limit: unlimited (use --limit 10 for typical agent queries)

3. **Display results**:
   - Show requirement ID and feature name
   - Include status, aspect, priority
   - Display file location with line number
   - Total count of matching requirements

4. **Common usage patterns**:

   **Find new work:**
   ```bash
   canary list --status STUB --limit 5
   ```

   **Find work needing tests:**
   ```bash
   canary list --status IMPL --limit 10
   ```

   **Focus on specific aspect:**
   ```bash
   canary list --aspect CLI --status STUB
   ```

   **Find stale requirements:**
   ```bash
   canary list --order-by "updated_at ASC" --limit 20
   ```

   **View all work for an aspect:**
   ```bash
   canary list --aspect CLI --limit 0
   ```

5. **Analyze and recommend**:
   - Identify highest priority STUB items for planning
   - Note IMPL items needing tests
   - Suggest using `/canary.next` for automatic priority selection
   - Recommend `/canary.plan` for STUB requirements

## Example Output

```markdown
## Top Priority Requirements

Found 10 requirements (showing top 10):

📌 {{.ReqID}}-API-134 - UserOnboarding
   Status: STUB | Aspect: API | Priority: 1
   Location: .canary/specs/{{.ReqID}}-API-134-user-onboarding/spec.md:1

📌 {{.ReqID}}-Engine-140 - ValidationRules
   Status: STUB | Aspect: Engine | Priority: 1
   Location: .canary/specs/{{.ReqID}}-Engine-140-validation-rules/spec.md:1

📌 {{.ReqID}}-API-105 - RegistrationFlow
   Status: IMPL | Aspect: API | Priority: 2
   Location: src/api/registration.go:45

📌 {{.ReqID}}-Engine-142 - AsyncQueue
   Status: IMPL | Aspect: Engine | Priority: 2
   Location: internal/queue/processor.go:78

📌 {{.ReqID}}-Security-115 - SecurityAudit
   Status: TESTED | Aspect: Security | Priority: 3
   Location: internal/security/audit.go:34
   Test: TestCANARY_{{.ReqID}}_Security_115_Audit

**Analysis:**
- **Highest Priority STUB**: {{.ReqID}}-API-134 (UserOnboarding)
- **Needs Tests**: {{.ReqID}}-API-105, {{.ReqID}}-Engine-142 (IMPL status)
- **Completed**: 1 of 10 shown

**Recommendations:**
1. Start with `/canary.plan {{.ReqID}}-API-134` for highest priority STUB
2. Add tests for {{.ReqID}}-API-105 and {{.ReqID}}-Engine-142
3. Use `/canary.next` to automatically select next priority work
```

## Use Cases

**AI Agent Context Management:**
```bash
# Minimal context (ultra-low token usage ~500 tokens)
canary list --status STUB --limit 3

# Standard context (~1500-2000 tokens)
canary list --limit 10

# Comprehensive view (higher token usage)
canary list --limit 0
```

**Workflow Queries:**
```bash
# What should I work on next?
canary list --status STUB --limit 5

# What needs tests?
canary list --status IMPL --limit 10

# What's in Phase1?
canary list --phase Phase1

# What's my team's work?
canary list --owner my-team

# What CLI work is pending?
canary list --aspect CLI --status STUB
```

## Guidelines

- **Default Filtering**: Hide test files, templates, examples for cleaner output
- **Priority First**: Order by priority to surface most important work
- **Context Awareness**: Use --limit to control token usage in agent queries
- **JSON Support**: Enable programmatic parsing with --json
- **Clear Output**: Use emoji indicators and structured formatting
- **Actionable**: Provide specific next steps based on results
- **Database Required**: Suggest `canary index` if database missing
- **Empty Results**: Suggest alternative filters if no matches
