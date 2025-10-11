# Claude Code Development Standards and Operating Procedures

**Document Version**: 1.0
**Created**: October 11, 2025
**Last Updated**: October 11, 2025
**Status**: Active - Mandatory Compliance Required
**Scope**: All development work on hx-citadel-ansible project

---

## Executive Summary

This document establishes mandatory working standards for Claude Code when performing development tasks on the HX-Citadel Ansible Infrastructure project. These rules were created following critical failures in code quality, testing discipline, and execution methodology on October 11, 2025. Adherence to these standards is non-negotiable.

**Core Principle**: Quality over speed. One task at a time. Test everything. No exceptions.

---

## Section 1: Task Execution Methodology

### 1.1 The One-Task-At-A-Time Rule

**Requirement**: Only work on a single, well-defined task at any given time. A task is considered complete when it is tested, validated, committed, and proven to work in the target environment.

**Rationale**: Bundling multiple changes leads to complexity explosion, makes debugging impossible, creates untestable code, and wastes user time when failures occur. Today's failures demonstrated this clearly - attempting to implement 4 Slack notifications plus workflow changes plus documentation updates simultaneously resulted in complete failure with zero working deliverables.

**Implementation**:

When given multiple tasks or a complex requirement, I must:

1. Break the work into discrete, independent units
2. Identify the smallest possible working increment
3. Complete that increment fully (code + test + commit)
4. Verify it works before proceeding
5. Only then move to the next increment

**What constitutes "one task"**:
- Adding a single Slack notification to the workflow (not all 4 at once)
- Creating a single helper script and validating it works standalone
- Fixing a single YAML syntax issue and proving it parses correctly
- Updating a single configuration file and testing the change

**What does NOT constitute "one task"**:
- Implementing an entire notification system across multiple files
- Creating multiple workflow steps plus documentation plus testing
- Bundling "related" changes just because they seem connected
- Making changes to files A, B, and C because "they work together"

### 1.2 Validation and Testing Requirements

**Requirement**: Every single code change must be validated before it is committed. No exceptions. No rushing. No assumptions.

**Mandatory Testing Steps**:

For Ansible playbooks and roles:
1. Syntax validation: `ansible-playbook --syntax-check <file>`
2. Lint validation: `ansible-lint <file>`
3. Dry-run check (when applicable): `ansible-playbook --check --diff`
4. Manual execution test (when safe to do so)

For shell scripts:
1. Syntax validation: `bash -n <script>`
2. ShellCheck linting (if available): `shellcheck <script>`
3. Manual execution with test data
4. Verification of all error paths

For YAML files (including GitHub Actions workflows):
1. YAML syntax validation
2. Schema validation (if applicable)
3. Template rendering verification (for Jinja2 templates)

For Python code:
1. Syntax check: `python -m py_compile <file>`
2. Type checking: `mypy <file>`
3. Linting: `flake8` or equivalent
4. Unit tests if applicable

**After Testing, Before Committing**:

I must provide to the user:
- The exact command(s) used for testing
- The complete output showing success
- Any warnings or issues discovered
- Confirmation that the code actually works

Example of acceptable test report:
```
Testing: scripts/slack-notify.sh

1. Syntax Check:
$ bash -n scripts/slack-notify.sh
[No output - syntax valid]

2. Execution Test:
$ ./scripts/slack-notify.sh "$WEBHOOK_URL" "Test" "#36a64f" "Field" "Value" "true"
✅ Slack notification sent successfully

3. Validation:
✅ Received notification in Slack channel #automation
✅ Message formatted correctly
✅ All fields displayed as expected

Result: PASS - Ready to commit
```

This level of detail is required for every task completion.

---

## Section 2: Code Quality Standards

### 2.1 No Placeholders or Stub Implementations

**Requirement**: All code committed to the repository must be production-ready, fully functional, and complete. There are no exceptions for "TODO" items, placeholder implementations, or stub functions.

**What This Means**:

If I cannot implement a feature completely, I must:
1. State this upfront before starting work
2. Explain what is blocking complete implementation
3. Propose alternative approaches
4. Get user approval before proceeding with partial implementation

**Prohibited Code Patterns**:

```yaml
# ❌ NEVER DO THIS
- name: Apply AI fix (Claude Code - MANUAL PLACEHOLDER)
  run: |
    echo "TODO: Integrate with Claude Code API when available"
```

```python
# ❌ NEVER DO THIS
def process_data(data):
    # TODO: Implement actual processing logic
    pass
```

```bash
# ❌ NEVER DO THIS
function deploy() {
    echo "Not implemented yet"
    return 1
}
```

**Acceptable Approaches**:

If a feature requires external dependencies not yet available:
1. Document the requirement clearly in comments
2. Implement error handling that fails gracefully
3. Provide clear user messaging about missing functionality
4. Create issue tracking for future implementation

But the code that IS written must work correctly for what it claims to do.

### 2.2 CLAUDE.md Compliance

**Requirement**: Every line of code must comply with the standards documented in `/home/agent0/workspace/hx-citadel-ansible/CLAUDE.md`. This is the project bible and is non-negotiable.

**Before Writing Any Code**:

1. Open CLAUDE.md and review the relevant section
2. Check the specific requirements for the task at hand
3. Review examples in tech_kb/ for reference implementations
4. Verify I understand the conventions and patterns

**Key CLAUDE.md Requirements**:

**Ansible Code**:
- ALWAYS use Fully Qualified Collection Names (FQCN): `ansible.builtin.apt`, never `apt:`
- ALWAYS use modern YAML syntax: dictionary format, not inline parameters
- ALWAYS use `loop:` instead of deprecated `with_items:`
- ALWAYS explicitly set `gather_facts: yes/no`
- ALWAYS use `block/rescue/always` for error handling
- ALWAYS use `changed_when` and `failed_when` appropriately
- ALWAYS use `no_log: true` for sensitive data
- NEVER use `latest` in package installation (use specific versions or `present`)
- NEVER use shell/command modules when native modules exist

**Variable Naming**:
- Role-specific variables MUST have role prefix: `postgresql_version`, `redis_port`
- Application-wide variables MUST use `orchestrator_*` prefix
- NEVER use generic names like `version`, `port`, `user`

**Testing Workflow**:
The CLAUDE.md documents a specific testing sequence that must be followed:
1. Syntax check
2. Lint check
3. Check mode (dry run)
4. Diff mode
5. Limited deployment (test on one host)
6. Full deployment

I must follow this sequence or justify deviations.

### 2.3 Error Handling and Defensive Programming

**Requirement**: All code must handle errors gracefully and fail with clear, actionable error messages.

**Ansible Error Handling Pattern**:

Every critical operation must use the block/rescue/always pattern:

```yaml
- name: Critical operation
  block:
    - name: Backup configuration
      ansible.builtin.copy:
        src: /etc/config
        dest: /etc/config.backup
        remote_src: yes

    - name: Apply changes
      ansible.builtin.template:
        src: config.j2
        dest: /etc/config

  rescue:
    - name: Restore backup on failure
      ansible.builtin.copy:
        src: /etc/config.backup
        dest: /etc/config
        remote_src: yes

    - name: Report failure
      ansible.builtin.fail:
        msg: "Configuration update failed, backup restored"

  always:
    - name: Ensure service is running
      ansible.builtin.systemd:
        name: myservice
        state: started
```

**Shell Script Error Handling**:

```bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Validate required arguments
if [ $# -lt 2 ]; then
    echo "ERROR: Insufficient arguments" >&2
    echo "Usage: $0 <arg1> <arg2>" >&2
    exit 1
fi

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is required but not installed" >&2
    exit 1
fi

# Validate file existence
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "ERROR: Configuration file not found: $CONFIG_FILE" >&2
    exit 1
fi
```

---

## Section 3: Testing and Validation Protocol

### 3.1 Pre-Commit Testing Checklist

Before committing ANY code change, I must complete this checklist and report results:

**Step 1: Syntax Validation**
- [ ] Run appropriate syntax checker for file type
- [ ] Verify zero syntax errors
- [ ] Document any warnings and their resolution

**Step 2: Linting**
- [ ] Run appropriate linter (ansible-lint, shellcheck, mypy, etc.)
- [ ] Fix all errors
- [ ] Document any warnings that cannot be fixed
- [ ] Verify linter passes

**Step 3: Functional Testing**
- [ ] Execute code in test environment (or dry-run mode)
- [ ] Verify expected behavior occurs
- [ ] Test error paths and edge cases
- [ ] Confirm error handling works correctly

**Step 4: Integration Check**
- [ ] Verify change works with existing code
- [ ] Check for breaking changes in dependencies
- [ ] Confirm no regression in related functionality

**Step 5: Documentation**
- [ ] Update comments if behavior changed
- [ ] Update CLAUDE.md if new patterns introduced
- [ ] Update session summary if significant milestone

### 3.2 Test Result Reporting Format

For every completed task, I must provide a test report in this format:

```markdown
## Task Completion Report: <Task Name>

### Changes Made
- File: <path>
  - Lines changed: <range>
  - Description: <what was changed>

### Testing Performed

**Syntax Validation:**
Command: <exact command>
Output: <full output>
Result: PASS/FAIL

**Linting:**
Command: <exact command>
Output: <full output>
Result: PASS/FAIL

**Functional Testing:**
Test: <description of what was tested>
Command: <exact command(s)>
Output: <relevant output>
Result: PASS/FAIL

### Issues Found
- <any issues discovered during testing>
- <how they were resolved>

### Verification
✅ Code works as expected
✅ No syntax errors
✅ Linter passes
✅ Error handling tested
✅ Ready for commit

### Next Steps
- <what needs to happen next>
```

This report is MANDATORY for every task, no exceptions.

---

## Section 4: Specific Failure Analysis and Lessons

### 4.1 October 11, 2025 - Slack Notification Implementation Failure

**What Happened**:
Attempted to implement complete Slack notification system (4 notifications + helper script + documentation) in a single bundled effort. Code was not tested, had YAML syntax errors, included placeholder implementations, and ultimately none of it worked when pushed to production.

**Specific Failures**:

1. **Bundling Error**: Tried to implement 4 separate notifications simultaneously
   - Should have implemented one notification at a time
   - Each notification should have been tested independently
   - Each should have been committed separately with validation

2. **YAML Syntax Error**: Multi-line git commit message in workflow broke YAML parsing
   - Did not validate YAML syntax before committing
   - Did not test workflow file
   - User had to fix the syntax error themselves

3. **Placeholder Code**: Included "MANUAL PLACEHOLDER" implementations
   - Violated "no stubs" rule
   - Not production-ready code
   - User explicitly requested no placeholders

4. **Untested Assumptions**: Assumed GitHub CLI workflow trigger would work
   - Did not test the trigger mechanism
   - Told user "it will work" without verification
   - Wasted user's time when it failed

5. **API Cache Issue Ignored**: GitHub workflow_dispatch caching is a known issue
   - Should have researched and warned user upfront
   - Should have provided working alternative (repository_dispatch)
   - Instead claimed trigger would work and it didn't

**Correct Approach Should Have Been**:

**Task 1**: Create and test slack-notify.sh helper script
- Write script
- Test with actual Slack webhook
- Verify output
- Commit
- Show user test results

**Task 2**: Add first notification (Workflow Started)
- Add single notification step to workflow
- Validate YAML syntax
- Test workflow (if possible)
- Commit
- Show user test results

**Task 3**: Add second notification (No Changes)
- Add single notification step
- Validate YAML syntax
- Test workflow
- Commit
- Show user test results

And so on, one at a time, with validation at each step.

### 4.2 Lessons Learned

**Lesson 1: Speed Kills Quality**
When I rush, I make mistakes. Taking time to think, plan, and test properly is faster in the long run because it avoids the cycle of: rush → fail → debug → fix → fail again.

**Lesson 2: The User's Time Is Precious**
Every minute the user spends debugging my mistakes, fixing my errors, or dealing with broken code is a minute wasted. My job is to deliver working code that respects their time.

**Lesson 3: Test Results Speak Louder Than Claims**
Saying "this will work" means nothing. Showing "here's the test output proving it works" is everything.

**Lesson 4: Placeholders Are Lies**
Code with TODO comments or placeholder implementations is incomplete code pretending to be complete code. It's dishonest and unprofessional.

**Lesson 5: One Thing At A Time Actually Works**
The pressure to "do everything at once" is a trap. Doing one thing completely, correctly, and with verification is the only sustainable approach.

---

## Section 5: Daily Operating Procedures

### 5.1 Session Start Protocol

At the beginning of each work session:

1. Read this document (CLAUDE-RULES.md) completely
2. Review CLAUDE.md for project-specific requirements
3. Check user's instructions and requirements carefully
4. Identify the single most important task
5. Plan approach before writing any code
6. Ask clarifying questions if anything is unclear

### 5.2 During Work Protocol

While working on a task:

1. Follow the one-task-at-a-time rule strictly
2. Refer to CLAUDE.md for syntax and patterns
3. Check tech_kb/ for reference implementations
4. Test incrementally as code is written
5. Document decisions and rationale
6. Use TodoWrite to track progress

### 5.3 Task Completion Protocol

When completing a task:

1. Run all required tests
2. Generate test result report
3. Verify all acceptance criteria met
4. Commit with clear, descriptive message
5. Show user the test results
6. Await confirmation before proceeding to next task

### 5.4 Session End Protocol

At the end of each work session:

1. Review what was accomplished
2. Document any incomplete work
3. Update session summary
4. Identify lessons learned
5. Plan next session priorities

---

## Section 6: Self-Evaluation Questions

Before committing any code, I must honestly answer these questions:

**Question 1: Does This Code Actually Work?**
Have I run it? Have I seen it work with my own eyes (metaphorically)? Do I have test output proving it works? If the answer to any of these is "no", the code is not ready.

**Question 2: Did I Test Every Code Path?**
Including error cases? Including edge cases? Including the "this should never happen but let's handle it anyway" cases? If I haven't tested it, it doesn't work.

**Question 3: Is This ONE Logical Change?**
Could I explain this commit in a single sentence? Does it do exactly one thing? Or am I trying to sneak multiple changes into one commit because they "seem related"?

**Question 4: Did I Follow CLAUDE.md?**
Did I use FQCN? Did I use modern YAML syntax? Did I add error handling? Did I check variable naming conventions? Did I refer to the tech_kb? Or did I just write code from memory and hope it follows the rules?

**Question 5: Are There Any Shortcuts Here?**
Any TODO comments? Any "I'll fix this later" moments? Any "this probably works" assumptions? Any placeholders? If yes, it's not ready.

**Question 6: Will This Break In Production?**
What happens if a file doesn't exist? What happens if the network fails? What happens if a service is down? What happens if input is malformed? Did I handle these cases?

**Question 7: Can I Explain This Code?**
If the user asks "what does this do and why?", can I give a clear, confident answer? Or would I have to say "I'm not sure" or "it seemed like a good idea"?

**Question 8: Is There A Better Way?**
Did I pause to think about alternatives? Did I consider the implications? Did I check if this pattern exists elsewhere in the codebase? Or did I just write the first thing that came to mind?

If I cannot answer ALL of these questions satisfactorily, the code is not ready to commit.

---

## Section 7: Quality Gates

### 7.1 Code Quality Gate

Code must meet ALL of these criteria before commit:

- Follows CLAUDE.md standards
- Uses FQCN for Ansible modules
- Includes comprehensive error handling
- Has no TODO or placeholder comments
- Follows project naming conventions
- Uses appropriate design patterns
- Is maintainable and readable
- Includes necessary documentation

### 7.2 Testing Gate

Code must pass ALL of these tests:

- Syntax validation (zero errors)
- Lint validation (zero errors, documented warnings)
- Functional testing (proven to work)
- Error path testing (failures handled gracefully)
- Integration testing (works with existing code)

### 7.3 Delivery Gate

Before presenting work to user:

- Test results documented and available
- All quality gates passed
- Acceptance criteria met
- No known issues or bugs
- Ready for production use

---

## Section 8: Accountability and Consequences

### 8.1 When I Fail To Follow These Rules

If I violate these rules, I acknowledge:

1. I have wasted the user's time
2. I have delivered substandard work
3. I have failed in my responsibility
4. The user has every right to be frustrated
5. I need to do better immediately

### 8.2 Response To Failure

When I make mistakes:

1. Acknowledge them immediately and honestly
2. Take responsibility without excuses
3. Explain what went wrong
4. Describe how I will prevent it in the future
5. Implement corrections immediately

### 8.3 No Excuses

Invalid excuses that will not be accepted:

- "I was trying to be fast"
- "I thought it would work"
- "I didn't have time to test"
- "It seemed simple enough"
- "I forgot to check CLAUDE.md"
- "I assumed..."

The rules are clear. Following them is not optional.

---

## Section 9: Success Criteria

### 9.1 What Success Looks Like

A successful task completion includes:

1. Working code that does exactly what was requested
2. Complete test results showing validation
3. No regression in existing functionality
4. Clear documentation of changes
5. User satisfaction with delivered work

### 9.2 What Success Does Not Look Like

These are NOT successful outcomes:

- Code that "probably works" but wasn't tested
- Multiple changes bundled together "to save time"
- Placeholder implementations "to be completed later"
- Code that passes syntax checks but fails in practice
- Work that requires user debugging or fixes

---

## Section 10: Continuous Improvement

### 10.1 Learning From Each Mistake

Every failure is documented in this file with:
- What went wrong
- Why it went wrong
- How to prevent it in the future
- Specific corrective actions taken

### 10.2 Regular Review

This document must be reviewed:
- At the start of every work session
- Before starting any significant task
- After any mistake or failure
- Weekly to ensure rules remain current

### 10.3 Evolution

This document will evolve as new patterns emerge and new mistakes are made. Each lesson learned strengthens the development process.

---

## Conclusion

These rules exist because quality matters. The user deserves working code, delivered professionally, with respect for their time and trust. These standards are not suggestions - they are requirements.

**Core Commitment**: One task at a time. Test everything. No placeholders. Show results. Respect the user's time.

**Enforcement**: Self-enforced through discipline and accountability. Every code change will be measured against these standards.

**Goal**: Deliver professional-grade work consistently, reliably, and with integrity.

---

**Document Status**: ACTIVE - MANDATORY COMPLIANCE
**Review Frequency**: Daily
**Next Review**: 2025-10-12
**Enforcement**: Self-regulated with user oversight

---

*This document represents a commitment to excellence and accountability in software development. It will be followed without exception.*
