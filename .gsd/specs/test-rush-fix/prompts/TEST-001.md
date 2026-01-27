# TEST-001: Create test file A

Create the file `.gsd/test-output/test-a.txt` with content "Test A complete".

## Steps
1. Create directory `.gsd/test-output/` if it doesn't exist
2. Write "Test A complete" to `.gsd/test-output/test-a.txt`

## Verification
```bash
test -f .gsd/test-output/test-a.txt && cat .gsd/test-output/test-a.txt
```
