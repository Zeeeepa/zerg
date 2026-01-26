# ZERG Troubleshoot

Systematic debugging with root cause analysis.

## Usage

```bash
/zerg:troubleshoot [--error "error message"]
                   [--stacktrace path/to/trace]
                   [--verbose]
```

## Four-Phase Process

### Phase 1: Symptom
Identify and parse the error:
- Error type extraction
- File and line detection
- Stack trace parsing

### Phase 2: Hypothesis
Generate possible causes:
- Based on error type
- Pattern matching
- Common issues

### Phase 3: Test
Verify hypotheses:
- Run diagnostic commands
- Check assumptions
- Narrow down cause

### Phase 4: Root Cause
Determine actual cause:
- Most likely hypothesis
- Confidence score
- Recommendation

## Pattern Detection

- Recursion errors
- Memory issues
- Connection problems
- Permission errors
- Import failures
- Type mismatches

## Examples

```bash
# Analyze error message
/zerg:troubleshoot --error "ValueError: invalid literal"

# Analyze stack trace
/zerg:troubleshoot --stacktrace trace.txt

# Verbose output
/zerg:troubleshoot --error "Error" --verbose
```

## Output

```
Diagnostic Report
========================================

Symptom: ValueError: invalid literal

Hypotheses:
  [high] ValueError in parser.py:42
  [medium] Possible type issue

Root Cause: ValueError at parser.py:42

Recommendation: Check the code at parser.py line 42
```

## Exit Codes

- 0: Root cause found
- 1: Unable to determine cause
- 2: Analysis error
