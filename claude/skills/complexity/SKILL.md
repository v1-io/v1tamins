---
name: complexity
description: Use when reducing cognitive complexity, flattening nested code, or simplifying functions. Triggers on "reduce complexity", "simplify", "too nested".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
---

# Reduce Cognitive Complexity

Refactor functions to reduce cognitive complexity score while maintaining identical behavior.

## Usage

```
/complexity [file:function]
```

**Examples:**
```bash
/complexity                                    # Analyze current diff
/complexity services/analyst/core/query.py    # Analyze specific file
/complexity query.py:process_result           # Analyze specific function
```

## Understanding Cognitive Complexity

**What increments complexity (+1 each):**
- Control flow: `if`, `else if`, `else`, ternary operators
- Loops: `for`, `foreach`, `while`, `do while`
- Exception handling: `catch`
- Switch statements: `switch`, `case`
- Jump statements: `goto`, `break`, `continue` (labeled)
- Binary logical operators: `&&`, `||` in conditions
- Recursive function calls

**Nesting multiplier:**
- Each nesting level adds +1 to structures nested inside
- Deeper nesting = harder to understand

**What's free (no increment):**
- Function/method calls (encourages extraction)
- Simple return statements

**Target:** Keep cognitive complexity **under 15** per function

## Refactoring Strategies

### 1. Return Early (Reduce Nesting)
```python
# Before: Complexity 6
def calculate(data):
    if data is not None:  # +1
        total = 0
        for item in data: # +1 +1 (nested)
            if item > 0:  # +1 +2 (nested)
                total += item * 2
        return total

# After: Complexity 4
def calculate(data):
    if data is None:      # +1
        return None
    total = 0
    for item in data:     # +1
        if item > 0:      # +1 +1 (nested)
            total += item * 2
    return total
```

### 2. Extract Complex Conditions
```python
# Before: Complexity 5
def process_eligible_users(users):
    for user in users:             # +1
        if ((user.is_active and    # +1 +1 +1 +1
            user.has_profile) or
            user.age > 18):
            user.process()

# After: Complexity 3
def process_eligible_users(users):
    for user in users:             # +1
        if is_eligible_user(user): # +1 +1
            user.process()

def is_eligible_user(user):
    return (user.is_active and user.has_profile) or user.age > 18
```

### 3. Break Down Large Functions
Extract logical blocks into separate functions with single responsibilities.

## Process

1. **Analyze** the target function:
   - Current complexity score
   - What's contributing to it
   - Deeply nested structures (2+ levels)
   - Complex boolean conditions

2. **Preserve existing tests** - understand coverage before changes

3. **Refactor** using strategies above:
   - Start with early returns to flatten nesting
   - Extract complex conditions into named helpers
   - Break down into smaller functions if still above target
   - Use clear, descriptive names

4. **Verify behavior** - run existing tests

5. **Add tests if needed** - for new helper functions with complex logic

## Critical Requirements

- ✅ Maintain **identical behavior**
- ✅ Follow **existing code patterns**
- ✅ Use **descriptive names** for extracted functions
- ✅ Keep complexity **under 15** per function
- ✅ **Run tests** to verify correctness
