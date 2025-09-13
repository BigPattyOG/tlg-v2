# cogs/dev/listcogs.py
"""command to list documented cogs (the ones in COG_METADATA only)"""

from discord import Embed

from cogs import ALL_COGS


def _build_cog_field_name(cog, is_loaded):
    """Build the field name for a cog entry"""
    name = cog.get("name")
    version = cog.get("version", "")
    enabled = "🟢" if is_loaded else "🔴"

    if version:
        return f"{enabled} {name} `v{version}`"

    return f"{enabled} {name}"


def _build_cog_info(cog):
    """Build the detailed info text for a cog"""
    desc = cog.get("description")
    author = cog.get("author")
    module = cog.get("module")
    commands = cog.get("commands", {})

    cog_info_parts = []
    if desc:
        cog_info_parts.append(f"Description: {desc}")
    if author:
        cog_info_parts.append(f"Author: {author}")
    cog_info_parts.append(f"Module: `{module}`")

    # add commands from metadata
    if commands:
        commands_list = []
        for cmd_name, cmd_data in commands.items():
            help_text = cmd_data.get("help", "No description")
            aliases = cmd_data.get("aliases", [])

            # Format command with aliases if they exist
            if aliases:
                aliases_str = ", ".join(f"`{alias}`" for alias in aliases)
                commands_list.append(f"- `{cmd_name}` (aliases: {aliases_str}): {help_text}")
            else:
                commands_list.append(f"- `{cmd_name}`: {help_text}")

        cog_info_parts.append("**Commands:**\n" + "\n".join(commands_list))

    return "\n".join(cog_info_parts)


async def list_cogs(self, ctx):
    """List all discovered cogs with metadata + commands"""
    embed = Embed(title="🛠️ Cogs List", color=0x00FF00)

    # Get currently loaded extensions from the bot
    loaded_extensions = set(self.bot.extensions.keys())

    if not ALL_COGS:
        embed.description = "No cogs discovered."
    else:
        for cog in ALL_COGS:
            # Check if this cog is actually loaded at runtime
            is_loaded = cog.get("module") in loaded_extensions

            # Build field name and cog info using helper functions
            field_name = _build_cog_field_name(cog, is_loaded)
            cog_info = _build_cog_info(cog)

            embed.add_field(
                name=field_name,
                value=cog_info or "No metadata",
                inline=False,
            )

    await ctx.send(embed=embed)
