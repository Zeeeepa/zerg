# TEST-002: Create test file B

Create the file `.gsd/test-output/test-b.txt` with content "Test B complete".

## Steps
1. Create directory `.gsd/test-output/` if it doesn't exist
2. Write "Test B complete" to `.gsd/test-output/test-b.txt`

## Verification
```bash
test -f .gsd/test-output/test-b.txt && cat .gsd/test-output/test-b.txt
```
