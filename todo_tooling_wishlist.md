# AI Coding Assistant - Todo Tooling Wishlist

## File System & Navigation

### `find`
Search for files by name, type, or content patterns
- Would complement `ls` for discovering files in large codebases
- Example: `find . -name "*.py"` or `find . -type f -name "*test*"`

### `grep`
Search file contents across multiple files
- Essential for understanding code patterns and finding usage
- Example: `grep -r "function_name" .` or `grep -n "TODO" *.py`

### `tree`
Display directory structure visually
- Better overview of project structure than recursive `ls`
- Example: `tree -L 2` to see 2 levels deep

## File Operations

### `mv`
Move or rename files
- Currently can only create new files, not reorganize
- Example: `mv old_name.py new_name.py`

### `cp`
Copy files or directories
- Useful for templates or duplicating test cases
- Example: `cp template.py new_feature.py`

### `rm`
Delete files or directories
- Currently no way to clean up unwanted files
- Example: `rm temp_file.txt` or `rm -r old_directory/`

## Code Analysis

### `ast-query`
Query code structure using AST patterns
- Find all classes, functions, imports, etc.
- Example: `ast-query --find-functions myfile.py`

### `code-metrics`
Get code complexity and quality metrics
- Cyclomatic complexity, line counts, function sizes
- Example: `code-metrics analyze src/`

### `dependency-graph`
Visualize or query module dependencies
- Understand architecture and find circular dependencies
- Example: `dependency-graph --check-cycles .`

## Testing & Quality

### `test-runner`
Smart test execution with filtering
- Run specific tests, failed tests, or tests related to changes
- Example: `test-runner --related-to myfile.py`

### `coverage`
Code coverage analysis
- See what's tested and what's not
- Example: `coverage report --missing`

### `lint`
Static analysis and style checking
- Catch potential issues before running code
- Example: `lint --errors-only src/`

## Git Integration

### `git-status`
Enhanced git status with diff preview
- See what's changed before committing
- Example: `git-status --short`

### `git-blame`
Find when and why code was changed
- Understand history and context
- Example: `git-blame filename.py 10-20`

### `git-log`
Search commit history
- Find related changes or regression points
- Example: `git-log --grep "feature" --oneline`

## Context & Memory

### `remember`
Store context between interactions
- Remember user preferences, project conventions
- Example: `remember "use pytest fixtures for test data"`

### `recall`
Query stored context
- Retrieve previously stored information
- Example: `recall test-conventions`

### `project-summary`
Generate/update project overview
- Understand project structure, key files, architecture
- Example: `project-summary --update`

## Debugging

### `stack-trace-analyze`
Parse and explain stack traces
- Identify root cause from error output
- Example: `stack-trace-analyze error.log`

### `breakpoint-inject`
Add debugging statements temporarily
- Insert print/logging without manual editing
- Example: `breakpoint-inject myfile.py:42 --print-locals`

## Multi-file Operations

### `bulk-edit`
Apply same edit across multiple files
- Rename symbols, update imports, etc.
- Example: `bulk-edit --rename old_name new_name src/`

### `diff-files`
Compare two files or versions
- Understand what changed between versions
- Example: `diff-files file1.py file2.py`

### `merge-check`
Preview merge conflicts
- See potential conflicts before committing
- Example: `merge-check main feature-branch`

## Documentation

### `generate-docs`
Auto-generate documentation from code
- API docs, README sections, etc.
- Example: `generate-docs src/ --format markdown`

### `explain-code`
Get detailed explanation of complex code
- Understand legacy or unclear code
- Example: `explain-code myfile.py:50-75`

## Performance

### `profile`
Performance profiling
- Find bottlenecks and slow functions
- Example: `profile script.py --top 10`

### `benchmark`
Run performance benchmarks
- Compare implementations or track performance
- Example: `benchmark --compare old_version.py new_version.py`
