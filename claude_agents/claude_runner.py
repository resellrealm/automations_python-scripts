"""
Claude Runner — Run Claude Code CLI programmatically
=====================================================
Wraps the `claude` CLI for non-interactive use from Python scripts.
Claude handles: code writing, debugging, architecture, complex tasks.

Usage:
    from claude_runner import claude_run, claude_task
    result = claude_run("Fix the bug in oddpool/matcher.py")
    result = claude_task("Write a new strategy for Kalshi", max_turns=10)
"""

import os
import json
import subprocess
import logging
from typing import Optional, Generator
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_DIR = str(Path(__file__).parent.parent)


def claude_run(
    prompt: str,
    cwd: str = PROJECT_DIR,
    max_turns: int = 20,
    output_format: str = "text",
    model: str = "sonnet",
    allowed_tools: str = None,
    system_prompt: str = None,
    max_budget: float = None,
    resume_session: str = None,
) -> str:
    """
    Run Claude Code non-interactively (-p flag).
    Returns text output.
    """
    cmd = ["claude", "-p", prompt,
           "--output-format", output_format,
           "--model", model,
           "--max-turns", str(max_turns)]

    if allowed_tools:
        cmd += ["--allowedTools", allowed_tools]
    if system_prompt:
        cmd += ["--system-prompt", system_prompt]
    if max_budget:
        cmd += ["--max-budget-usd", str(max_budget)]
    if resume_session:
        cmd += ["--resume", resume_session]

    logger.info(f"Claude CLI: {prompt[:80]}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=cwd,
            timeout=300,
        )

        if output_format == "json" and result.stdout:
            try:
                data = json.loads(result.stdout)
                return data.get("result", result.stdout)
            except json.JSONDecodeError:
                pass

        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            logger.warning(f"Claude CLI stderr: {result.stderr[:200]}")

        return output

    except subprocess.TimeoutExpired:
        logger.error("Claude CLI timed out after 300s")
        return "[timeout]"
    except FileNotFoundError:
        logger.error("claude CLI not found — run: curl -fsSL https://claude.ai/install.sh | bash")
        return "[claude not installed]"
    except Exception as e:
        logger.error(f"Claude CLI error: {e}")
        return f"[error: {e}]"


def claude_task(
    task: str,
    context: str = "",
    tools: str = "Read,Write,Edit,Bash,Glob,Grep",
    max_turns: int = 30,
    budget: float = 2.0,
) -> str:
    """
    Run Claude on a specific task with full tool access.
    Use this for code writing, debugging, complex analysis.
    """
    full_prompt = task
    if context:
        full_prompt = f"Context:\n{context}\n\nTask:\n{task}"

    return claude_run(
        prompt       = full_prompt,
        max_turns    = max_turns,
        allowed_tools= tools,
        max_budget   = budget,
    )


def claude_stream(prompt: str, cwd: str = PROJECT_DIR) -> Generator[str, None, None]:
    """Stream Claude output token by token."""
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json"]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", cwd=cwd,
        )
        for line in proc.stdout:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    if data.get("type") == "text":
                        yield data.get("text", "")
                except json.JSONDecodeError:
                    yield line
    except Exception as e:
        yield f"[stream error: {e}]"


def claude_code(description: str, file_path: str = None, language: str = "python") -> str:
    """
    Ask Claude to write or fix code.
    If file_path given, Claude reads it first then fixes/extends it.
    """
    if file_path and Path(file_path).exists():
        prompt = (
            f"Read {file_path} and then: {description}\n"
            f"Write the complete updated {language} code."
        )
    else:
        prompt = f"Write {language} code to: {description}\nInclude all imports."

    return claude_run(prompt, tools="Read,Write,Edit,Bash", max_turns=15)


def claude_github_research(query: str, max_results: int = 5) -> str:
    """
    Ask Claude to search GitHub and return relevant findings.
    """
    prompt = (
        f"Search GitHub for: {query}\n"
        f"Find the top {max_results} most relevant repos.\n"
        f"For each: name, stars, description, key code patterns, install command.\n"
        f"Focus on working, recent (2024-2026) implementations."
    )
    return claude_run(
        prompt,
        allowed_tools="WebSearch,WebFetch",
        max_turns=10,
    )
