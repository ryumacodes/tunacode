# Fix subprocess shell=True security vulnerabilities
_Started: 2025-06-24 22:04:38_
_Agent: security

[1] Analyze vulnerability in /src/tunacode/tools/run_command.py line 41: subprocess.Popen with shell=True
[2] Analyze vulnerability in /src/tunacode/cli/repl.py line 323: subprocess.run with shell=True for user shell commands
[3] Research secure alternatives: shlex.quote for shell escaping, subprocess with list args instead of shell=True
