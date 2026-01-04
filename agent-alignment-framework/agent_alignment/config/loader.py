"""Prompt loading utilities for the agent alignment framework.

This module provides utilities for loading and managing prompt templates
from files, with support for template variables and validation.
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PromptLoader:
    """Utility class for loading and managing prompt templates."""
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize the prompt loader.
        
        Args:
            base_path: Base directory for prompt templates
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._template_cache = {}
        
        logger.debug(
            "prompt_loader_initialized",
            extra={"base_path": str(self.base_path)}
        )
    
    def load_template(self, template_path: str, use_cache: bool = True) -> str:
        """Load a prompt template from file.
        
        Args:
            template_path: Path to template file (relative to base_path)
            use_cache: Whether to use cached templates
            
        Returns:
            str: Template content
            
        Raises:
            FileNotFoundError: If template file is not found
        """
        # Check cache first
        if use_cache and template_path in self._template_cache:
            logger.debug(
                "prompt_template_cache_hit",
                extra={"template_path": template_path}
            )
            return self._template_cache[template_path]
        
        # Resolve full path
        if os.path.isabs(template_path):
            full_path = Path(template_path)
        else:
            full_path = self.base_path / template_path
        
        # Load template
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Cache the template
            if use_cache:
                self._template_cache[template_path] = content
            
            logger.debug(
                "prompt_template_loaded",
                extra={
                    "template_path": template_path,
                    "full_path": str(full_path),
                    "content_length": len(content),
                }
            )
            
            return content
            
        except FileNotFoundError:
            logger.error(
                "prompt_template_not_found",
                extra={
                    "template_path": template_path,
                    "full_path": str(full_path),
                    "base_path": str(self.base_path),
                }
            )
            raise FileNotFoundError(f"Prompt template not found: {full_path}")
    
    def format_template(
        self,
        template_path: str,
        variables: Dict[str, Any],
        use_cache: bool = True
    ) -> str:
        """Load and format a prompt template with variables.
        
        Args:
            template_path: Path to template file
            variables: Variables to substitute in template
            use_cache: Whether to use cached templates
            
        Returns:
            str: Formatted template content
        """
        template = self.load_template(template_path, use_cache)
        
        try:
            formatted = template.format(**variables)
            
            logger.debug(
                "prompt_template_formatted",
                extra={
                    "template_path": template_path,
                    "variable_count": len(variables),
                    "formatted_length": len(formatted),
                }
            )
            
            return formatted
            
        except KeyError as e:
            logger.error(
                "prompt_template_format_error",
                extra={
                    "template_path": template_path,
                    "missing_variable": str(e),
                    "available_variables": list(variables.keys()),
                }
            )
            raise ValueError(f"Missing template variable {e} in {template_path}")
    
    def validate_template(self, template_path: str, required_variables: Optional[list] = None) -> bool:
        """Validate that a template exists and contains required variables.
        
        Args:
            template_path: Path to template file
            required_variables: List of required variable names
            
        Returns:
            bool: True if template is valid
        """
        try:
            template = self.load_template(template_path)
            
            if required_variables:
                # Extract variable names from template
                import re
                template_vars = set(re.findall(r'\{(\w+)\}', template))
                missing_vars = set(required_variables) - template_vars
                
                if missing_vars:
                    logger.warning(
                        "prompt_template_missing_variables",
                        extra={
                            "template_path": template_path,
                            "missing_variables": list(missing_vars),
                            "template_variables": list(template_vars),
                        }
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error(
                "prompt_template_validation_failed",
                extra={
                    "template_path": template_path,
                    "error": str(e),
                }
            )
            return False
    
    def list_templates(self, pattern: str = "*.txt") -> list:
        """List available template files.
        
        Args:
            pattern: File pattern to match (e.g., "*.txt", "*.md")
            
        Returns:
            list: List of template file paths
        """
        templates = []
        
        try:
            for template_file in self.base_path.glob(f"**/{pattern}"):
                if template_file.is_file():
                    # Get relative path from base_path
                    rel_path = template_file.relative_to(self.base_path)
                    templates.append(str(rel_path))
            
            logger.debug(
                "prompt_templates_listed",
                extra={
                    "base_path": str(self.base_path),
                    "pattern": pattern,
                    "template_count": len(templates),
                }
            )
            
        except Exception as e:
            logger.error(
                "prompt_template_listing_failed",
                extra={
                    "base_path": str(self.base_path),
                    "pattern": pattern,
                    "error": str(e),
                }
            )
        
        return sorted(templates)
    
    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._template_cache.clear()
        logger.debug("prompt_template_cache_cleared")


# Global prompt loader instance
_global_loader = None


def get_prompt_loader(base_path: Optional[str] = None) -> PromptLoader:
    """Get the global prompt loader instance.
    
    Args:
        base_path: Base path for templates (only used on first call)
        
    Returns:
        PromptLoader: Global prompt loader instance
    """
    global _global_loader
    
    if _global_loader is None:
        _global_loader = PromptLoader(base_path)
    
    return _global_loader


def load_prompt_template(template_path: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to load and optionally format a prompt template.
    
    Args:
        template_path: Path to template file
        variables: Optional variables for template formatting
        
    Returns:
        str: Template content (formatted if variables provided)
    """
    loader = get_prompt_loader()
    
    if variables:
        return loader.format_template(template_path, variables)
    else:
        return loader.load_template(template_path)


def validate_prompt_templates(template_configs: list) -> Dict[str, bool]:
    """Validate multiple prompt templates.
    
    Args:
        template_configs: List of dicts with 'path' and optional 'required_variables'
        
    Returns:
        Dict[str, bool]: Validation results for each template
    """
    loader = get_prompt_loader()
    results = {}
    
    for config in template_configs:
        template_path = config.get('path')
        required_vars = config.get('required_variables')
        
        if template_path:
            results[template_path] = loader.validate_template(template_path, required_vars)
    
    return results