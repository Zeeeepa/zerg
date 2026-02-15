"""Security scanning functions for ZERG.

Migrated from zerg/security.py — contains all scan functions and constants.
"""

import os
import re
from pathlib import Path
from typing import Any

from zerg.logging import get_logger

logger = get_logger("security")

# Patterns for detecting potential secrets
SECRET_PATTERNS = [
    re.compile(r"password\s*[=:]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
    re.compile(r"secret\s*[=:]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
    re.compile(r"api_?key\s*[=:]\s*['\"][^'\"]{16,}['\"]", re.IGNORECASE),
    re.compile(r"access_?token\s*[=:]\s*['\"][^'\"]{16,}['\"]", re.IGNORECASE),
    re.compile(r"auth_?token\s*[=:]\s*['\"][^'\"]{16,}['\"]", re.IGNORECASE),
    re.compile(r"private_?key\s*[=:]\s*['\"][^'\"]{16,}['\"]", re.IGNORECASE),
    re.compile(r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"ghp_[A-Za-z0-9]{36}", re.IGNORECASE),  # GitHub Personal Access Token
    re.compile(r"gho_[A-Za-z0-9]{36}", re.IGNORECASE),  # GitHub OAuth Token
    re.compile(r"sk-[A-Za-z0-9]{48}", re.IGNORECASE),  # OpenAI API Key
    re.compile(r"AKIA[A-Z0-9]{16}", re.IGNORECASE),  # AWS Access Key ID
]

# Hook patterns for pre-commit checks
# These patterns are used by both the bash hook and Python validation
HOOK_PATTERNS = {
    # Security patterns (BLOCK on violation)
    "security": {
        "aws_key": r"AKIA[0-9A-Z]{16}",
        "github_pat": r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{20,}_[a-zA-Z0-9]{40,})",
        "openai_key": r"sk-[a-zA-Z0-9]{48}",
        "anthropic_key": r"sk-ant-[a-zA-Z0-9\-]{90,}",
        "private_key": r"-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
        "generic_secret": (
            r"(password|secret|api_key|apikey|access_token|auth_token)" r"\s*[=:]\s*['\"][^'\"]{8,}['\"]"
        ),
        "shell_injection": r"(shell\s*=\s*True|os\.system\s*\(|os\.popen\s*\()",
        "code_injection": r"^[^#]*\b(eval|exec)\s*\(",
        # Detect unsafe deserialization usage
        "unsafe_deserialization": r"pickle\.(load|loads)\s*\(",
    },
    # Quality patterns (WARN on violation)
    "quality": {
        "debugger": r"(breakpoint\s*\(\)|pdb\.set_trace\s*\(\)|import\s+i?pdb)",
        "merge_conflict": r"^(<{7}|={7}|>{7})",
        "print_stmt": r"^[^#]*\bprint\s*\(",
    },
    # ZERG-specific patterns
    "zerg": {
        "branch_name": r"^zerg/[a-z0-9-]+/worker-[0-9]+$",
        "localhost": r"(localhost|127\.0\.0\.1|0\.0\.0\.0):[0-9]+",
    },
}

# Sensitive file names to warn about
SENSITIVE_FILES = [
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "credentials.json",
    "service-account.json",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    ".npmrc",
    ".pypirc",
]


def check_for_secrets(content: str) -> list[tuple[int, str, str]]:
    """Check content for potential secrets.

    Args:
        content: Text content to check

    Returns:
        List of (line_number, pattern_name, matched_text) tuples
    """
    findings = []

    for line_num, line in enumerate(content.split("\n"), start=1):
        for pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                # Mask the actual secret value
                masked = line[:50] + "..." if len(line) > 50 else line
                findings.append((line_num, pattern.pattern[:30] + "...", masked))

    return findings


def check_for_non_ascii_filenames(files: list[str]) -> list[str]:
    """Check for non-ASCII characters in filenames.

    Args:
        files: List of file paths to check

    Returns:
        List of files with non-ASCII characters
    """
    non_ascii = []

    for filepath in files:
        # Check if any character is non-ASCII
        try:
            filepath.encode("ascii")
        except UnicodeEncodeError:
            non_ascii.append(filepath)

    return non_ascii


def check_sensitive_files(files: list[str]) -> list[str]:
    """Check for sensitive files in the list.

    Args:
        files: List of file paths to check

    Returns:
        List of sensitive files found
    """
    sensitive = []

    for filepath in files:
        filename = Path(filepath).name
        if filename in SENSITIVE_FILES:
            sensitive.append(filepath)

    return sensitive


def validate_commit_message(message: str) -> tuple[bool, str | None]:
    """Validate commit message format.

    Args:
        message: Commit message to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message:
        return False, "Commit message is empty"

    first_line = message.split("\n")[0].strip()

    if len(first_line) < 10:
        return False, "Commit message too short (minimum 10 characters)"

    if len(first_line) > 72:
        return False, "Commit message first line too long (maximum 72 characters)"

    # Check for conventional commit format
    conventional_pattern = re.compile(r"^(feat|fix|docs|style|refactor|test|chore|build|ci|perf|revert)(\(.+\))?!?: .+")

    if not conventional_pattern.match(first_line) and not first_line.startswith("Merge "):
        return False, (
            "Commit message doesn't follow conventional commit format. "
            "Use: feat|fix|docs|style|refactor|test|chore|build|ci|perf|revert"
        )

    return True, None


def check_file_size(filepath: str | Path, max_size_mb: float = 5.0) -> bool:
    """Check if file exceeds maximum size.

    Args:
        filepath: Path to file
        max_size_mb: Maximum size in megabytes

    Returns:
        True if file is within size limit
    """
    path = Path(filepath)
    if not path.exists():
        return True

    size_bytes = path.stat().st_size
    max_bytes = max_size_mb * 1024 * 1024

    return size_bytes <= max_bytes


def get_large_files(files: list[str], max_size_mb: float = 5.0) -> list[tuple[str, float]]:
    """Get list of files exceeding size limit.

    Args:
        files: List of file paths to check
        max_size_mb: Maximum size in megabytes

    Returns:
        List of (filepath, size_mb) tuples for large files
    """
    large = []
    max_bytes = max_size_mb * 1024 * 1024

    for filepath in files:
        path = Path(filepath)
        if path.exists():
            size_bytes = path.stat().st_size
            if size_bytes > max_bytes:
                size_mb = size_bytes / (1024 * 1024)
                large.append((filepath, round(size_mb, 2)))

    return large


def run_security_scan(path: str | Path = ".") -> dict[str, Any]:
    """Run a security scan on the specified path.

    Args:
        path: Path to scan

    Returns:
        Dictionary with scan results
    """
    scan_path = Path(path).resolve()
    results: dict[str, Any] = {
        "secrets_found": [],
        "sensitive_files": [],
        "non_ascii_files": [],
        "large_files": [],
        "symlink_violations": [],
        "passed": True,
    }

    # Collect all files
    all_files = []
    for root, dirs, files in os.walk(scan_path, followlinks=False):
        # Skip git and cache directories
        skip = {".git", "__pycache__", "node_modules", ".venv", "venv"}
        dirs[:] = [d for d in dirs if d not in skip]

        for f in files:
            filepath = os.path.join(root, f)

            # Validate path stays within scan boundary (defense against symlink escapes)
            try:
                resolved = Path(filepath).resolve()
                if not resolved.is_relative_to(scan_path):
                    logger.warning(f"Symlink escape detected, skipping: {filepath}")
                    results["symlink_violations"].append(filepath)
                    continue
            except (OSError, ValueError) as e:
                logger.warning(f"Path resolution error, skipping {filepath}: {e}")
                continue

            all_files.append(str(resolved))

    # Check for sensitive files
    results["sensitive_files"] = check_sensitive_files(all_files)

    # Check for non-ASCII filenames
    results["non_ascii_files"] = check_for_non_ascii_filenames(all_files)

    # Check for large files
    results["large_files"] = get_large_files(all_files)

    # Check for secrets in text files
    text_extensions = {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".md", ".txt", ".sh", ".env"}
    for filepath in all_files:
        if Path(filepath).suffix in text_extensions:
            try:
                file_content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
                secrets = check_for_secrets(file_content)
                if secrets:
                    results["secrets_found"].append(
                        {
                            "file": filepath,
                            "findings": secrets,
                        }
                    )
            except OSError:
                pass

    # Determine if scan passed
    results["passed"] = not (results["secrets_found"] or results["sensitive_files"])

    return results
