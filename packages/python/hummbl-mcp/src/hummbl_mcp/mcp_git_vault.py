import sys
import os
import json
import ntpath
import subprocess
import re
import traceback
from pathlib import Path

from hummbl_mcp._constants import MCP_PROTOCOL_VERSION

try:
    from hummbl_mcp._services import machine_config as _mc
except ImportError:
    _mc = None  # type: ignore[assignment]

# Redirect sys.stdout to sys.stderr so any unwanted print() statements don't corrupt JSON-RPC
original_stdout = sys.stdout
sys.stdout = sys.stderr

def log(msg):
    sys.stderr.write(f"[mcp-git-vault] {msg}\n")
    sys.stderr.flush()

# Define tools
TOOLS = [
    {
        "name": "vault_git_status",
        "description": "Retrieve repository status in a porcelain clean machine-readable format.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "vault_git_diff",
        "description": "Retrieve unified diff of modifications for specified file paths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional file paths to diff."
                },
                "staged": {
                    "type": "boolean",
                    "description": "If true, diff staged changes."
                }
            }
        }
    },
    {
        "name": "vault_git_stage",
        "description": "Stage files for commit (equivalent to git add). Only permits paths inside workspace. Wildcards are banned.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Explicit relative paths to stage. Wildcard '*' is banned."
                }
            },
            "required": ["paths"]
        }
    },
    {
        "name": "vault_git_commit",
        "description": "Commit staged changes, enforcing Conventional Commit formatting and injecting standard attribution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Commit message, e.g. 'feat/gemini/add-mcp: message'."
                },
                "co_authors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of co-author lines (e.g. 'Co-authored-by: Name <email>')."
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "vault_git_branch",
        "description": "Create or list development branches matching authorized pattern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "create"],
                    "description": "Action to perform."
                },
                "branch_name": {
                    "type": "string",
                    "description": "The branch name to create (required if action is 'create'). Must match type/agent/short-desc pattern."
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "vault_git_worktree_create",
        "description": "Create a secure git worktree for isolated task execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Target worktree directory path. Must be under '.gemini/antigravity-cli/worktrees/'."
                },
                "branch_name": {
                    "type": "string",
                    "description": "Branch to check out in the worktree."
                }
            },
            "required": ["path", "branch_name"]
        }
    },
    {
        "name": "vault_git_push",
        "description": "Push the current branch to origin. Force push and no-verify are blocked.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote name (defaults to 'origin')."
                },
                "set_upstream": {
                    "type": "boolean",
                    "description": "If true, set upstream branch."
                }
            }
        }
    }
]

def get_git_root():
    try:
        res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return os.path.abspath(res.stdout.strip())
    except Exception as e:
        log(f"Error getting git root: {e}")
        return os.path.abspath(os.getcwd())

def check_safety_guards(args):
    blocked = ["--no-verify", "--force", "-f", "--hard"]
    for arg in args:
        for b in blocked:
            if b == arg or arg.startswith(b + "="):
                return True
    return False

def _looks_windows_path(value):
    text = str(value)
    return bool(re.match(r"^[A-Za-z]:[\\/]", text)) or "\\" in text

def resolve_inside(root, path):
    if _looks_windows_path(root) or _looks_windows_path(path):
        root_path = ntpath.normcase(ntpath.abspath(str(root)))
        if ntpath.isabs(str(path)):
            candidate = str(path)
        else:
            candidate = ntpath.join(root_path, str(path))
        candidate_path = ntpath.normcase(ntpath.abspath(candidate))
        try:
            if ntpath.commonpath([root_path, candidate_path]) != root_path:
                return None
        except ValueError:
            return None
        return ntpath.normpath(candidate_path)

    root_path = Path(root).resolve(strict=False)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root_path / candidate
    candidate = candidate.resolve(strict=False)
    try:
        candidate.relative_to(root_path)
    except ValueError:
        return None
    return str(candidate)

def git_config_value(name):
    try:
        res = subprocess.run(["git", "config", "--get", name], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip() or None
    except Exception as e:
        log(f"git config lookup skipped for {name}: {e}")
    return None

def check_windows_headless_locks():
    # Pre-flight SSH keys check
    try:
        # Run standard git check or ssh-add
        res = subprocess.run(["ssh-add", "-l"], capture_output=True, text=True)
        if res.returncode != 0:
            return "SSH_AGENT_LOCKED", "SSH keys are locked or agent is not running. Please run 'ssh-add' in your Git Bash terminal."
    except Exception as e:
        log(f"ssh-add check skipped: {e}")

    # Pre-flight GPG check
    try:
        proc = subprocess.Popen(["gpg", "--clearsign"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate(input="test\n", timeout=3)
        if proc.returncode != 0:
            return "GPG_KEYS_LOCKED", f"GPG key is locked or passphrase is required. Error: {err.strip()}"
    except subprocess.TimeoutExpired:
        return "GPG_KEYS_LOCKED", "GPG signature check timed out. Keyring is locked or prompting for passphrase."
    except Exception as e:
        log(f"GPG check skipped: {e}")

    return None, None

def get_attributed_env():
    env = os.environ.copy()
    author_name = env.get("MCP_GIT_AUTHOR_NAME") or env.get("GIT_AUTHOR_NAME") or git_config_value("user.name")
    author_email = env.get("MCP_GIT_AUTHOR_EMAIL") or env.get("GIT_AUTHOR_EMAIL") or git_config_value("user.email")
    committer_name = env.get("MCP_GIT_COMMITTER_NAME") or env.get("GIT_COMMITTER_NAME") or author_name
    committer_email = env.get("MCP_GIT_COMMITTER_EMAIL") or env.get("GIT_COMMITTER_EMAIL") or author_email

    if author_name:
        env["GIT_AUTHOR_NAME"] = author_name
    if author_email:
        env["GIT_AUTHOR_EMAIL"] = author_email
    if committer_name:
        env["GIT_COMMITTER_NAME"] = committer_name
    if committer_email:
        env["GIT_COMMITTER_EMAIL"] = committer_email
    return env

def handle_git_status():
    git_root = get_git_root()
    res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=git_root)
    if res.returncode != 0:
        return {"content": [{"type": "text", "text": f"Error running git status: {res.stderr.strip()}"}], "isError": True}

    lines = []
    for line in res.stdout.splitlines():
        if len(line) >= 4:
            code = line[:2]
            file = line[3:]
            lines.append({"code": code, "file": file})

    return {"content": [{"type": "text", "text": json.dumps({"status_lines": lines}, indent=2)}], "isError": False}

def handle_git_diff(arguments):
    staged = arguments.get("staged", False)
    paths = arguments.get("paths", [])

    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")

    for p in paths:
        if "*" in p or "?" in p:
            return {"content": [{"type": "text", "text": "Wildcard characters are blocked in file paths."}], "isError": True}
        cmd.append(p)

    if check_safety_guards(cmd):
        return {"content": [{"type": "text", "text": "Destructive or bypass flags are blocked."}], "isError": True}

    git_root = get_git_root()
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=git_root)
    if res.returncode != 0:
        return {"content": [{"type": "text", "text": f"Error running git diff: {res.stderr.strip()}"}], "isError": True}

    return {"content": [{"type": "text", "text": res.stdout}], "isError": False}

def handle_git_stage(arguments):
    paths = arguments.get("paths", [])
    if not paths:
        return {"content": [{"type": "text", "text": "No paths specified to stage."}], "isError": True}

    git_root = get_git_root()
    for p in paths:
        if "*" in p or "?" in p:
            return {"content": [{"type": "text", "text": f"Wildcard '{p}' is banned. Specify paths explicitly."}], "isError": True}
        if resolve_inside(git_root, p) is None:
            return {"content": [{"type": "text", "text": f"Path '{p}' resolves outside the workspace."}], "isError": True}

    cmd = ["git", "add"] + paths
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=git_root)
    if res.returncode != 0:
        return {"content": [{"type": "text", "text": f"Error running git add: {res.stderr.strip()}"}], "isError": True}

    return {"content": [{"type": "text", "text": json.dumps({"staged_files": paths}, indent=2)}], "isError": False}

def handle_git_commit(arguments):
    message = arguments.get("message", "").strip()
    co_authors = arguments.get("co_authors", [])

    if not message:
        return {"content": [{"type": "text", "text": "Commit message is required."}], "isError": True}

    # Enforce Conventional Commit formatting
    # Regex matching type/scope format, or type/agent pattern
    commit_regex = r'^[a-zA-Z0-9_\-\/]+(\([a-zA-Z0-9_\-\/]+\))?: .+$'
    if not re.match(commit_regex, message):
        return {"content": [{"type": "text", "text": f"Commit message '{message}' does not match Conventional Commit format. Example: 'feat/gemini/add-mcp: message'."}], "isError": True}

    # Pre-flight GPG check to avoid headless hang
    err_code, err_msg = check_windows_headless_locks()
    if err_code == "GPG_KEYS_LOCKED":
        return {"content": [{"type": "text", "text": f"GPG verification failed: {err_msg}"}], "isError": True}

    # Build complete commit message with optional co-authors
    full_message = message
    if co_authors:
        full_message += "\n\n" + "\n".join(co_authors)

    git_root = get_git_root()
    env = get_attributed_env()

    cmd = ["git", "commit", "-m", full_message]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=git_root, env=env)
    if res.returncode != 0:
        return {"content": [{"type": "text", "text": f"Error running git commit: {res.stderr.strip()}"}], "isError": True}

    # Retrieve last commit SHA
    sha_res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=git_root)
    sha = sha_res.stdout.strip() if sha_res.returncode == 0 else "UNKNOWN"

    return {"content": [{"type": "text", "text": json.dumps({"commit_sha": sha, "summary": res.stdout.strip()}, indent=2)}], "isError": False}

def handle_git_branch(arguments):
    action = arguments.get("action")
    branch_name = arguments.get("branch_name", "").strip()

    git_root = get_git_root()
    if action == "list":
        res = subprocess.run(["git", "branch"], capture_output=True, text=True, cwd=git_root)
        if res.returncode != 0:
            return {"content": [{"type": "text", "text": f"Error listing branches: {res.stderr.strip()}"}], "isError": True}

        branches = []
        active_branch = ""
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("*"):
                active = line[1:].strip()
                branches.append(active)
                active_branch = active
            else:
                branches.append(line)
        return {"content": [{"type": "text", "text": json.dumps({"branches": branches, "active_branch": active_branch}, indent=2)}], "isError": False}

    elif action == "create":
        if not branch_name:
            return {"content": [{"type": "text", "text": "Branch name is required for create action."}], "isError": True}

        # Validate authorized pattern: type/agent/short-desc
        branch_regex = r'^(feat|fix|chore|docs|refactor|test)/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+$'
        if not re.match(branch_regex, branch_name):
            return {"content": [{"type": "text", "text": f"Branch name '{branch_name}' does not match authorized pattern 'type/agent/short-desc' (e.g. 'feat/gemini/git-vault')."}], "isError": True}

        cmd = ["git", "checkout", "-b", branch_name]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=git_root)
        if res.returncode != 0:
            return {"content": [{"type": "text", "text": f"Error creating branch: {res.stderr.strip()}"}], "isError": True}

        return {"content": [{"type": "text", "text": f"Successfully created and checked out branch '{branch_name}'."}], "isError": False}

    return {"content": [{"type": "text", "text": f"Unknown branch action: {action}"}], "isError": True}

def handle_git_worktree_create(arguments):
    path = arguments.get("path", "").strip()
    branch_name = arguments.get("branch_name", "").strip()

    if not path or not branch_name:
        return {"content": [{"type": "text", "text": "Both 'path' and 'branch_name' are required."}], "isError": True}

    # Enforce safe worktrees path boundary
    _home = _mc.current().home_dir if _mc else str(Path.home())
    allowed_root = f"{_home}/.gemini/antigravity-cli/worktrees/"
    resolved_path = resolve_inside(allowed_root, path)
    if resolved_path is None:
        return {"content": [{"type": "text", "text": f"Worktree path '{path}' resolves outside the allowed worktrees directory '{allowed_root}'."}], "isError": True}

    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)

    git_root = get_git_root()
    cmd = ["git", "worktree", "add", resolved_path, branch_name]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=git_root)
    if res.returncode != 0:
        return {"content": [{"type": "text", "text": f"Error creating worktree: {res.stderr.strip()}"}], "isError": True}

    return {"content": [{"type": "text", "text": json.dumps({"worktree_path": resolved_path, "status": "created"}, indent=2)}], "isError": False}

def handle_git_push(arguments):
    remote = arguments.get("remote", "origin").strip()
    set_upstream = arguments.get("set_upstream", True)

    # Pre-flight SSH agent check to prevent headless hang
    err_code, err_msg = check_windows_headless_locks()
    if err_code == "SSH_AGENT_LOCKED":
        return {"content": [{"type": "text", "text": f"SSH agent lock check failed: {err_msg}"}], "isError": True}

    git_root = get_git_root()

    # Get current branch
    branch_res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=git_root)
    if branch_res.returncode != 0 or not branch_res.stdout.strip():
        return {"content": [{"type": "text", "text": "Failed to determine current branch name."}], "isError": True}
    branch_name = branch_res.stdout.strip()

    cmd = ["git", "push"]
    if set_upstream:
        cmd += ["-u", remote, branch_name]
    else:
        cmd += [remote, branch_name]

    if check_safety_guards(cmd):
        return {"content": [{"type": "text", "text": "Push blocked: destructive force flags or verification bypasses are prohibited."}], "isError": True}

    res = subprocess.run(cmd, capture_output=True, text=True, cwd=git_root, env=get_attributed_env())
    if res.returncode != 0:
        return {"content": [{"type": "text", "text": f"Error running git push: {res.stderr.strip()}"}], "isError": True}

    return {"content": [{"type": "text", "text": json.dumps({"pushed_to": remote, "ref": branch_name}, indent=2)}], "isError": False}

# Base JSON-RPC Reader/Writer
def main():
    log("Initializing MCP Git Vault...")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                log(f"Invalid JSON input: {line}")
                continue

            # Parse JSON-RPC fields
            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            response = {"jsonrpc": "2.0"}
            if req_id is not None:
                response["id"] = req_id

            if method == "initialize":
                response["result"] = {
                    "protocolVersion": params.get("protocolVersion", MCP_PROTOCOL_VERSION),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mcp-git-vault", "version": "0.1.0"}
                }
            elif method == "notifications/initialized":
                # Initialized notification has no response
                continue
            elif method == "tools/list":
                response["result"] = {"tools": TOOLS}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                try:
                    if tool_name == "vault_git_status":
                        response["result"] = handle_git_status()
                    elif tool_name == "vault_git_diff":
                        response["result"] = handle_git_diff(arguments)
                    elif tool_name == "vault_git_stage":
                        response["result"] = handle_git_stage(arguments)
                    elif tool_name == "vault_git_commit":
                        response["result"] = handle_git_commit(arguments)
                    elif tool_name == "vault_git_branch":
                        response["result"] = handle_git_branch(arguments)
                    elif tool_name == "vault_git_worktree_create":
                        response["result"] = handle_git_worktree_create(arguments)
                    elif tool_name == "vault_git_push":
                        response["result"] = handle_git_push(arguments)
                    else:
                        response["error"] = {
                            "code": -32601,
                            "message": f"Method not found: {tool_name}"
                        }
                except Exception as ex:
                    tb = traceback.format_exc()
                    log(f"Error executing tool {tool_name}: {ex}\n{tb}")
                    response["result"] = {"content": [{"type": "text", "text": f"Internal tool execution failure: {ex}"}], "isError": True}
            else:
                response["error"] = {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }

            # Write JSON-RPC back to original stdout as a single line
            original_stdout.write(json.dumps(response) + "\n")
            original_stdout.flush()

        except Exception as e:
            tb = traceback.format_exc()
            log(f"Global loop error: {e}\n{tb}")
            break

if __name__ == "__main__":
    main()
