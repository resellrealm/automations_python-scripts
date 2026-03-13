---
name: github-research
description: Research GitHub for trading bots, arbitrage strategies, or any code we can use. Finds real working repos, extracts key code patterns, and integrates the best ideas into our codebase. Use when asked to find/steal code from GitHub.
allowed-tools: WebSearch, WebFetch, Read, Write, Edit, Bash
argument-hint: "<search query>"
---

Research GitHub for: $ARGUMENTS

Steps:
1. Search GitHub for the query using WebSearch
2. Find 3-5 most promising repos (recent, starred, working)
3. For each repo:
   - Read the main Python files
   - Extract the core algorithm/strategy
   - Note any API patterns or edge detection logic
4. Write a summary of findings to `claude_agents/research_findings.md`
5. Ask: "Should I integrate any of these into our existing bots?"
6. If yes — implement the best parts into the relevant bot

Focus on: prediction markets, arbitrage, price mismatch detection, CLOB APIs.
