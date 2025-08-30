# cogs/__init__.py
"""
cogs
"""

import logging
from importlib import import_module
from pathlib import Path

logger = logging.getLogger(__name__)
COG_FOLDER = Path(__file__).parent
COG_MODULES = []
ALL_COGS = []

logger.debug("COG_FOLDER path: %s", COG_FOLDER)
logger.debug("Current working directory: %s", Path.cwd())


def load_cog(module_path: str):
    """Import module and return metadata dict"""
    try:
        module = import_module(module_path)
    except (ModuleNotFoundError, ImportError) as e:
        logger.warning("Failed to import %s: %s", module_path, e)
        return None

    meta = getattr(module, "COG_METADATA", None)
    if not meta:
        # logger.warning("Cog %s has no COG_METADATA, skipping...", module_path)
        return None

    is_cog = bool(meta.get("is_cog", False))
    enabled = bool(meta.get("enabled", True))
    name = meta.get("name", module_path)
    description = meta.get("description", "")
    version = meta.get("version", "")
    author = meta.get("author", "")
    priority = int(meta.get("priority", 0))
    commands = meta.get("commands", {})

    return {
        "name": name,
        "is_cog": is_cog,
        "enabled": enabled,
        "description": description,
        "version": version,
        "author": author,
        "priority": priority,
        "module": module_path,
        "commands": commands,
    }


def discover_cogs():
    """Discover and load all cog modules from the cogs directory"""
    for file in COG_FOLDER.rglob("*.py"):
        if file.name == "__init__.py":
            if file.parent == COG_FOLDER:
                continue  # skip top-level __init__.py
            # For __init__.py files, use the parent directory path
            relative_parts = list(file.parent.relative_to(COG_FOLDER).parts)
            module_path = "cogs." + ".".join(relative_parts) if relative_parts else "cogs"
        else:
            # For regular .py files, use the file path without extension
            relative_parts = list(file.relative_to(COG_FOLDER).with_suffix("").parts)
            module_path = "cogs." + ".".join(relative_parts)

        logger.debug("Found file: %s -> module_path: %s", file, module_path)
        result = load_cog(module_path)
        if not result:
            continue

        metadata = result
        ALL_COGS.append(metadata)

        if metadata["is_cog"] and metadata["enabled"]:
            COG_MODULES.append(module_path)

    logger.info("Discovered cogs: %s", [c["name"] for c in ALL_COGS])
    logger.info("Enabled cogs: %s", COG_MODULES)


# Run discovery automatically
discover_cogs()
