"""Runs actions inside the sandbox."""

import re
import subprocess

from .actions import Action
from .config import COMMAND_TIMEOUT, CONFIRM_COMMANDS, OUTPUT_LIMIT, SANDBOX

BLOCK_RE = re.compile(
    r"\bsudo\b|\bmkfs|:\(\)\s*\{|\b(shutdown|reboot|poweroff)\b|>\s*/dev/"
    r"|\brm\s+(-\w+\s+)*(/|~|\$HOME|\.\.)(\s|$|/)|\|\s*(ba|z)?sh\b|\bdd\s+if=|\.\./")
FENCE_RE = re.compile(r"^```[\w+-]*\n(.*?)\n?```$", re.S)


def unstar(text):
    return text.replace("{{STAR}}", "*")


def clean_content(text):
    """Strip a markdown code fence Meta AI may wrap around file contents."""
    m = FENCE_RE.match(text.strip("\n"))
    return unstar((m.group(1) if m else text).rstrip("\n")) + "\n"


def safe_path(rel):
    p = (SANDBOX / rel).resolve()
    if SANDBOX not in p.parents and p != SANDBOX:
        raise ValueError(f"path outside sandbox: {rel}")
    return p


def run_bash(cmd):
    cmd = unstar(cmd)
    if BLOCK_RE.search(cmd):
        return "BLOCKED: command not allowed"
    if CONFIRM_COMMANDS and input(f"\n$ {cmd}\nRun? [y/N] ").lower() != "y":
        return "SKIPPED by user"
    try:
        r = subprocess.run(cmd, shell=True, cwd=SANDBOX, capture_output=True,
                           text=True, timeout=COMMAND_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"TIMEOUT ({COMMAND_TIMEOUT}s)"
    out = (r.stdout + r.stderr).strip() or "(no output)"
    return f"exit={r.returncode}\n{out[-OUTPUT_LIMIT:]}"  # keep it short for WA


def write_file(rel, raw):
    p = safe_path(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    content = clean_content(raw)
    p.write_text(content)
    return f"[write] {rel} ({len(content)} chars) OK"


def execute(action: Action):
    if action.kind == "bash":
        return f"[bash] {action.arg}\n{run_bash(action.arg)}"
    if action.kind == "write":
        return write_file(action.arg, action.content)
    return ""
