# Reduce Cognitive Complexity

## Goal
Refactor a function to reduce its cognitive complexity score while maintaining identical behavior and improving code readability.

## Understanding Cognitive Complexity

**What increments complexity (+1 each):**
- Control flow breaks: `if`, `else if`, `else`, ternary operators
- Loops: `for`, `foreach`, `while`, `do while`
- Exception handling: `catch`
- Switch statements: `switch`, `case`
- Jump statements: `goto`, `break`, `continue` (labeled)
- Binary logical operators: `&&`, `||` in conditions
- Recursive function calls

**Nesting multiplier:**
- Each nesting level adds +1 to structures nested inside control flow
- Deeper nesting = harder to understand

**What's free (no increment):**
- Function/method calls (encourages extraction)
- Simple return statements

**Target:** Keep cognitive complexity under 15 per function

## Refactoring Strategy

Analyze the function and apply these techniques in order:

### 1. Return Early (Reduce Nesting)
**Pattern:** Invert conditions to handle edge cases first and return immediately
```python
# Before: Complexity 6
def calculate(data):
    if data is not None:  # +1 (if)
        total = 0
        for item in data: # +1 (for) +1 (nested)
            if item > 0:  # +1 (if) +2 (nested)
                total += item * 2
        return total

# After: Complexity 4
def calculate(data):
    if data is None:      # +1 (if)
        return None
    total = 0
    for item in data:     # +1 (for)
        if item > 0:      # +1 (if) +1 (nested)
            total += item * 2
    return total
```

### 2. Extract Complex Conditions
**Pattern:** Move complex boolean logic into well-named functions
```python
# Before: Complexity 5
def process_eligible_users(users):
    for user in users:             # +1 (for)
        if ((user.is_active and    # +1 (if) +1 (nested) +1 (multiple conditions)
            user.has_profile) or   # +1 (mixed operator)
            user.age > 18):
            user.process()

# After: Complexity 3 (main function)
def process_eligible_users(users):
    for user in users:             # +1 (for)
        if is_eligible_user(user): # +1 (if) +1 (nested)
            user.process()

def is_eligible_user(user):
    return ((user.is_active and user.has_profile) or user.age > 18)
```

### 3. Break Down Large Functions
**Pattern:** Extract logical blocks into separate functions with single responsibilities
```python
# Before: Complexity 8
def process_user(user):
    if user.is_active():             # +1 (if)
        if user.has_profile():       # +1 (if) +1 (nested)
            # complex processing
        else:                        # +1 (else)
            # different processing
    else:                            # +1 (else)
        if user.has_profile():       # +1 (if) +1 (nested)
            # more processing
        else:                        # +1 (else)
            # final case

# After: Complexity 2 (main function)
def process_user(user):
    if user.is_active():             # +1 (if)
        process_active_user(user)
    else:                            # +1 (else)
        process_inactive_user(user)

def process_active_user(user):
    # Handle active user cases

def process_inactive_user(user):
    # Handle inactive user cases
```

## Implementation Steps

1. **Analyze** the target function to identify:
   - Current complexity score and what's contributing to it
   - Deeply nested structures (2+ levels)
   - Complex boolean conditions with multiple operators
   - Logical sections that could be separate functions

2. **Preserve existing tests** - Read and understand all existing test coverage before making changes

3. **Refactor** using the strategies above:
   - Start with early returns to flatten nesting
   - Extract complex conditions into named helper functions
   - Break down into smaller functions if still above target
   - Ensure each extracted function has a clear, descriptive name
   - Keep functions focused on single responsibilities

4. **Verify behavior** - Run existing tests to confirm no behavioral changes

5. **Add tests as needed**:
   - If test coverage is insufficient, add tests for edge cases
   - If you created new helper functions that handle complex logic, add unit tests for them
   - Ensure all code paths in refactored functions are tested
   - Verify that the refactoring hasn't introduced any regressions

## Critical Requirements

- ✅ Maintain **identical behavior** - no functional changes
- ✅ Follow **existing code patterns** and conventions in the codebase
- ✅ Use **descriptive names** for extracted functions that clearly convey intent
- ✅ Keep cognitive complexity **under 15** for each function
- ✅ **Run existing tests** to verify correctness after refactoring
- ✅ **Create or update tests** as needed to ensure comprehensive coverage of the refactored code
