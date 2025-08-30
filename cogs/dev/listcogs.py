# cogs/dev/listcogs.py
"""command to list documented cogs (the ones in COG_METADATA only)"""

from discord import Embed

from cogs import ALL_COGS


async def list_cogs(_, ctx):
    """List all discovered cogs with metadata + commands"""
    embed = Embed(title="🛠️ Cogs List", color=0x00FF00)

    if not ALL_COGS:
        embed.description = "No cogs discovered."
    else:
        for cog in ALL_COGS:
            meta = {
                "name": cog.get("name"),
                "desc": cog.get("description"),
                "version": cog.get("version", ""),
                "enabled": "🟢" if cog.get("enabled") else "🔴",
                "author": cog.get("author"),
                "module": cog.get("module"),
                "commands": cog.get("commands", {}),
            }

            # build cog header
            field_name = (
                f"{meta['enabled']} {meta['name']} `v{meta['version']}`"
                if meta["version"]
                else f"{meta['enabled']} {meta['name']}"
            )

            # build cog details
            cog_info_parts = []
            if meta["desc"]:
                cog_info_parts.append(f"Description: {meta['desc']}")
            if meta["author"]:
                cog_info_parts.append(f"Author: {meta['author']}")
            cog_info_parts.append(f"Module: `{meta['module']}`")

            # add commands from metadata
            if meta["commands"]:
                commands_list = []
                for cmd_name, cmd_data in meta["commands"].items():
                    help_text = cmd_data.get("help", "No description")
                    aliases = cmd_data.get("aliases", [])

                    # Format command with aliases if they exist
                    if aliases:
                        aliases_str = ", ".join(f"`{alias}`" for alias in aliases)
                        commands_list.append(
                            f"- `{cmd_name}` (aliases: {aliases_str}): {help_text}"
                        )
                    else:
                        commands_list.append(f"- `{cmd_name}`: {help_text}")

                cog_info_parts.append("**Commands:**\n" + "\n".join(commands_list))

            # finalize field value
            cog_info = "\n".join(cog_info_parts)

            embed.add_field(
                name=field_name,
                value=cog_info or "No metadata",
                inline=False,
            )

    await ctx.send(embed=embed)
