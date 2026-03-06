import os
import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
from dotenv import load_dotenv
import json
import asyncio
import datetime
from typing import Union, List, Literal, Optional, Dict
import math
import aiohttp
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Get bot token and owner ID
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# New environment variables for bot status
BOT_ACTIVITY_TYPE = os.getenv("BOT_ACTIVITY_TYPE", "watching")
BOT_ACTIVITY_MESSAGE = os.getenv("BOT_ACTIVITY_MESSAGE", "over {membercount} members")
BOT_STATUS_TYPE = os.getenv("BOT_STATUS_TYPE", "online").lower()

# Define bot intents (ESSENTIEEL VOOR RUNNABLE CODE)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.presences = True

# Create the bot client
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=OWNER_ID)

# Global variable to store bot start time (for uptime)
bot_start_time = datetime.datetime.now(datetime.timezone.utc)

# Define file names
BLACKLIST_FILE = "blacklist.json"
SERVER_CONFIGS_FILE = "server_configs.json"
MEMBER_DATA_FILE = "member_data.json"
CUSTOM_COMMANDS_FILE = "custom_commands.json"
MODLOG_FILE = "modlog.json"
LOG_CHANNELS_FILE = "log_channels.json"
TICKET_SYSTEM_FILE = "ticket_system.json"
VOICE_CHANNELS_FILE = "voice_channels.json"
REACTION_ROLES_FILE = "reaction_roles.json"
REMINDERS_FILE = "reminders.json"
LEVELING_FILE = "leveling.json"
XP_CONFIG_FILE = "xp_config.json"
GIVEAWAYS_FILE = "giveaways.json"

# Caching mechanism to reduce API calls
_cached_users = {}

# --- Localization strings ---
MESSAGES = {
    "welcome_dm": {
        "nl": "Welkom op onze server! Ik ben de bot en sta klaar om je te helpen. Veel plezier!",
        "en": "Welcome to our server! I'm the bot and ready to help you. Have fun!"
    },
    "goodbye_message": {
        "nl": "Tot ziens, {user}! We hopen je snel weer te zien.",
        "en": "Goodbye, {user}! We hope to see you again soon."
    },
    "info_command": {
        "nl": {
            "title": "Bot Informatie",
            "description": "Mijn hoofdtaak is het beheren van de **Globale Blacklist** om te zorgen dat jouw server veilig en vrij van ongewenste gebruikers blijft. Ik zorg voor real-time controle op nieuwe leden. Ik ben ontwikkeld door {owner_mention}.",
            "uptime": "Uptime",
            "owner": "Bot Eigenaar",
            "commands": "Commando's Geregistreerd",
            "guilds": "Aantal Servers"
        },
        "en": {
            "title": "Bot Information",
            "description": "My primary function is to maintain the **Global Blacklist** to keep your server safe and free from undesirable users. I provide real-time checks on new members. I was developed by {owner_mention}.",
            "uptime": "Uptime",
            "owner": "Bot Owner",
            "commands": "Commands Registered",
            "guilds": "Total Guilds"
        }
    },
    "help_command": {
        "nl": {
            "title": "Beschikbare Commando's",
            "description": "Hieronder zie je de lijst met commando's die jij kunt uitvoeren. (Commando's voor de Bot Eigenaar zijn weggelaten).",
            "admin_section": "⚙️ Beheer & Configuratie",
            "general_section": "ℹ️ Algemeen",
            "blacklist_section": "🚫 Blacklist (Alleen Bot Eigenaar)",
        },
        "en": {
            "title": "Available Commands",
            "description": "Below is the list of commands you are permitted to execute. (Bot Owner commands are excluded).",
            "admin_section": "⚙️ Admin & Configuration",
            "general_section": "ℹ️ General",
            "blacklist_section": "🚫 Blacklist (Bot Owner Only)",
        }
    },
    "error_messages": {
        "nl": {
            "owner_check_failed_title": "Toegang geweigerd",
            "owner_check_failed": "Dit commando kan alleen worden uitgevoerd door de eigenaar van de bot.",
            "guild_owner_check_failed": "Dit commando kan alleen worden uitgevoerd door de server eigenaar of iemand met de juiste permissies.",
            "unexpected_error_title": "Onverwachte Fout",
            "blacklist_title": "Blacklist Beheer",
            "blacklist_show_title": "Globale Blacklist ({type})",
            "blacklist_empty": "De {type} blacklist is leeg.",
            "not_found": "{item} niet gevonden op de blacklist.",
            "already_listed": "{item} staat al op de blacklist.",
            "add_success": "{item} is succesvol toegevoegd aan de blacklist.",
            "remove_success": "{item} is succesvol verwijderd van de blacklist.",
            "invalid_id": "Ongeldig ID opgegeven of ongeldige invoer.",
            "permission_denied": "Je hebt niet de juiste rechten om dit te doen.",
            "user_not_found": "Gebruiker niet gevonden.",
            "role_not_found": "Rol niet gevonden.",
            "channel_not_found": "Kanaal niet gevonden.",
            "invalid_time": "Ongeldige tijdsaanduiding.",
            "command_not_found": "Commando niet gevonden.",
            "lang_set_success_nl": "De servertaal is ingesteld op **Nederlands**.",
            "lang_set_success_en": "De servertaal is ingesteld op **Engels**.",
            "warning_channel_set": "Waarschuwingsberichten voor bans/kicks worden nu naar {channel} gestuurd.",
            "warning_channel_reset": "Waarschuwingsberichten worden niet meer naar een specifiek kanaal gestuurd.",
            "dm_owner_toggled_on": "DM's naar de bot-eigenaar over waarschuwingen zijn nu **ingeschakeld**.",
            "dm_owner_toggled_off": "DM's naar de bot-eigenaar over waarschuwingen zijn nu **uitgeschakeld**.",
        },
        "en": {
            "owner_check_failed_title": "Access Denied",
            "owner_check_failed": "This command can only be executed by the bot owner.",
            "guild_owner_check_failed": "This command can only be executed by the server owner or someone with the right permissions.",
            "unexpected_error_title": "Unexpected Error",
            "blacklist_title": "Blacklist Management",
            "blacklist_show_title": "Global Blacklist ({type})",
            "blacklist_empty": "The {type} blacklist is empty.",
            "not_found": "{item} not found on the blacklist.",
            "already_listed": "{item} is already on the blacklist.",
            "add_success": "{item} successfully added to the blacklist.",
            "remove_success": "{item} successfully removed from the blacklist.",
            "invalid_id": "Invalid ID provided or invalid input.",
            "permission_denied": "You do not have the necessary permissions.",
            "user_not_found": "User not found.",
            "role_not_found": "Role not found.",
            "channel_not_found": "Channel not found.",
            "invalid_time": "Invalid time specification.",
            "command_not_found": "Command not found.",
            "lang_set_success_nl": "The server language has been set to **Dutch**.",
            "lang_set_success_en": "The server language has been set to **English**.",
            "warning_channel_set": "Warning messages for bans/kicks will now be sent to {channel}.",
            "warning_channel_reset": "Warning messages are no longer sent to a specific channel.",
            "dm_owner_toggled_on": "DMs to the bot owner about warnings are now **enabled**.",
            "dm_owner_toggled_off": "DMs to the bot owner about warnings are now **disabled**.",
        }
    }
}


# --- Custom Checks ---
async def is_bot_owner(interaction: discord.Interaction) -> bool:
    """Aangepaste check om te verifiëren of de gebruiker de bot eigenaar is."""
    return await interaction.client.is_owner(interaction.user)


# --- Helper Functions (Load/Save Data) ---
def load_data(file_name: str, default_data: Union[dict, list]) -> Union[dict, list]:
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error loading {file_name}: Invalid JSON. Using default data.")
                return default_data
    return default_data


def save_data(file_name: str, data: Union[dict, list]):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


# --- Server Config Functions ---
def load_server_configs() -> dict:
    """Laadt de server configuratie data."""
    return load_data(SERVER_CONFIGS_FILE, {})


def save_server_configs(data: Dict[str, Dict]):
    """Slaat de server configuratie data op."""
    save_data(SERVER_CONFIGS_FILE, data)


def get_guild_config(guild_id: int) -> Dict:
    """Haalt de configuratie voor een specifieke guild op, met defaults."""
    configs = load_server_configs()
    # Default configuratie: NL, geen waarschuwingskanaal, DM's naar owner AAN
    default_config = {
        'language': 'nl',
        'warning_channel_id': None,
        'dm_owner_on_warning': True,
    }
    return configs.get(str(guild_id), default_config)


def get_guild_lang(guild_id: int) -> str:
    """Haalt de voorkeurstaal van een server op, standaard is NL."""
    return get_guild_config(guild_id)['language']


# --- Localization & Embed Helpers ---
def get_user_lang(user_id: int) -> str:
    # Standaard taal voor DM's of als er geen guild-context is
    return 'nl'


def get_interaction_lang(interaction: discord.Interaction) -> str:
    """Haalt de taal op basis van de interactie (server of NL default)."""
    if interaction.guild:
        return get_guild_lang(interaction.guild_id)
    return get_user_lang(interaction.user.id)


def get_message(lang: str, category: str, key: str, **kwargs) -> str:
    # Fallback to Dutch if the specified language or key is missing
    messages = MESSAGES.get(category, {})
    message = messages.get(lang, messages.get('nl', {})).get(key, f"Missing message for {lang}.{category}.{key}")
    # Handle nested localization for info/help messages
    if isinstance(message, dict):
        return message

    return message.format(**kwargs)


def create_embed(interaction: discord.Interaction, category: str, key: str, color: discord.Color,
                 lang: Optional[str] = None, **kwargs) -> discord.Embed:
    # Gebruikt de nieuwe functie om de taal context te bepalen
    lang = lang or get_interaction_lang(interaction)

    # Voor info/help messages, haal de structuur op
    message_data = get_message(lang, category, key)

    if isinstance(message_data, dict):
        title = message_data.get('title', key)
        description = message_data.get('description', '')
    else:
        # Voor error messages
        title = MESSAGES.get(category, {}).get(lang, {}).get(f"{key}_title", key)
        description = kwargs.pop('message', '')

    error_detail = kwargs.pop('error', None)

    embed = discord.Embed(
        title=title,
        description=description.format(**kwargs),
        color=color
    )
    if error_detail:
        embed.add_field(name=f"Error Details ({lang.upper()})", value=f"```py\n{error_detail}\n```", inline=False)

    return embed


def format_uptime(td: datetime.timedelta) -> str:
    """Formatteert een timedelta object naar een leesbare uptime string in het Nederlands."""
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} dag{'en' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} uur")
    if minutes > 0:
        parts.append(f"{minutes} min")
    # Alleen seconden tonen als er geen grotere eenheden zijn
    if not parts or days == 0 and hours == 0 and minutes < 5:
        parts.append(f"{seconds} sec")

    return ", ".join(parts)


# --- Blacklist Functions (Ongewijzigd, behalve import) ---
# ... (load_blacklist, save_blacklist, add_to_blacklist, remove_from_blacklist, is_blacklisted, etc. blijven hetzelfde)
def load_blacklist() -> dict:
    """
    Laadt de blacklist data van het JSON bestand.
    MIGRATIE: Converteert oude 'blacklisted_users' (lijst) naar het nieuwe 'users' (dict) formaat.
    """
    # 1. Laad de ruwe data, met de verwachte structuur als default
    data = load_data(BLACKLIST_FILE, {"users": {}, "ids": {}})

    # 2. Migratie van het oude lijst-formaat (indien aanwezig)
    if "blacklisted_users" in data and isinstance(data["blacklisted_users"], list):
        print("Migratie gestart: Oude 'blacklisted_users' (lijst) gevonden.")
        migrated_users = {}

        # Converteer elk item in de lijst naar het nieuwe dictionary-formaat
        for entry in data["blacklisted_users"]:
            if 'id' in entry and 'reason' in entry:
                user_id_str = str(entry['id'])
                # Behoud bestaande data of voeg een standaard reden en tijdstempel toe
                migrated_users[user_id_str] = {
                    "reason": entry['reason'],
                    "timestamp": datetime.datetime.now().isoformat()
                }

        # Voeg de gemigreerde gebruikers samen met eventuele nieuwe 'users' data
        data["users"] = {**data.get("users", {}), **migrated_users}

        # Verwijder de oude lijst-sleutel om herhaling van migratie te voorkomen
        del data["blacklisted_users"]

        # Sla onmiddellijk op om het nieuwe formaat vast te leggen
        save_blacklist(data)
        print("Migratie voltooid. Blacklist.json is opgeslagen in het nieuwe formaat.")

    # 3. Zorg ervoor dat beide verwachte sleutels bestaan en dictionaries zijn
    if "users" not in data or not isinstance(data["users"], dict):
        data["users"] = {}
    if "ids" not in data or not isinstance(data["ids"], dict):
        data["ids"] = {}

    return data


def save_blacklist(blacklist_data):
    """Slaat de blacklist data op naar het JSON bestand."""
    save_data(BLACKLIST_FILE, blacklist_data)


def add_to_blacklist(id_str: str, reason: str, type: Literal['users', 'ids'] = 'users'):
    """Voegt een ID toe aan de blacklist."""
    blacklist_data = load_blacklist()
    target_list = blacklist_data.get(type, {})

    if id_str in target_list:
        return False, f"{id_str} is al blacklisted"

    target_list[id_str] = {
        "reason": reason,
        "timestamp": datetime.datetime.now().isoformat()
    }

    blacklist_data[type] = target_list
    save_blacklist(blacklist_data)
    return True, f"{id_str} toegevoegd"


def remove_from_blacklist(id_str: str, type: Literal['users', 'ids'] = 'users'):
    """Verwijdert een ID van de blacklist."""
    blacklist_data = load_blacklist()
    target_list = blacklist_data.get(type, {})

    if id_str not in target_list:
        return False, f"{id_str} niet gevonden"

    del target_list[id_str]

    blacklist_data[type] = target_list
    save_blacklist(blacklist_data)
    return True, f"{id_str} verwijderd"


def is_blacklisted(user_id: int) -> bool:
    """Controleert of een gebruiker op de blacklist staat."""
    blacklist_data = load_blacklist()
    id_str = str(user_id)
    return id_str in blacklist_data.get('users', {}) or id_str in blacklist_data.get('ids', {})


# --- Slash Commands ---
@bot.tree.command(name="ping", description="Check the bot's latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)


@app_commands.command(name="info", description="Toon informatie over de bot, inclusief uptime en eigenaar.")
async def info(interaction: discord.Interaction):
    lang = get_interaction_lang(interaction)

    # Bereken de uptime
    current_time = datetime.datetime.now(datetime.timezone.utc)
    uptime_delta = current_time - bot_start_time
    uptime_formatted = format_uptime(uptime_delta)

    # Probeer de eigenaar op te halen
    owner_user = bot.get_user(OWNER_ID)
    owner_mention = f"<@{OWNER_ID}>" if owner_user else f"ID: {OWNER_ID}"

    info_texts = get_message(lang, "info_command", "info")

    embed = create_embed(
        interaction,
        "info_command",
        "info",
        discord.Color.gold(),
        owner_mention=owner_mention  # Geef de eigenaar mention door aan de description format
    )

    embed.add_field(name=info_texts['uptime'], value=uptime_formatted, inline=False)
    embed.add_field(name=info_texts['owner'], value=owner_mention, inline=True)
    embed.add_field(name=info_texts['commands'], value=len(bot.tree.get_commands()), inline=True)
    embed.add_field(name=info_texts['guilds'], value=len(bot.guilds), inline=True)
    embed.set_thumbnail(url=bot.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)


@app_commands.command(name="help", description="Toon een lijst van alle commando's die je mag gebruiken.")
async def help_command(interaction: discord.Interaction):
    lang = get_interaction_lang(interaction)
    help_texts = get_message(lang, "help_command", "help")

    embed = create_embed(
        interaction,
        "help_command",
        "help",
        discord.Color.dark_purple()
    )

    # Commando's filteren en groeperen
    commands_map: Dict[str, List[app_commands.AppCommand]] = {
        "admin": [],
        "general": [],
    }

    # Hulpfunctie om te controleren of de gebruiker permissie heeft
    async def user_can_run(command: app_commands.AppCommand, interaction: discord.Interaction) -> bool:
        # Dit is de meest betrouwbare manier om te controleren of een check faalt zonder de command uit te voeren.
        # We negeren hier de complexe checks (zoals is_bot_owner) in de help-lijst
        # omdat deze puur voor de eigenaar zijn.

        # Commando's voor de Bot Eigenaar (specifieke check)
        is_owner_cmd = any(check.__qualname__.split('.')[0] == 'is_bot_owner' for check in command.checks)
        if is_owner_cmd:
            return False  # Eigenaar-only commando's worden niet getoond in de algemene help

        # Overige checks (permissions, roles)
        try:
            # Controleer ingebouwde permissievereisten
            if command.default_permissions and interaction.app_permissions.value & command.default_permissions.value != command.default_permissions.value:
                return False
        except AttributeError:
            pass  # Geen permissies ingesteld

        return True

    # Verzamel alle commands, inclusief die in groepen
    all_commands = bot.tree.get_commands()
    for cmd in all_commands:
        if isinstance(cmd, app_commands.Group):
            # Groepen worden genegeerd, alleen subcommands tonen
            for sub_cmd in cmd.commands:
                if await user_can_run(sub_cmd, interaction):
                    if 'blacklist' in cmd.name:  # Blacklist is nu Bot Owner only
                        continue
                    elif sub_cmd.name in ['setlanguage', 'setwarningchannel', 'toggledmowner']:
                        commands_map['admin'].append(sub_cmd)
                    else:
                        commands_map['general'].append(sub_cmd)

        elif await user_can_run(cmd, interaction):
            if cmd.name in ['setlanguage', 'setwarningchannel', 'toggledmowner']:
                commands_map['admin'].append(cmd)
            else:
                commands_map['general'].append(cmd)

    # Maak de velden voor de embed
    # Admin commands
    admin_commands = [f"`/{cmd.name}`: {cmd.description}" for cmd in commands_map['admin']]
    if admin_commands:
        embed.add_field(name=help_texts['admin_section'], value="\n".join(admin_commands), inline=False)

    # General commands
    general_commands = [f"`/{cmd.name}`: {cmd.description}" for cmd in commands_map['general']]
    if general_commands:
        embed.add_field(name=help_texts['general_section'], value="\n".join(general_commands), inline=False)

    # Blacklist commands (alleen voor de Bot Eigenaar, dus alleen als reminder)
    blacklist_cmds = [f"`/{cmd.name}`" for group in bot.tree.get_commands() if
                      isinstance(group, app_commands.Group) and group.name == 'blacklist' for cmd in group.commands]
    if blacklist_cmds:
        embed.add_field(name=help_texts['blacklist_section'], value=f"Commando's: {', '.join(blacklist_cmds)}",
                        inline=False)

    if not admin_commands and not general_commands:
        embed.description = "Je hebt momenteel geen commando's die je mag uitvoeren. Probeer `/info`."

    await interaction.response.send_message(embed=embed, ephemeral=True)


@app_commands.command(name="setwarningchannel",
                      description="Stel het kanaal in voor waarschuwingsberichten bij kicks/bans.")
@app_commands.describe(channel="Het kanaal om waarschuwingen naartoe te sturen. Leeg laten om te resetten.")
@app_commands.checks.has_permissions(administrator=True)
async def set_warning_channel(interaction: discord.Interaction, channel: Optional[discord.TextChannel]):
    if not interaction.guild:
        return await interaction.response.send_message("Dit commando kan alleen in een server gebruikt worden.",
                                                       ephemeral=True)

    guild_id = str(interaction.guild_id)
    configs = load_server_configs()

    if guild_id not in configs:
        configs[guild_id] = get_guild_config(interaction.guild_id)

    lang = get_interaction_lang(interaction)

    if channel:
        configs[guild_id]['warning_channel_id'] = channel.id
        save_server_configs(configs)
        message = get_message(lang, "error_messages", "warning_channel_set", channel=channel.mention)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.green(), message=message)
    else:
        configs[guild_id]['warning_channel_id'] = None
        save_server_configs(configs)
        message = get_message(lang, "error_messages", "warning_channel_reset")
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.orange(), message=message)

    await interaction.response.send_message(embed=embed)


@app_commands.command(name="toggledmowner",
                      description="Schakelt DM's naar de bot-eigenaar over waarschuwingen AAN/UIT.")
@app_commands.checks.has_permissions(administrator=True)
async def toggle_dm_owner(interaction: discord.Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("Dit commando kan alleen in een server gebruikt worden.",
                                                       ephemeral=True)

    guild_id = str(interaction.guild_id)
    configs = load_server_configs()

    if guild_id not in configs:
        configs[guild_id] = get_guild_config(interaction.guild_id)

    lang = get_interaction_lang(interaction)

    # Toggle de instelling
    current_setting = configs[guild_id].get('dm_owner_on_warning', True)
    new_setting = not current_setting
    configs[guild_id]['dm_owner_on_warning'] = new_setting
    save_server_configs(configs)

    if new_setting:
        message = get_message(lang, "error_messages", "dm_owner_toggled_on")
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.green(), message=message)
    else:
        message = get_message(lang, "error_messages", "dm_owner_toggled_off")
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.orange(), message=message)

    await interaction.response.send_message(embed=embed)


# Voeg set_language toe
@app_commands.command(name="setlanguage", description="Stel de voorkeurstaal voor deze server in (Admin vereist).")
@app_commands.describe(language="Kies de taal: nl (Nederlands) of en (Engels).")
@app_commands.checks.has_permissions(administrator=True)
async def set_language(interaction: discord.Interaction, language: Literal['nl', 'en']):
    if not interaction.guild:
        # Hier gebruiken we de standaardtaal NL (get_user_lang)
        return await interaction.response.send_message("Dit commando kan alleen in een server gebruikt worden.",
                                                       ephemeral=True)

    guild_id = str(interaction.guild_id)
    configs = load_server_configs()

    if guild_id not in configs:
        configs[guild_id] = get_guild_config(interaction.guild_id)  # Zorg voor defaults

    configs[guild_id]['language'] = language
    save_server_configs(configs)

    # Gebruik de NIEUWE taal om de bevestiging te versturen
    key = f"lang_set_success_{language}"

    embed = create_embed(
        interaction,
        "error_messages",
        "lang_set_success",  # Gebruik een algemene key voor de titel
        discord.Color.blue(),
        lang=language,
        message=get_message(language, "error_messages", key)
    )
    await interaction.response.send_message(embed=embed)


# Maak de blacklist command group
blacklist = app_commands.Group(name="blacklist", description="Beheer de globale blacklist.")


# -----------------------------------------------------------
# COMMANDS MET BOT OWNER RESTRICTIE (GECORRIGEERD met de nieuwe is_bot_owner check)
# -----------------------------------------------------------

@blacklist.command(name="addid", description="Voeg een ID (Guild of ander) toe aan de blacklist.")
@app_commands.describe(id="Het ID om toe te voegen.", reden="De reden voor de blacklist.")
@app_commands.check(is_bot_owner)  # <<< FIX: Gebruik de custom check
async def add_id(interaction: discord.Interaction, id: str, reden: str):
    lang = get_interaction_lang(interaction)
    success, result = add_to_blacklist(id, reden, type='ids')

    if success:
        message = get_message(lang, "error_messages", "add_success", item=id)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.green(), message=message)
    else:
        message = get_message(lang, "error_messages", "already_listed", item=id)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.orange(), message=message)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist.command(name="addidmore", description="Voeg meerdere ID's toe aan de blacklist. Gescheiden door een komma.")
@app_commands.describe(ids="De ID's om toe te voegen (gescheiden door komma's).", reden="De reden voor de blacklist.")
@app_commands.check(is_bot_owner)  # <<< FIX: Gebruik de custom check
async def add_id_more(interaction: discord.Interaction, ids: str, reden: str):
    id_list = [i.strip() for i in ids.split(',') if i.strip()]
    added_ids = []
    already_listed = []

    for id_str in id_list:
        success, _ = add_to_blacklist(id_str, reden, type='ids')
        if success:
            added_ids.append(id_str)
        else:
            already_listed.append(id_str)

    lang = get_interaction_lang(interaction)
    message = ""
    if added_ids:
        message += get_message(lang, "error_messages", "add_success",
                               item=f"**{len(added_ids)}** ID's ({', '.join(added_ids[:5])}...)") + "\n"
    if already_listed:
        message += get_message(lang, "error_messages", "already_listed",
                               item=f"**{len(already_listed)}** ID's ({', '.join(already_listed[:5])}...)") + "\n"

    color = discord.Color.green() if added_ids else discord.Color.orange()
    embed = create_embed(interaction, "error_messages", "blacklist", color, message=message)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist.command(name="adduser", description="Voeg een Gebruiker toe aan de blacklist.")
@app_commands.describe(user="De gebruiker om toe te voegen.", reden="De reden voor de blacklist.")
@app_commands.check(is_bot_owner)  # <<< FIX: Gebruik de custom check
async def add_user(interaction: discord.Interaction, user: discord.User, reden: str):
    lang = get_interaction_lang(interaction)
    id_str = str(user.id)
    success, result = add_to_blacklist(id_str, reden, type='users')

    if success:
        message = get_message(lang, "error_messages", "add_success", item=user.mention)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.green(), message=message)
    else:
        message = get_message(lang, "error_messages", "already_listed", item=user.mention)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.orange(), message=message)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist.command(name="removeuser", description="Verwijder een gebruiker van de blacklist.")
@app_commands.describe(user="De gebruiker om te verwijderen.")
@app_commands.check(is_bot_owner)  # <<< FIX: Gebruik de custom check
async def remove_user(interaction: discord.Interaction, user: discord.User):
    lang = get_interaction_lang(interaction)
    id_str = str(user.id)
    success, result = remove_from_blacklist(id_str, type='users')

    if success:
        message = get_message(lang, "error_messages", "remove_success", item=user.mention)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.green(), message=message)
    else:
        message = get_message(lang, "error_messages", "not_found", item=user.mention)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.orange(), message=message)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist.command(name="removeid", description="Verwijder een enkel ID van de blacklist.")
@app_commands.describe(id="Het ID om te verwijderen.")
@app_commands.check(is_bot_owner)  # <<< FIX: Gebruik de custom check
async def remove_id(interaction: discord.Interaction, id: str):
    lang = get_interaction_lang(interaction)
    success, result = remove_from_blacklist(id, type='ids')

    if success:
        message = get_message(lang, "error_messages", "remove_success", item=id)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.green(), message=message)
    else:
        message = get_message(lang, "error_messages", "not_found", item=id)
        embed = create_embed(interaction, "error_messages", "blacklist", discord.Color.orange(), message=message)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklist.command(name="removeidmore",
                   description="Verwijder meerdere ID's van de blacklist. Gescheiden door een komma.")
@app_commands.describe(ids="De ID's om te verwijderen (gescheiden door komma's).")
@app_commands.check(is_bot_owner)  # <<< FIX: Gebruik de custom check
async def remove_id_more(interaction: discord.Interaction, ids: str):
    id_list = [i.strip() for i in ids.split(',') if i.strip()]
    removed_ids = []
    not_found = []

    for id_str in id_list:
        success, _ = remove_from_blacklist(id_str, type='ids')
        if success:
            removed_ids.append(id_str)
        else:
            not_found.append(id_str)

    lang = get_interaction_lang(interaction)
    message = ""
    if removed_ids:
        message += get_message(lang, "error_messages", "remove_success",
                               item=f"**{len(removed_ids)}** ID's ({', '.join(removed_ids[:5])}...)") + "\n"
    if not_found:
        message += get_message(lang, "error_messages", "not_found",
                               item=f"**{len(not_found)}** ID's ({', '.join(not_found[:5])}...)") + "\n"

    color = discord.Color.green() if removed_ids else discord.Color.orange()
    embed = create_embed(interaction, "error_messages", "blacklist", color, message=message)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# -----------------------------------------------------------
# COMMAND MET FIX EN PAGINATIE (AANGEPAST)
# -----------------------------------------------------------

class BlacklistPaginator(ui.View):
    """View voor het navigeren door de blacklist pagina's."""

    def __init__(self, interaction: discord.Interaction, blacklist_data: dict, list_type: str,
                 entries_per_page: int = 10):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.list_type = list_type
        # Converteer de dictionary items naar een lijst van tuples voor gemakkelijke paginatie
        self.entries = list(blacklist_data.items())
        self.entries_per_page = entries_per_page
        self.max_pages = math.ceil(len(self.entries) / entries_per_page) if self.entries else 1
        self.current_page = 1
        self.lang = get_interaction_lang(interaction)

        # Initieel de knoppen updaten
        self.update_buttons()

    def update_buttons(self):
        """Knoppen in- of uitschakelen op basis van de huidige pagina."""
        # Check of er knoppen zijn
        if len(self.children) >= 2:
            # De eerste twee children zijn de knoppen
            self.children[0].disabled = self.current_page == 1  # Vorige
            self.children[1].disabled = self.current_page == self.max_pages  # Volgende

            # De paginanummering op de knoppen weergeven
            self.children[0].label = f"Vorige (Pagina {self.current_page - 1})" if self.current_page > 1 else "Vorige"
            self.children[
                1].label = f"Volgende (Pagina {self.current_page + 1})" if self.current_page < self.max_pages else "Volgende"

    def create_page_embed(self) -> discord.Embed:
        """Maakt de embed voor de huidige pagina."""
        start_index = (self.current_page - 1) * self.entries_per_page
        end_index = start_index + self.entries_per_page
        page_entries = self.entries[start_index:end_index]

        target_name = "Gebruikers" if self.list_type == 'users' else "ID's"

        embed = create_embed(self.interaction, "error_messages", "blacklist_show", discord.Color.blue(),
                             type=target_name)
        embed.set_footer(text=f"Pagina {self.current_page}/{self.max_pages} | Totaal: {len(self.entries)}")

        if not self.entries:
            embed.description = get_message(self.lang, "error_messages", "blacklist_empty", type=target_name)
            return embed

        description_lines = []
        for id_str, data in page_entries:
            reason = data.get("reason", "Geen reden opgegeven")
            timestamp = data.get("timestamp")

            # Probeer de gebruiker/guild op te halen voor een mooie weergave, indien mogelijk
            if self.list_type == 'users':
                try:
                    display_name = f"<@{id_str}>"  # Maakt een mention, zelfs als de user niet in cache zit
                except ValueError:
                    display_name = f"Ongeldig Gebruikers-ID ({id_str})"
            # Voor 'ids' geven we alleen het ID weer
            else:
                display_name = id_str

            line = f"**{display_name}** (`{id_str}`)\n" \
                   f"   Reden: *{reason}*\n"
            if timestamp:
                # Probeer een leesbare tijd te maken (Discord timestamp)
                try:
                    dt_object = datetime.datetime.fromisoformat(timestamp)
                    line += f"   Datum: <t:{int(dt_object.timestamp())}:D>"
                except ValueError:
                    line += f"   Datum: Onbekend"

            description_lines.append(line)

        embed.description = "\n".join(description_lines)
        return embed

    async def send_initial_response(self):
        """Stuurt de eerste pagina en de view."""
        self.update_buttons()

        # De knoppen verbergen als er maar één pagina is
        if self.max_pages <= 1:
            # We moeten de view verwijderen voor de respons, maar eerst de knoppen uit de view halen
            view_to_send = None
            if len(self.children) >= 2:
                # Maak een tijdelijke view zonder de knoppen
                view_to_send = ui.View()

            await self.interaction.response.send_message(embed=self.create_page_embed(), view=view_to_send,
                                                         ephemeral=True)
        else:
            # Stuur de initiële respons met knoppen
            await self.interaction.response.send_message(embed=self.create_page_embed(), view=self, ephemeral=True)

    async def update_page(self):
        """Wijzigt de embed van het originele bericht naar de huidige pagina."""
        self.update_buttons()
        await self.interaction.edit_original_response(embed=self.create_page_embed(), view=self)

    @ui.button(label="Vorige", style=discord.ButtonStyle.blurple, emoji="⬅️", custom_id="previous_page")
    async def previous_button(self, interaction: discord.Interaction, button: ui.Button):
        # Zorg ervoor dat alleen de oorspronkelijke gebruiker kan interageren
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message("Dit is niet jouw knop!", ephemeral=True)

        if self.current_page > 1:
            self.current_page -= 1
            await self.update_page()
        # We gebruiken defer() als we de knop niet direct willen updaten
        await interaction.response.defer()

    @ui.button(label="Volgende", style=discord.ButtonStyle.blurple, emoji="➡️", custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        # Zorg ervoor dat alleen de oorspronkelijke gebruiker kan interageren
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message("Dit is niet jouw knop!", ephemeral=True)

        if self.current_page < self.max_pages:
            self.current_page += 1
            await self.update_page()
        await interaction.response.defer()

    async def on_timeout(self):
        """Schakelt knoppen uit bij time-out."""
        try:
            # Probeer het oorspronkelijke bericht bij te werken om de knoppen uit te schakelen
            for item in self.children:
                item.disabled = True
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            # Bericht is al verwijderd, geen actie nodig
            pass
        except Exception:
            # Andere fouten negeren
            pass


@blacklist.command(name="showblacklist", description="Toon de huidige globale blacklist.")
@app_commands.describe(type="Type blacklist om weer te geven: users of IDs.")
async def show_blacklist(interaction: discord.Interaction, type: Literal['users', 'ids'] = 'users'):
    """Toont de blacklist met paginatie."""
    # 1. Laad data
    blacklist_data = load_blacklist()

    # 2. Selecteer de juiste dictionary
    target_data = blacklist_data.get(type, {})

    # 3. Initialiseer en stuur de paginator
    view = BlacklistPaginator(interaction, target_data, type)
    await view.send_initial_response()


# Voeg de command group en nieuwe commands toe aan de bot tree
bot.tree.add_command(blacklist)
bot.tree.add_command(set_language)
bot.tree.add_command(info)
bot.tree.add_command(help_command)
bot.tree.add_command(set_warning_channel)
bot.tree.add_command(toggle_dm_owner)


# --- Bot Event Handlers ---
@bot.event
async def on_ready():
    # Zorg ervoor dat de starttijd correct is ingesteld zodra de bot klaar is
    global bot_start_time
    bot_start_time = datetime.datetime.now(datetime.timezone.utc)

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        # Synchroniseer commands
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    if not update_bot_status.is_running():
        update_bot_status.start()
    if not check_reminders.is_running():
        check_reminders.start()
    # ... (andere start-up logica)


@bot.event
async def on_member_join(member: discord.Member):
    # Controleer of de gebruiker op de blacklist staat
    if is_blacklisted(member.id):
        try:
            id_str = str(member.id)
            # Haal configuratie en reden op
            guild_config = get_guild_config(member.guild.id)
            lang = guild_config['language']
            reason = load_blacklist().get('users', {}).get(id_str, {}).get('reason', 'Geen reden opgegeven')

            # 1. DM de gebruiker
            dm_message = f"Je bent van de server **{member.guild.name}** verbannen omdat je op de globale blacklist staat. Reden: {reason}"
            try:
                await member.send(dm_message)
            except discord.Forbidden:
                print(f"Kan gebruiker {member.id} geen DM sturen.")

            # 2. Ban de gebruiker
            await member.ban(reason=f"Globale Blacklist: {reason}")
            print(f"Gebruiker {member.id} is verbannen vanwege de globale blacklist.")

            # 3. Stuur waarschuwing naar kanaal (indien ingesteld)
            warning_channel_id = guild_config.get('warning_channel_id')
            if warning_channel_id:
                channel = member.guild.get_channel(warning_channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    warning_embed = discord.Embed(
                        title="🚫 Gebruiker Verwijderd van Blacklist",
                        description=f"De blacklisted gebruiker **{member.name}** (`{id_str}`) probeerde de server te joinen en is automatisch verbannen.",
                        color=discord.Color.red()
                    )
                    warning_embed.add_field(name="Reden Blacklist", value=reason, inline=False)
                    await channel.send(embed=warning_embed)

            # 4. DM de bot eigenaar (indien ingeschakeld)
            if guild_config.get('dm_owner_on_warning', True):
                owner = bot.get_user(OWNER_ID)
                if owner:
                    owner_dm_embed = discord.Embed(
                        title=f"🚨 Blacklist Waarschuwing in {member.guild.name}",
                        description=f"Gebruiker **{member.name}** (`{id_str}`) is succesvol **verbannen** na joinen.",
                        color=discord.Color.dark_red()
                    )
                    owner_dm_embed.add_field(name="Reden", value=reason, inline=False)
                    await owner.send(embed=owner_dm_embed)


        except discord.Forbidden:
            # Bot heeft geen ban permissies
            print(f"Kan gebruiker {member.id} niet verbannen (Forbidden).")
        except Exception as e:
            print(f"Fout bij het afhandelen van de blacklist check voor {member.id}: {e}")


# ... (Andere event handlers hier, inclusief on_message, leveling, etc.)

# --- Taken Loops (Uit de originele code) ---
@tasks.loop(minutes=10)
async def update_bot_status():
    activity_type_map = {
        "playing": discord.ActivityType.playing, "watching": discord.ActivityType.watching,
        "listening": discord.ActivityType.listening, "streaming": discord.ActivityType.streaming,
    }
    status_map = {
        "online": discord.Status.online, "idle": discord.Status.idle,
        "dnd": discord.Status.dnd, "invisible": discord.Status.invisible,
    }
    try:
        member_count = sum(guild.member_count for guild in bot.guilds if guild.member_count is not None)
        message = BOT_ACTIVITY_MESSAGE.format(membercount=member_count)
        activity_type = activity_type_map.get(BOT_ACTIVITY_TYPE.lower(), discord.ActivityType.watching)
        status_type = status_map.get(BOT_STATUS_TYPE, discord.Status.online)
        activity = discord.Activity(type=activity_type, name=message)
        await bot.change_presence(status=status_type, activity=activity)
    except Exception as e:
        print(f"Fout bij het updaten van de bot status: {e}")


@tasks.loop(minutes=1)
async def check_reminders():
    # ... (reminder check logica, ongewijzigd)
    pass


# --- Error Handling (AANGEPAST) ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    send_func = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
    lang = get_interaction_lang(interaction)

    # Probeer de fout af te handelen
    try:
        if isinstance(error, app_commands.CheckFailure):
            # Controle op permissies (Admin check)
            if isinstance(error, app_commands.MissingPermissions) or isinstance(error, app_commands.MissingRole):
                await send_func(
                    embed=create_embed(interaction, "error_messages", "permission_denied", discord.Color.red(),
                                       message=get_message(lang, "error_messages", "permission_denied")),
                    ephemeral=True)

            # Controle op Bot Owner check (custom is_bot_owner)
            elif isinstance(error, app_commands.AppCommandCheckFailure):
                await send_func(
                    embed=create_embed(interaction, "error_messages", "owner_check_failed_title", discord.Color.red(),
                                       message=get_message(lang, "error_messages", "owner_check_failed")),
                    ephemeral=True)

            # Controle op Missing Permissions van de bot zelf
            elif isinstance(error, app_commands.BotMissingPermissions):
                await send_func(
                    embed=create_embed(interaction, "error_messages", "unexpected_error_title", discord.Color.red(),
                                       message=f"De bot mist de volgende permissie(s) om dit te doen: {', '.join(error.missing_permissions)}"),
                    ephemeral=True)

            else:
                # Andere onverwachte check failures
                await send_func(
                    embed=create_embed(interaction, "error_messages", "owner_check_failed_title", discord.Color.red(),
                                       message=get_message(lang, "error_messages", "owner_check_failed")),
                    ephemeral=True)

        elif isinstance(error, ValueError):
            await send_func(
                embed=create_embed(interaction, "error_messages", "unexpected_error_title", discord.Color.red(),
                                   message=get_message(lang, "error_messages", "invalid_id")), ephemeral=True)
        else:
            # Algemene onverwachte fouten
            print(f"Unexpected error with command '{interaction.command.name}': {error} ({type(error)})")
            await send_func(
                embed=create_embed(interaction, "error_messages", "unexpected_error_title", discord.Color.red(),
                                   message="Er is een Onverwachte Fout Opgetreden.", error=error), ephemeral=True)

    except Exception as final_e:
        # Als er een fout optreedt tijdens het versturen van de foutmelding
        print(f"FATALE FOUT bij het afhandelen van een fout: {final_e}")


# Start the bot
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Fout: BOT_TOKEN is niet ingesteld in de omgevingsvariabelen.")
