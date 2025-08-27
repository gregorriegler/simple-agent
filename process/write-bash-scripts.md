STARTER_SYMBOL=📜

Use #!/usr/bin/env bash as shebang.
Always use set -euo pipefail for safety and debugging.
Keep scripts minimal: avoid comments or echoes.
Only do minimal input validation; print a usage message to stderr and exit if inputs are missing or invalid.
Use paths that work on all computers, not just this one.
Do not check for installed commands if failure will be obvious on use.
Make script executable: chmod +x <script>.
Prefer concise, direct logic over verbosity.
