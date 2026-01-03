"""Prompt management system for compatibility evaluation agents.

This package provides versioned, disk-based prompt management with caching
and validation. Prompts are separated from business logic to enable easy
updates and A/B testing without code changes.

Design Philosophy:
- Prompts are data, not code
- Version control for prompt evolution
- Validation to prevent runtime failures
- Caching for performance
"""
