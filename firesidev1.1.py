import os
import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
from dotenv import load_dotenv
import json
import asyncio
import datetime
from typing import Union, List, Literal
import math

# Load environment variables from .env file
load_dotenv()

# Get bot token and owner ID
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# New environment variables for bot status
BOT_ACTIVITY_TYPE = os.getenv("BOT_ACTIVITY_TYPE", "watching")
BOT_ACTIVITY_MESSAGE = os.getenv("BOT_ACTIVITY_MESSAGE", "over {membercount} members")
BOT_STATUS_TYPE = os.getenv("BOT_STATUS_TYPE", "online").lower()

# Define bot intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.presences = True

# Create the bot client
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=OWNER_ID, help_command=None)

# Define file names
BLACKLIST_FILE = "blacklist.json"
SERVER_CONFIGS_FILE = "server_configs.json"

# Caching mechanism to reduce API calls
_cached_users = {}

# --- Constanten voor Fireside functionaliteit ---
# De ID van de Fireside Discord-server.
FIRESIDE_GUILD_ID = 1411711201892892714
# De ID van de rol die geblackliste gebruikers moeten krijgen.
BLACKLIST_ROLE_ID = 1416390043131449395

# --- Localization strings ---
MESSAGES = {
    "welcome_dm": {
        "title": {
            "en": "Thank you for adding Fireside to {guild_name}!",
            "nl": "Bedankt voor het toevoegen van Fireside aan {guild_name}!"
        },
        "description": {
            "en": (
                "Fireside is now active on your server! Here are some important steps to configure the bot:\n\n"
                "**1. Receiving warnings in DMs:**\n"
                "By default, the server owner receives a DM notification when a blacklisted member joins the server. To disable these notifications, use the command:\n"
                "`/blacklist toggledmserverowner`\n\n"
                "**2. Setting a warning channel:**\n"
                "To set a specific channel where public warnings are posted when a blacklisted member is kicked, use the following command in the desired channel:\n"
                "`/blacklist setwarningchannel`\n"
                "Select the desired channel from the list that appears after typing the command.\n\n"
                "**3. Changing the bot's language:**\n"
                "You can change the bot's language for your server by using the command:\n"
                "`/settings setlanguage <language>`"
            ),
            "nl": (
                "Fireside is nu actief op je server! Hier zijn enkele belangrijke stappen om de bot te configureren:\n\n"
                "**1. Ontvangst van waarschuwingen in DM's:**\n"
                "Standaard ontvangt de servereigenaar een DM-melding wanneer een geblacklist lid de server betreedt. Om deze meldingen uit te schakelen, gebruik je het commando:\n"
                "`/blacklist toggledmserverowner`\n\n"
                "**2. Een waarschuwingskanaal instellen:**\n"
                "Om een specifiek kanaal in te stellen waar publieke waarschuwingen worden geplaatst wanneer een geblacklist lid wordt gekickt, gebruik je het volgende commando in het gewenste kanaal:\n"
                "`/blacklist setwarningchannel`\n"
                "Kies het gewenste kanaal in de lijst die verschijnt na het typen van het commando.\n\n"
                "**3. De taal van de bot veranderen:**\n"
                "Je kunt de taal van de bot voor je server veranderen met het volgende commando:\n"
                "`/settings setlanguage <language>`"
            )
        }
    },
    "set_language_response": {
        "title_success": {"en": "Language Set", "nl": "Taal Ingesteld"},
        "title_fail": {"en": "Could Not Set Language", "nl": "Kon de Taal niet instellen"},
        "desc_success": {"en": "The bot's language has been successfully set to `{lang_code}`.",
                         "nl": "De taal van de bot is succesvol ingesteld op `{lang_code}`."},
        "desc_fail": {"en": "An error occurred while trying to set the language: `{error}`.",
                      "nl": "Er is een fout opgetreden bij het instellen van de taal: `{error}`."}
    },
    "blacklist_messages": {
        "user_blacklisted_title": {"en": "User Blacklisted", "nl": "Gebruiker op Blacklist"},
        "user_blacklisted_message": {
            "en": "User {user_mention} ({user_id}) has been added to the blacklist for reason: `{reason}`.",
            "nl": "Gebruiker {user_mention} ({user_id}) is toegevoegd aan de blacklist omwille van: `{reason}`."
        },
        "user_already_blacklisted": {
            "en": "User `{user_id}` is already on the blacklist.",
            "nl": "Gebruiker `{user_id}` staat al op de blacklist."
        },
        "user_not_blacklisted": {
            "en": "User `{user_id}` is not on the blacklist.",
            "nl": "Gebruiker `{user_id}` staat niet op de blacklist."
        },
        "user_removed_title": {"en": "User Removed", "nl": "Gebruiker Verwijderd"},
        "user_removed_message": {
            "en": "User `{user_id}` has been removed from the blacklist.",
            "nl": "Gebruiker `{user_id}` is verwijderd van de blacklist."
        },
        "multi_add_title": {"en": "Multiple Users Blacklisted", "nl": "Meerdere Gebruikers op Blacklist"},
        "multi_add_success": {"en": "{count} users successfully added to the blacklist.",
                              "nl": "{count} gebruikers succesvol toegevoegd aan de blacklist."},
        "multi_add_fail": {"en": "{count} users were already on the blacklist.",
                           "nl": "{count} gebruikers stonden al op de blacklist."},
        "multi_remove_title": {"en": "Multiple Users Removed", "nl": "Meerdere Gebruikers Verwijderd"},
        "multi_remove_success": {"en": "{count} users successfully removed from the blacklist.",
                                 "nl": "{count} gebruikers succesvol verwijderd van de blacklist."},
        "multi_remove_fail": {"en": "{count} users were not on the blacklist.",
                              "nl": "{count} gebruikers stonden niet op de blacklist."},
        "blacklist_info_title": {"en": "Fireside Blacklist", "nl": "Fireside Blacklist"},
        "blacklist_info_description": {
            "en": "**Total Users:** {total_users}\n**Total Servers:** {total_servers}\n\nHere are the first {count} users on the blacklist. Use the buttons below to navigate.",
            "nl": "**Totaal aantal gebruikers:** {total_users}\n**Totaal aantal servers:** {total_servers}\n\nHier zijn de eerste {count} gebruikers op de blacklist. Gebruik de knoppen hieronder om te navigeren."
        }
    },
    "error_messages": {
        "access_denied": {"en": "Access Denied", "nl": "Toegang Geweigerd"},
        "not_owner_message": {"en": "Only the bot owner can run this command.",
                              "nl": "Alleen de bot eigenaar kan dit commando uitvoeren."},
        "user_not_found": {"en": "User not found.", "nl": "Gebruiker niet gevonden."},
        "dm_error": {"en": "Could not DM the user.", "nl": "Kon de gebruiker niet een DM sturen."},
        "kick_error": {"en": "Could not kick the user. Please check bot permissions.",
                       "nl": "Kon de gebruiker niet kicken. Controleer de bot permissies."},
        "unexpected_error_title": {"en": "Unexpected Error", "nl": "Onverwachte Fout"},
        "missing_perms_title": {"en": "Missing Permissions", "nl": "Ontbrekende Permissies"},
        "bot_perms_missing_title": {"en": "Bot Missing Permissions", "nl": "Bot Mist Permissies"},
        "missing_perms": {"en": "You are missing the required permissions to run this command.",
                          "nl": "Je mist de benodigde permissies om dit commando uit te voeren."},
        "bot_perms_missing": {"en": "The bot is missing the required permissions to run this command.",
                              "nl": "De bot mist de benodigde permissies om dit commando uit te voeren."},
        "owner_check_failed": {"en": "This action can only be performed by the bot owner or the guild owner.",
                               "nl": "Deze actie kan alleen worden uitgevoerd door de bot eigenaar of de server eigenaar."},
        "owner_check_failed_title": {"en": "Permission Denied", "nl": "Toestemming Geweigerd"},
        "dm_only_command": {"en": "This command can only be used in a private message with the bot.",
                            "nl": "Dit commando kan alleen gebruikt worden in een privébericht met de bot."}
    },
    "general": {
        "footer": "fireside | Blacklist | made by t_62__",
        "kick_reason": {
            "en": "User is on the Fireside blacklist.",
            "nl": "Gebruiker staat op de Fireside blacklist."
        },
        "dm_toggle_title": {
            "en": "DM Notifications Toggled",
            "nl": "DM-meldingen In- of Uitgeschakeld"
        },
        "warning_channel_title": {
            "en": "Warning Channel Set",
            "nl": "Waarschuwingskanaal Ingesteld"
        },
        "user_kick_title": {
            "en": "Blacklisted User Detected!",
            "nl": "Geblackliste Gebruiker Gedetecteerd!"
        },
        "user_kick_description": {
            "en": "A blacklisted user, `{member_name}` ({member_id}), attempted to join the server and has been kicked.",
            "nl": "Een geblackliste gebruiker, `{member_name}` ({member_id}), heeft geprobeerd de server te betreden en is gekickt."
        }
    }
}


def get_message(lang_key: str, message_group: str, message_key: str, **kwargs) -> str:
    """Get the translated text from the specified message group and key."""
    try:
        return MESSAGES[message_group][message_key][lang_key].format(**kwargs)
    except KeyError:
        # Fallback to English if the specific language/key is not found
        return MESSAGES[message_group][message_key]['en'].format(**kwargs)


def load_blacklist():
    """Load the blacklist from the JSON file."""
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_blacklist(blacklist):
    """Save the blacklist to the JSON file."""
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(blacklist, f, indent=4)


def load_configs():
    """Load server configurations from the JSON file."""
    if os.path.exists(SERVER_CONFIGS_FILE):
        with open(SERVER_CONFIGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_configs(configs):
    """Save server configurations to the JSON file."""
    with open(SERVER_CONFIGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(configs, f, indent=4)


blacklist_data = load_blacklist()
server_configs = load_configs()


# Helper function to get the correct language for a guild
def get_guild_lang(guild_id: int):
    return server_configs.get(str(guild_id), {}).get('language', 'en')


def create_embed(interaction: discord.Interaction, message_group: str, title_key: str, color: discord.Color, **kwargs):
    """Creates a standardized embed with a title from the message group."""
    lang = get_guild_lang(interaction.guild_id)

    # Get the title from the messages dictionary
    title = get_message(lang, message_group, title_key)

    # Check if a specific message is provided in kwargs, otherwise use a default
    if 'message' in kwargs:
        description = kwargs['message']
    elif 'description_key' in kwargs:
        description = get_message(lang, message_group, kwargs['description_key'], **kwargs)
    else:
        # Fallback to an empty string if no message is found
        description = ""

    # Add error details if provided
    if 'error' in kwargs:
        description += f"\n\n**Error Details:**\n```\n{kwargs['error']}\n```"

    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    # Set the footer using the standardized function
    embed.set_footer(text=MESSAGES['general']['footer'])

    return embed


@bot.event
async def on_ready():
    """This event is triggered when the bot is successfully connected."""
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    update_member_count.start()
    sync_fireside_blacklist_role.start()


@tasks.loop(minutes=5.0)
async def update_member_count():
    """
    Updates the bot's status with the total member count across all servers.
    This task runs every 5 minutes.
    """
    await bot.wait_until_ready()
    try:
        total_members = sum(guild.member_count for guild in bot.guilds)

        status_message = BOT_ACTIVITY_MESSAGE.format(membercount=total_members)
        activity_type_map = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "custom": discord.ActivityType.custom
        }
        status_type_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible
        }

        activity_type = activity_type_map.get(BOT_ACTIVITY_TYPE.lower(), discord.ActivityType.watching)
        status_type = status_type_map.get(BOT_STATUS_TYPE, discord.Status.online)

        await bot.change_presence(activity=discord.Activity(type=activity_type, name=status_message),
                                  status=status_type)

    except Exception as e:
        print(f"Error updating bot status: {e}")


@tasks.loop(minutes=10)
async def sync_fireside_blacklist_role():
    """
    Periodically synchroniseert de blacklist rol in de Fireside Discord-server.
    Dit zorgt ervoor dat leden die al in de server zijn, de rol krijgen als ze geblacklist worden,
    en dat de rol wordt verwijderd als ze van de blacklist worden gehaald.
    """
    await bot.wait_until_ready()
    guild = bot.get_guild(FIRESIDE_GUILD_ID)
    if not guild:
        print("Fireside Discord-server niet gevonden, sla taak over.")
        return

    print("Bezig met controleren van geblackliste leden in Fireside...")
    role = guild.get_role(BLACKLIST_ROLE_ID)
    if not role:
        print(f"Rol met ID {BLACKLIST_ROLE_ID} niet gevonden in Fireside, sla taak over.")
        return

    for member in guild.members:
        member_id_str = str(member.id)
        is_member_blacklisted = member_id_str in blacklist_data
        has_blacklist_role = role in member.roles

        # Voeg de rol toe als de gebruiker geblacklist is en de rol niet heeft
        if is_member_blacklisted and not has_blacklist_role:
            try:
                await member.add_roles(role,
                                       reason="Gebruiker staat op de blacklist. Automatisch toegewezen door periodieke controle.")
                print(f"Rol '{role.name}' toegevoegd aan {member.name} (periodieke controle).")
            except discord.Forbidden:
                print(f"Fout: Bot mist de rechten om rollen toe te wijzen aan {member.name}.")
            except Exception as e:
                print(f"Onverwachte fout bij het toewijzen van de rol aan {member.name}: {e}")

        # Verwijder de rol als de gebruiker niet geblacklist is maar de rol wel heeft
        elif not is_member_blacklisted and has_blacklist_role:
            try:
                await member.remove_roles(role,
                                          reason="Gebruiker is van de blacklist verwijderd. Rol automatisch verwijderd.")
                print(f"Rol '{role.name}' verwijderd van {member.name} (periodieke controle).")
            except discord.Forbidden:
                print(f"Fout: Bot mist de rechten om rollen te verwijderen van {member.name}.")
            except Exception as e:
                print(f"Onverwachte fout bij het verwijderen van de rol van {member.name}: {e}")


@bot.event
async def on_guild_join(guild):
    """Event: Send welcome message to the guild owner when the bot joins a new guild."""
    lang = get_guild_lang(guild.id)

    embed = discord.Embed(
        title=get_message(lang, "welcome_dm", "title", guild_name=guild.name),
        description=get_message(lang, "welcome_dm", "description"),
        color=discord.Color.blue()
    )
    embed.set_footer(text=MESSAGES['general']['footer'])

    try:
        await guild.owner.send(embed=embed)
    except discord.Forbidden:
        print(f"Failed to DM the owner of guild {guild.name} ({guild.id})")


@bot.event
async def on_member_join(member: discord.Member):
    """Event: Check if a new member is blacklisted and take action."""
    lang = get_guild_lang(member.guild.id)

    if str(member.id) in blacklist_data:
        # Extra functionaliteit voor de Fireside server
        if member.guild.id == FIRESIDE_GUILD_ID:
            role = member.guild.get_role(BLACKLIST_ROLE_ID)
            if role and role not in member.roles:
                try:
                    await member.add_roles(role, reason="Gebruiker staat op de blacklist.")
                    print(f"Rol '{role.name}' succesvol toegevoegd aan {member.name} ({member.id}).")
                except discord.Forbidden:
                    print(f"Fout: Bot mist de rechten om rollen toe te wijzen aan {member.name} in Fireside.")
                except Exception as e:
                    print(f"Onverwachte fout bij het toewijzen van de rol aan {member.name}: {e}")

        try:
            # DM server owner
            if server_configs.get(str(member.guild.id), {}).get('dm_server_owner', True):
                embed = discord.Embed(
                    title=get_message(lang, "general", "user_kick_title"),
                    description=get_message(lang, "general", "user_kick_description", member_name=member.name,
                                            member_id=member.id),
                    color=discord.Color.red()
                )
                embed.set_footer(text=MESSAGES['general']['footer'])
                try:
                    await member.guild.owner.send(embed=embed)
                except discord.Forbidden:
                    print(f"Could not DM server owner for guild {member.guild.name} ({member.guild.id})")

            # Send message to warning channel if set
            warning_channel_id = server_configs.get(str(member.guild.id), {}).get('warning_channel_id')
            if warning_channel_id:
                warning_channel = member.guild.get_channel(warning_channel_id)
                if warning_channel:
                    embed = discord.Embed(
                        title=get_message(lang, "general", "user_kick_title"),
                        description=get_message(lang, "general", "user_kick_description", member_name=member.name,
                                                member_id=member.id),
                        color=discord.Color.red()
                    )
                    embed.set_footer(text=MESSAGES['general']['footer'])
                    await warning_channel.send(embed=embed)

            # Kick the member
            await member.kick(reason=get_message(lang, "general", "kick_reason", lang_key=lang))

        except discord.Forbidden:
            print(f"Failed to kick user {member.name} from guild {member.guild.name}. Check permissions.")
        except Exception as e:
            print(f"An error occurred during blacklisted user handling: {e}")


# Main command group for Blacklist
blacklist_group = app_commands.Group(name="blacklist", description="Blacklist related commands.")
bot.tree.add_command(blacklist_group)

# Main command group for Settings
settings_group = app_commands.Group(name="settings", description="Server settings.")
bot.tree.add_command(settings_group)


@blacklist_group.command(name="add", description="Add a user to the blacklist.")
@app_commands.checks.has_permissions(manage_guild=True)
async def add_user_to_blacklist(interaction: discord.Interaction, user: discord.Member,
                                reason: str = "No reason provided."):
    """Adds a user to the blacklist."""
    lang = get_guild_lang(interaction.guild_id)

    user_id_str = str(user.id)
    if user_id_str in blacklist_data:
        embed = create_embed(
            interaction, "blacklist_messages", "user_already_blacklisted", discord.Color.red(),
            message=get_message(lang, "blacklist_messages", "user_already_blacklisted", user_id=user_id_str)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        blacklist_data[user_id_str] = reason
        save_blacklist(blacklist_data)

        # Nieuwe logica voor de Fireside server
        if interaction.guild.id == FIRESIDE_GUILD_ID:
            role = interaction.guild.get_role(BLACKLIST_ROLE_ID)
            if role:
                try:
                    await user.add_roles(role, reason="Gebruiker is geblacklist via het `/blacklist add` commando.")
                except discord.Forbidden:
                    print(f"Bot mist de rechten om de rol toe te wijzen aan {user.name} in Fireside.")

        user_mention = f"<@{user_id_str}>"
        embed = create_embed(
            interaction, "blacklist_messages", "user_blacklisted_title", discord.Color.green(),
            message=get_message(lang, "blacklist_messages", "user_blacklisted_message", user_mention=user_mention,
                                user_id=user_id_str, reason=reason)
        )
        await interaction.response.send_message(embed=embed)


@blacklist_group.command(name="remove", description="Remove a user from the blacklist.")
@app_commands.checks.has_permissions(manage_guild=True)
async def remove_user_from_blacklist(interaction: discord.Interaction, user: discord.Member):
    """Removes a user from the blacklist."""
    lang = get_guild_lang(interaction.guild_id)

    user_id_str = str(user.id)
    if user_id_str in blacklist_data:
        del blacklist_data[user_id_str]
        save_blacklist(blacklist_data)

        # Nieuwe logica voor de Fireside server
        if interaction.guild.id == FIRESIDE_GUILD_ID:
            role = interaction.guild.get_role(BLACKLIST_ROLE_ID)
            if role:
                try:
                    await user.remove_roles(role, reason="Gebruiker is van de blacklist verwijderd.")
                except discord.Forbidden:
                    print(f"Bot mist de rechten om de rol te verwijderen van {user.name} in Fireside.")

        embed = create_embed(
            interaction, "blacklist_messages", "user_removed_title", discord.Color.green(),
            message=get_message(lang, "blacklist_messages", "user_removed_message", user_id=user_id_str)
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_embed(
            interaction, "blacklist_messages", "user_not_blacklisted", discord.Color.red(),
            message=get_message(lang, "blacklist_messages", "user_not_blacklisted", user_id=user_id_str)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist_group.command(name="addid", description="Add a user to the blacklist via ID.")
@app_commands.checks.has_permissions(manage_guild=True)
async def add_id_to_blacklist(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided."):
    """Adds a user to the blacklist via ID."""
    lang = get_guild_lang(interaction.guild_id)

    user_id_str = str(user_id)
    if user_id_str in blacklist_data:
        embed = create_embed(
            interaction, "blacklist_messages", "user_already_blacklisted", discord.Color.red(),
            message=get_message(lang, "blacklist_messages", "user_already_blacklisted", user_id=user_id_str)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        blacklist_data[user_id_str] = reason
        save_blacklist(blacklist_data)

        user_mention = f"<@{user_id_str}>"
        embed = create_embed(
            interaction, "blacklist_messages", "user_blacklisted_title", discord.Color.green(),
            message=get_message(lang, "blacklist_messages", "user_blacklisted_message", user_mention=user_mention,
                                user_id=user_id_str, reason=reason)
        )
        await interaction.response.send_message(embed=embed)


@blacklist_group.command(name="removeid", description="Remove a user from the blacklist via ID.")
@app_commands.checks.has_permissions(manage_guild=True)
async def remove_id_from_blacklist(interaction: discord.Interaction, user_id: str):
    """Removes a user from the blacklist via ID."""
    lang = get_guild_lang(interaction.guild_id)

    user_id_str = str(user_id)
    if user_id_str in blacklist_data:
        del blacklist_data[user_id_str]
        save_blacklist(blacklist_data)

        embed = create_embed(
            interaction, "blacklist_messages", "user_removed_title", discord.Color.green(),
            message=get_message(lang, "blacklist_messages", "user_removed_message", user_id=user_id_str)
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_embed(
            interaction, "blacklist_messages", "user_not_blacklisted", discord.Color.red(),
            message=get_message(lang, "blacklist_messages", "user_not_blacklisted", user_id=user_id_str)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist_group.command(name="addidmore", description="Add multiple users to the blacklist via IDs.")
@app_commands.checks.has_permissions(manage_guild=True)
async def add_id_more_to_blacklist(interaction: discord.Interaction, user_ids: str,
                                   reason: str = "No reason provided."):
    """Adds multiple users to the blacklist via IDs."""
    lang = get_guild_lang(interaction.guild_id)

    ids_to_add = user_ids.split()
    added_count = 0
    already_blacklisted_count = 0

    for user_id in ids_to_add:
        if user_id in blacklist_data:
            already_blacklisted_count += 1
        else:
            blacklist_data[user_id] = reason
            added_count += 1

    save_blacklist(blacklist_data)

    embed = create_embed(
        interaction, "blacklist_messages", "multi_add_title", discord.Color.green(),
        message=(
                get_message(lang, "blacklist_messages", "multi_add_success", count=added_count) +
                (f"\n" + get_message(lang, "blacklist_messages", "multi_add_fail",
                                     count=already_blacklisted_count) if already_blacklisted_count > 0 else "")
        )
    )
    await interaction.response.send_message(embed=embed)


@blacklist_group.command(name="removeidmore", description="Remove multiple users from the blacklist via IDs.")
@app_commands.checks.has_permissions(manage_guild=True)
async def remove_id_more_from_blacklist(interaction: discord.Interaction, user_ids: str):
    """Removes multiple users from the blacklist via IDs."""
    lang = get_guild_lang(interaction.guild_id)

    ids_to_remove = user_ids.split()
    removed_count = 0
    not_blacklisted_count = 0

    for user_id in ids_to_remove:
        if user_id in blacklist_data:
            del blacklist_data[user_id]
            removed_count += 1
        else:
            not_blacklisted_count += 1

    save_blacklist(blacklist_data)

    embed = create_embed(
        interaction, "blacklist_messages", "multi_remove_title", discord.Color.green(),
        message=(
                get_message(lang, "blacklist_messages", "multi_remove_success", count=removed_count) +
                (f"\n" + get_message(lang, "blacklist_messages", "multi_remove_fail",
                                     count=not_blacklisted_count) if not_blacklisted_count > 0 else "")
        )
    )
    await interaction.response.send_message(embed=embed)


class BlacklistInfoView(discord.ui.View):
    def __init__(self, interaction, total_pages, blacklist_items, lang):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.current_page = 0
        self.total_pages = total_pages
        self.blacklist_items = blacklist_items
        self.lang = lang
        self.update_buttons()

    def create_page_embed(self, page_number):
        start_index = page_number * 10
        end_index = min((page_number + 1) * 10, len(self.blacklist_items))
        page_items = self.blacklist_items[start_index:end_index]

        embed = discord.Embed(
            title=get_message(self.lang, "blacklist_messages", "blacklist_info_title"),
            description=get_message(self.lang, "blacklist_messages", "blacklist_info_description",
                                    total_users=len(self.blacklist_items),
                                    total_servers=len(self.interaction.client.guilds),
                                    count=len(page_items)
                                    ),
            color=discord.Color.blue()
        )
        embed.set_footer(
            text=f"{MESSAGES['general']['footer']} | Page {page_number + 1}/{self.total_pages}" if self.lang == 'en' else f"{MESSAGES['general']['footer']} | Pagina {page_number + 1}/{self.total_pages}")

        for item in page_items:
            embed.add_field(
                name=f"User ID: `{item['user_id']}`" if self.lang == 'en' else f"Gebruiker ID: `{item['user_id']}`",
                value=f"**Reason:** `{item['reason']}`" if self.lang == 'en' else f"**Reden:** `{item['reason']}`",
                inline=False
            )
        return embed

    def update_buttons(self):
        self.children[0].label = "Previous" if self.lang == 'en' else "Vorige"
        self.children[1].label = "Next" if self.lang == 'en' else "Volgende"
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == self.total_pages - 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = self.create_page_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            embed = self.create_page_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)


@blacklist_group.command(name="info", description="Get info about the blacklist.")
@app_commands.checks.has_permissions(manage_guild=True)
async def get_blacklist_info(interaction: discord.Interaction):
    """Provides an interactive overview of the blacklist."""
    lang = get_guild_lang(interaction.guild_id)

    if not blacklist_data:
        embed = create_embed(
            interaction, "blacklist_messages", "blacklist_info_title", discord.Color.blue(),
            message="The blacklist is currently empty." if lang == 'en' else "De blacklist is momenteel leeg."
        )
        await interaction.response.send_message(embed=embed)
        return

    blacklist_items = []
    for user_id, reason in blacklist_data.items():
        blacklist_items.append({"user_id": user_id, "reason": reason})

    total_pages = math.ceil(len(blacklist_items) / 10)
    view = BlacklistInfoView(interaction, total_pages, blacklist_items, lang)

    initial_embed = view.create_page_embed(0)
    await interaction.response.send_message(embed=initial_embed, view=view)


@blacklist_group.command(name="toggle-dm-server-owner", description="Toggle DM notifications for the server owner.")
@app_commands.checks.has_permissions(manage_guild=True)
async def toggle_dm_server_owner(interaction: discord.Interaction):
    """Toggles DM notifications for the server owner."""
    lang = get_guild_lang(interaction.guild_id)
    server_id = str(interaction.guild_id)

    if server_id not in server_configs:
        server_configs[server_id] = {}

    current_state = server_configs[server_id].get('dm_server_owner', True)
    new_state = not current_state
    server_configs[server_id]['dm_server_owner'] = new_state
    save_configs(server_configs)

    status_text = "enabled" if new_state else "ingeschakeld"
    status_text_nl = "ingeschakeld" if new_state else "uitgeschakeld"
    embed = create_embed(
        interaction, "general", "dm_toggle_title", discord.Color.green(),
        message=f"DM notifications for the server owner are now `{status_text}`." if lang == 'en' else f"DM-meldingen voor de servereigenaar zijn nu `{status_text_nl}`."
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist_group.command(name="setwarningchannel", description="Set the channel for public blacklist warnings.")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_warning_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Sets the channel for public blacklist warnings."""
    lang = get_guild_lang(interaction.guild_id)
    server_id = str(interaction.guild.id)

    if server_id not in server_configs:
        server_configs[server_id] = {}

    server_configs[server_id]['warning_channel_id'] = channel.id
    save_configs(server_configs)

    embed = create_embed(
        interaction, "general", "warning_channel_title", discord.Color.green(),
        message=f"The warning channel has been successfully set to {channel.mention}." if lang == 'en' else f"Het waarschuwingskanaal is succesvol ingesteld op {channel.mention}."
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist_group.command(name="dmserverowners", description="Send a message to all server owners.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dm_server_owners(interaction: discord.Interaction, message: str):
    """Sends a message to all unique server owners who have the bot."""
    lang = get_guild_lang(interaction.guild.id)
    await interaction.response.defer(ephemeral=True)

    sent_owners = set()
    successful_dms = 0
    failed_dms = 0

    for guild in bot.guilds:
        owner = guild.owner
        if owner and owner.id not in sent_owners:
            try:
                await owner.send(message)
                sent_owners.add(owner.id)
                successful_dms += 1
                await asyncio.sleep(1)  # Delay to prevent rate limiting
            except discord.Forbidden:
                failed_dms += 1
            except Exception as e:
                print(f"Error dming owner of guild {guild.name}: {e}")
                failed_dms += 1

    await interaction.followup.send(
        f"Message successfully sent to {successful_dms} unique owners. Failed for {failed_dms} owners." if lang == 'en' else f"Bericht succesvol verzonden naar {successful_dms} unieke eigenaren. Mislukt voor {failed_dms} eigenaren.",
        ephemeral=True)


@settings_group.command(name="setlanguage", description="Set the bot's language (e.g., 'en' or 'nl').")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_language(interaction: discord.Interaction, lang: Literal['en', 'nl']):
    """Stelt de taal van de bot in voor de server."""
    current_lang = get_guild_lang(interaction.guild_id)
    try:
        lang_lower = lang.lower()
        server_id = str(interaction.guild_id)
        if server_id not in server_configs:
            server_configs[server_id] = {}
        server_configs[server_id]['language'] = lang_lower
        save_configs(server_configs)

        embed = create_embed(
            interaction, "set_language_response", "title_success", discord.Color.green(),
            description_key="desc_success", lang_code=lang_lower
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"Error setting language: {e}")
        embed = create_embed(
            interaction, "set_language_response", "title_fail", discord.Color.red(),
            description_key="desc_fail", error=e
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@settings_group.command(name="setupdatechannel", description="Set the update channel for blacklist notifications.")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_update_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Sets the update channel for the server."""
    lang = get_guild_lang(interaction.guild_id)
    server_id = str(interaction.guild_id)
    if server_id not in server_configs:
        server_configs[server_id] = {}
    server_configs[server_id]['update_channel_id'] = channel.id
    save_configs(server_configs)

    embed = discord.Embed(
        title="Update Channel Set" if lang == 'en' else "Updatekanaal Ingesteld",
        description="This channel is now set as the update channel for Fireside. Notifications about blacklisted users will be posted here." if lang == 'en' else "Dit kanaal is nu ingesteld als het updatekanaal voor Fireside. Meldingen van geblackliste gebruikers worden hier geplaatst.",
        color=discord.Color.green()
    )
    embed.set_footer(text=MESSAGES['general']['footer'])
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    lang = get_guild_lang(interaction.guild_id)

    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            embed=create_embed(interaction, "error_messages", "missing_perms_title", discord.Color.red(),
                               message=get_message(lang, "error_messages", "missing_perms")), ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message(
            embed=create_embed(interaction, "error_messages", "bot_perms_missing_title", discord.Color.red(),
                               message=get_message(lang, "error_messages", "bot_perms_missing")), ephemeral=True)
    elif isinstance(error, app_commands.CheckFailure):
        if interaction.guild is None and interaction.command.name != "help":
            await interaction.response.send_message(
                embed=create_embed(interaction, "error_messages", "access_denied", discord.Color.red(),
                                   message=get_message(lang, "error_messages", "dm_only_command")), ephemeral=True)
        elif interaction.user.id != OWNER_ID and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                embed=create_embed(interaction, "error_messages", "owner_check_failed_title", discord.Color.red(),
                                   message=get_message(lang, "error_messages", "owner_check_failed")), ephemeral=True)
        else:
            print(f"CheckFailure but not owner. Interaction: {interaction.command.name}")
    else:
        print(f"Unexpected error with command '{interaction.command.name}': {error}")
        await interaction.response.send_message(
            embed=create_embed(interaction, "error_messages", "unexpected_error_title", discord.Color.red(),
                               error=error), ephemeral=True)


# Start the bot
bot.run(BOT_TOKEN)
