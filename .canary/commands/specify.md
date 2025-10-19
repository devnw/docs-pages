---
description: Create a new CANARY requirement specification from a natural language feature description
scripts:
  sh: .canary/scripts/create-new-requirement.sh "$ARGUMENTS"
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/canary.specify` is the feature description.

Given that feature description, do this:

1. **Generate requirement ID**:
   - Scan existing `.canary/specs/` directory for highest {{.ReqID}}-<ASPECT>-### number
   - Assign next sequential ID (e.g., if {{.ReqID}}-<ASPECT>-105 exists, use {{.ReqID}}-<ASPECT>-106)
   - Format: {{.ReqID}}-<ASPECT>-XXX (zero-padded 3 digits)

2. **Generate concise feature name** (2-4 words):
   - Extract meaningful keywords from description
   - Use action-noun format (e.g., "user-authentication", "data-validation")
   - Keep technical terms (OAuth2, JWT, API, etc.)

3. **Run the script** `.canary/scripts/create-new-requirement.sh --req-id {{.ReqID}}-<ASPECT>-XXX --feature "name"`:
   - Creates `.canary/specs/{{.ReqID}}-<ASPECT>-XXX-feature-name/` directory
   - Initializes `spec.md` from template
   - Returns SPEC_FILE path

4. **Create the specification**:
   - Load `templates/spec-template.md` to understand required sections
   - Focus on WHAT users need and WHY (not HOW to implement)
   - Fill required sections:
     - Feature Overview
     - User Stories
     - Functional Requirements
     - Success Criteria (measurable, technology-agnostic)
     - Assumptions and Constraints
   - Limit [NEEDS CLARIFICATION] markers to maximum 3 critical items

5. **Generate CANARY token**:
   ```
   // CANARY: REQ={{.ReqID}}-<ASPECT>-XXX; FEATURE="FeatureName"; ASPECT=API; STATUS=STUB; UPDATED=YYYY-MM-DD
   ```
   - Determine appropriate ASPECT based on feature description
   - Set STATUS=STUB (will be promoted when implemented)
   - Use current date for UPDATED field

6. **Document where to place token**:
   - Suggest file/location in codebase where token should go
   - Provide example of token placement

7. **Create requirement tracking entry**:
   - Update `.canary/requirements.md` (create if doesn't exist)
   - Add entry: `- [ ] {{.ReqID}}-<ASPECT>-XXX - FeatureName (STATUS=STUB)`

8. **Report completion**:
   - Requirement ID and feature name
   - Spec file path
   - CANARY token (ready to paste into code)
   - Suggested code location
   - Next steps: Use `/canary.plan` to create implementation plan

## Quality Validation

After creating the spec, validate:

- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] All requirements are testable and unambiguous
- [ ] Success criteria are measurable and technology-agnostic
- [ ] Maximum 3 [NEEDS CLARIFICATION] markers
- [ ] All acceptance scenarios defined
- [ ] Feature scope clearly bounded

## Example Flow

User input: "Add user authentication with email/password and OAuth2 support"

1. Generate ID: {{.ReqID}}-<ASPECT>-107
2. Feature name: "user-authentication"
3. Create: `.canary/specs/{{.ReqID}}-<ASPECT>-107-user-authentication/spec.md`
4. CANARY token:
   ```
   // CANARY: REQ={{.ReqID}}-<ASPECT>-107; FEATURE="UserAuthentication"; ASPECT=API; STATUS=STUB; UPDATED=2025-10-16
   ```
5. Suggest placement:
   ```go
   // File: src/auth/auth.go
   // CANARY: REQ={{.ReqID}}-API-107; FEATURE="UserAuthentication"; ASPECT=API; STATUS=STUB; UPDATED=2025-10-16
   package auth

   func Authenticate(credentials Credentials) (*Session, error) {
       // Implementation will go here
   }
   ```

## Guidelines

- **Specification Focus**: WHAT and WHY, not HOW
- **Measurable Outcomes**: "Users can login in < 3 seconds" not "JWT token generation"
- **Technology Agnostic**: Don't specify frameworks, databases, or languages
- **Token Placement**: Suggest logical location in codebase based on ASPECT
- **Status Progression**: Starts as STUB, becomes IMPL when implemented, TESTED when tests added
