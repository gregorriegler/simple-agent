import sys

def read_file(filename):
    """Read content from a file, handling errors gracefully."""
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filename}: {e}", file=sys.stderr)
        sys.exit(1)