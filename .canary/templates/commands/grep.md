---
description: Search CANARY tokens by keyword or pattern across all fields
---


## User Input

```text
$ARGUMENTS
```

## Outline

Search for CANARY tokens matching a keyword or pattern across features, files, tests, and requirement IDs.

1. **Parse search pattern**:
   - Extract search keyword/pattern from arguments
   - Pattern is case-insensitive
   - Searches across all fields (feature, file path, test name, bench name, req ID)

2. **Run canary grep command**:
   ```bash
   canary grep <pattern>
   ```

   Available flags:
   - `--group-by none`: Flat list of results [default]
   - `--group-by requirement`: Group by requirement ID
   - `--db <path>`: Custom database path (default: `.canary/canary.db`)

3. **Display search results**:
   - Show matching tokens with context
   - Include requirement ID, feature name, status
   - Show file location and line number
   - Highlight matched field (what matched the pattern)
   - Total match count

4. **Categorize results**:
   - Group by requirement if `--group-by requirement` used
   - Show status distribution of matches
   - Identify patterns in results (e.g., all in one directory)

5. **Provide navigation**:
   - List file:line references for each match
   - Suggest refinement if too many results
   - Suggest related searches

## Example Output

```markdown
## Search Results for "Auth"

Found 8 matches:

📌 {{.ReqID}}-API-120 - UserAuthentication
   Status: TESTED | Aspect: API | Priority: 1
   Location: src/api/auth/user.go:45
   Test: TestCANARY_{{.ReqID}}_API_120_UserAuthentication
   Match: Feature name

📌 {{.ReqID}}-API-120 - AuthMiddleware
   Status: TESTED | Aspect: API | Priority: 2
   Location: src/api/auth/middleware.go:23
   Test: TestCANARY_{{.ReqID}}_API_120_AuthMiddleware
   Match: Feature name

📌 {{.ReqID}}-API-121 - OAuth2Integration
   Status: IMPL | Aspect: API | Priority: 1
   Location: src/api/auth/oauth.go:67
   Match: File path

📌 {{.ReqID}}-Security-134 - SessionValidation
   Status: TESTED | Aspect: Security | Priority: 1
   Location: src/api/auth/session.go:89
   Test: TestAuthSession
   Match: Test name "TestAuthSession"

**Summary:**
- Total matches: 8
- Requirements: 3 ({{.ReqID}}-API-120, {{.ReqID}}-API-121, {{.ReqID}}-Security-134)
- Status: TESTED (5), IMPL (3)
- Primary location: src/api/auth/

**Suggested refinements:**
- `canary grep src/api/auth` - Focus on auth directory
- `canary grep {{.ReqID}}-API-120` - See all tokens for {{.ReqID}}-API-120
- `canary show {{.ReqID}}-API-121` - View details of OAuth2Integration
```

## Use Cases

**Find by Feature:**
```bash
canary grep User       # All tokens related to users
canary grep Cache      # All caching-related tokens
canary grep Parse      # All parsing-related tokens
```

**Find by Location:**
```bash
canary grep src/api/auth      # Tokens in auth directory
canary grep cmd/app           # Tokens in CLI commands
canary grep internal/db       # Tokens related to database
```

**Find by Test:**
```bash
canary grep TestAuth          # Tokens with AuthN tests
canary grep BenchParser       # Tokens with parser benchmarks
```

**Find by Requirement:**
```bash
canary grep {{.ReqID}}-API-120    # All tokens for {{.ReqID}}-API-120
```

## Guidelines

- **Broad Search**: Search across all fields for maximum coverage
- **Case-Insensitive**: Make search user-friendly
- **Context**: Show what field matched the pattern
- **Navigation**: Provide file:line references
- **Refinement**: Suggest ways to narrow results if too many
- **Grouping**: Offer grouping options for better organization
- **Database Required**: Suggest `canary index` if database missing
