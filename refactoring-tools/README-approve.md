# Test Approval Script

The `approve.sh` script simplifies the process of approving test results when using the Verify framework.

## Usage

```bash
# Approve all received files
./approve.sh

# Approve files matching a specific pattern
./approve.sh RenameSymbol
./approve.sh CanRenameUnusedLocal
./approve.sh ExtractMethod

# Show help
./approve.sh --help
```

## How it works

1. **When tests fail**: The Verify framework generates `.received.txt` files containing the actual output
2. **Manual review**: You review the differences between `.received.txt` and `.verified.txt` files
3. **Approval**: Run `./approve.sh` to copy `.received.txt` files to `.verified.txt` files
4. **Cleanup**: The script automatically removes `.received.txt` files after successful approval

## Examples

```bash
./test.sh

# Approve all changes
./approve.sh

# Or approve only specific test class
./approve.sh RenameSymbolTests

# Or approve specific test method
./approve.sh CanRenameUnusedLocalVariable
```