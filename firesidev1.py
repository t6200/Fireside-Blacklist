import os

import discord

from discord import app_commands, ui

from discord.ext import commands

from dotenv import load_dotenv

import json

import asyncio

import datetime

from typing import Union

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID"))

BOT_ACTIVITY_TYPE = os.getenv("BOT_ACTIVITY_TYPE", "watching")

BOT_ACTIVITY_MESSAGE = os.getenv("BOT_ACTIVITY_MESSAGE", "over {guildcount} servers")

BOT_STATUS_TYPE = os.getenv("BOT_STATUS_TYPE", "online").lower()

intents = discord.Intents.default()

intents.members = True

intents.message_content = True

intents.guilds = True

intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents, owner_id=OWNER_ID, help_command=None)

pending_requests = {}

BLACKLIST_FILE = "blacklist.json"

CONFIG_FILE = "config.json"

APPROVED_SERVERS_FILE = "approved_servers.json"

ACTION_HISTORY_FILE = "action_history.json"

PENDING_SERVERS_FILE = "pending_servers.json"

PENDING_DM_FILE = "pending_dms.json"

def load_blacklist():

    """Laad de blacklist vanuit het JSON-bestand."""

    if not os.path.exists(BLACKLIST_FILE):

        return {"blacklisted_users": [], "blacklisted_servers": []}

    with open(BLACKLIST_FILE, 'r') as f:

        try:

            data = json.load(f)

            if isinstance(data, dict) and "blacklisted_users" in data:

                if not isinstance(data.get("blacklisted_servers"), list) or
                        (data.get("blacklisted_servers") and isinstance(data["blacklisted_servers"][0], int)):

                    old_server_list = data["blacklisted_servers"]

                    data["blacklisted_servers"] = [{"id": s_id, "reason": "Geen reden opgegeven."} for s_id in

                                                   old_server_list]

                return data

            else:

                return {

                    "blacklisted_users": [{"id": user_id, "reason": "Geen reden opgegeven."} for user_id in data],

                    "blacklisted_servers": []

                }

        except (json.JSONDecodeError, IndexError):

            return {"blacklisted_users": [], "blacklisted_servers": []}

def save_blacklist(blacklist_data):

    """Sla de blacklist op in het JSON-bestand."""

    with open(BLACKLIST_FILE, 'w') as f:

        json.dump(blacklist_data, f, indent=4)

def load_config():

    """Laad de configuratie vanuit het JSON-bestand."""

    if not os.path.exists(CONFIG_FILE):

        default_config = {"notify_on_update": False}

        with open(CONFIG_FILE, 'w') as f:

            json.dump(default_config, f, indent=4)

        return default_config

    with open(CONFIG_FILE, 'r') as f:

        config_data = json.load(f)

        if "notify_on_update" not in config_data:

            config_data["notify_on_update"] = False

            save_config(config_data)

        return config_data

def save_config(config_data):

    """Sla de configuratie op in het JSON-bestand."""

    with open(CONFIG_FILE, 'w') as f:

        json.dump(config_data, f, indent=4)

def load_approved_servers():

    """Laad de lijst met goedgekeurde server-ID's."""

    if not os.path.exists(APPROVED_SERVERS_FILE):

        return []

    with open(APPROVED_SERVERS_FILE, 'r') as f:

        try:

            return json.load(f)

        except json.JSONDecodeError:

            return []

def save_approved_servers(approved_servers_data):

    """Sla de goedgekeurde server-ID's op in het JSON-bestand."""

    with open(APPROVED_SERVERS_FILE, 'w') as f:

        json.dump(approved_servers_data, f, indent=4)

def load_pending_servers():

    """Laadt de lijst met servers in afwachting van goedkeuring."""

    if not os.path.exists(PENDING_SERVERS_FILE):

        return []

    with open(PENDING_SERVERS_FILE, 'r') as f:

        try:

            return json.load(f)

        except json.JSONDecodeError:

            return []

def save_pending_servers(pending_servers_data):

    """Sla de servers in afwachting van goedkeuring op in het JSON-bestand."""

    with open(PENDING_SERVERS_FILE, 'w') as f:

        json.dump(pending_servers_data, f, indent=4)

def load_pending_dms():

    """Laadt de ID's van de wachtende DM berichten."""

    if not os.path.exists(PENDING_DM_FILE):

        return {}

    with open(PENDING_DM_FILE, 'r') as f:

        try:

            return {int(k): v for k, v in json.load(f).items()}

        except json.JSONDecodeError:

            return {}

def save_pending_dms(pending_dms_data):

    """Slaat de ID's van de wachtende DM berichten op."""

    with open(PENDING_DM_FILE, 'w') as f:

        json.dump(pending_dms_data, f, indent=4)

def load_action_history():

    """Laad de actiegeschiedenis vanuit het JSON-bestand."""

    if not os.path.exists(ACTION_HISTORY_FILE):

        return []

    with open(ACTION_HISTORY_FILE, 'r') as f:

        try:

            return json.load(f)

        except json.JSONDecodeError:

            return []

def save_action_history(history_data):

    """Sla de actiegeschiedenis op in het JSON-bestand."""

    with open(ACTION_HISTORY_FILE, 'w') as f:

        json.dump(history_data, f, indent=4)

blacklist = load_blacklist()

config = load_config()

approved_servers = load_approved_servers()

pending_servers = load_pending_servers()

action_history = load_action_history()

pending_dms = load_pending_dms()

def create_footer_embed(title, description, color=discord.Color.blue()):

    """Maakt een embed met een standaard voettekst."""

    embed = discord.Embed(title=title, description=description, color=color)

    embed.set_footer(text="fireside | made by t_62__")

    return embed

class ModerationView(discord.ui.View):

    def __init__(self, member, guild):

        super().__init__()

        self.member = member

        self.guild = guild

    async def record_action(self, action_type):

        action_entry = {

            "user_id": self.member.id,

            "guild_id": self.guild.id,

            "action": action_type,

            "timestamp": datetime.datetime.now().isoformat()

        }

        action_history.append(action_entry)

        save_action_history(action_history)

    @discord.ui.button(label="Verban", style=discord.ButtonStyle.danger)

    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        """Knop om de gebruiker te verbannen."""

        try:

            await self.guild.ban(self.member, reason="Verbannen via blacklist waarschuwing.")

            await interaction.response.send_message(

                f"`{self.member.name}` is succesvol verbannen uit `{self.guild.name}`.", ephemeral=True)

            await self.record_action("Verbannen")

            self.stop()

        except discord.Forbidden:

            await interaction.response.send_message("Ik heb niet de juiste rechten om deze gebruiker te verbannen.",

                                                    ephemeral=True)

            self.stop()

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.primary)

    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        """Knop om de gebruiker te kicken."""

        try:

            await self.guild.kick(self.member, reason="Gekickt via blacklist waarschuwing.")

            await interaction.response.send_message(

                f"`{self.member.name}` is succesvol gekickt uit `{self.guild.name}`.", ephemeral=True)

            await self.record_action("Gekickt")

            self.stop()

        except discord.Forbidden:

            await interaction.response.send_message("Ik heb niet de juiste rechten om deze gebruiker te kicken.",

                                                    ephemeral=True)

            self.stop()

    @discord.ui.button(label="Laat Staan", style=discord.ButtonStyle.secondary)

    async def ignore_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        """Knop om geen actie te ondernemen."""

        await interaction.response.send_message(

            f"Actie geannuleerd voor `{self.member.name}`. De gebruiker blijft in de server.", ephemeral=True)

        await self.record_action("Genegeerd")

        self.stop()

class AccessButtons(discord.ui.View):

    def __init__(self, owner: discord.Member, original_message: discord.Message):

        super().__init__(timeout=None)

        self.owner = owner

        self.original_message = original_message

        self.guild_id = original_message.guild.id

    @discord.ui.button(label="Goedkeuren", style=discord.ButtonStyle.success)

    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != OWNER_ID:

            await interaction.response.send_message("Alleen de bot-eigenaar kan dit doen.", ephemeral=True)

            return

        guild = bot.get_guild(self.original_message.guild_id)

        if not guild:

            await interaction.response.send_message("Server niet gevonden.", ephemeral=True)

            return

        if guild.id not in approved_servers:

            approved_servers.append(guild.id)

            save_approved_servers(approved_servers)

            if guild.id in pending_servers:

                pending_servers.remove(guild.id)

                save_pending_servers(pending_servers)

        embed_approved = create_footer_embed(

            title="✅ Toegang Goedgekeurd",

            description=f"Je verzoek om toegang tot **{guild.name}** is succesvol goedgekeurd."

        )

        await self.original_message.edit(embed=embed_approved, view=None)

        await interaction.response.send_message(f"Toegang goedgekeurd voor **{guild.name}** (`{guild.id}`).",

                                                ephemeral=True)

    @discord.ui.button(label="Weigeren", style=discord.ButtonStyle.danger)

    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != OWNER_ID:

            await interaction.response.send_message("Alleen de bot-eigenaar kan dit doen.", ephemeral=True)

            return

        guild = bot.get_guild(self.original_message.guild_id)

        if not guild:

            await interaction.response.send_message("Server niet gevonden.", ephemeral=True)

            return

        if guild.id in approved_servers:

            approved_servers.remove(guild.id)

            save_approved_servers(approved_servers)

        if guild.id in pending_servers:

            pending_servers.remove(guild.id)

            save_pending_servers(pending_servers)

        embed_denied = create_footer_embed(

            title="❌ Toegang Geweigerd",

            description=f"Je verzoek om toegang tot **{guild.name}** is geweigerd."

        )

        await self.original_message.edit(embed=embed_denied, view=None)

        await interaction.response.send_message(f"Toegang geweigerd voor **{guild.name}** (`{guild.id}`).",

                                                ephemeral=True)

def is_bot_dev(interaction: discord.Interaction) -> bool:

    """Controleer of de gebruiker de botontwikkelaar is."""

    return interaction.user.id == OWNER_ID

def is_server_owner(interaction: discord.Interaction) -> bool:

    """Controleer of de gebruiker de servereigenaar is."""

    return interaction.user.id == interaction.guild.owner_id

def is_access_approved(interaction: discord.Interaction) -> bool:

    """Controleert of de bot is goedgekeurd voor deze server."""

    return interaction.guild.id in approved_servers

@bot.event

async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):

    """
    Foutafhandeling voor slash commands.
    Deze functie is aangepast om specifieke foutmeldingen te sturen op basis van de mislukte controle.
    """

    if interaction.command.name != "info" and interaction.guild and interaction.guild.id not in approved_servers:

        embed = create_footer_embed(

            title="Bot is niet geactiveerd in deze server",

            description=f"Deze bot is nog niet geactiveerd voor de server **{interaction.guild.name}**. Neem contact op met de servereigenaar om de bot-ontwikkelaar te benaderen voor toegang.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    if isinstance(error, discord.app_commands.errors.CheckFailure):

        if interaction.command.name in ["add", "remove", "addmore", "removemore", "show", "servers", "leave",

                                        "toggledmowner", "invite", "dmserverowners", "clearall", "search", "requests",

                                        "approveaccess", "denyaccess", "addserver", "removeserver"]:

            if not is_bot_dev(interaction):

                embed = create_footer_embed(

                    title="Geen toegang",

                    description="Dit commando is alleen beschikbaar voor de bot ontwikkelaar.",

                    color=discord.Color.red()

                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

                return

        if interaction.command.name in ["showinserver"]:

            if not is_bot_dev(interaction) and not is_server_owner(interaction):

                embed = create_footer_embed(

                    title="Geen toegang",

                    description="Dit commando is alleen beschikbaar voor de server eigenaar en de bot ontwikkelaar.",

                    color=discord.Color.red()

                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

                return

        embed = create_footer_embed(

            title="Fout",

            description="Er is een onbekende fout opgetreden bij het controleren van je rechten.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif isinstance(error, discord.app_commands.MissingPermissions):

        embed = create_footer_embed(

            title="Geen Rechten",

            description="Je hebt niet de juiste rechten om dit commando uit te voeren.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif isinstance(error, discord.app_commands.errors.CommandInvokeError):

        if isinstance(error.original, discord.errors.HTTPException):

            embed = create_footer_embed(

                title="Fout",

                description="De lijst is te lang om in één keer weer te geven. Gebruik het /show commando opnieuw om de volgende pagina te zien.",

                color=discord.Color.red()

            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:

            print(f"Er is een onverwachte fout opgetreden: {error}")

            await interaction.response.send_message("Er is een onverwachte fout opgetreden.", ephemeral=True)

    else:

        print(f"Er is een onverwachte fout opgetreden: {error}")

        await interaction.response.send_message("Er is een onverwachte fout opgetreden.", ephemeral=True)

@bot.tree.command(name="approveaccess", description="Keurt een server goed om de bot te gebruiken. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(guild_id="ID van de server die goedgekeurd moet worden.")

async def approve_access(interaction: discord.Interaction, guild_id: str):

    try:

        guild_id_int = int(guild_id)

    except ValueError:

        embed = create_footer_embed(

            title="Fout",

            description="De opgegeven ID is ongeldig. Voer een numerieke ID in.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    guild = bot.get_guild(guild_id_int)

    if not guild:

        embed = create_footer_embed(

            title="Fout",

            description=f"Server met ID `{guild_id_int}` niet gevonden.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    if guild_id_int in approved_servers:

        embed = create_footer_embed(

            title="Fout",

            description="Deze server is al goedgekeurd.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    approved_servers.append(guild_id_int)

    save_approved_servers(approved_servers)

    if guild_id_int in pending_servers:

        pending_servers.remove(guild_id_int)

        save_pending_servers(pending_servers)

    if guild_id_int in pending_dms:

        dm_data = pending_dms[guild_id_int]

        try:

            user_dm_channel = await bot.fetch_channel(dm_data['channel_id'])

            original_dm_message = await user_dm_channel.fetch_message(dm_data['message_id'])

            embed_approved = create_footer_embed(

                title="✅ Toegang Goedgekeurd",

                description=f"Je verzoek om toegang tot **{guild.name}** is succesvol goedgekeurd. Welkom op de server!",

                color=discord.Color.green()

            )

            await original_dm_message.edit(embed=embed_approved, view=None)

            del pending_dms[guild_id_int]

            save_pending_dms(pending_dms)

        except Exception as e:

            print(f"Kon DM bericht niet bewerken voor gilde {guild_id_int}: {e}")

    try:

        await guild.owner.send(

            embed=create_footer_embed(

                title="Toegang Goedgekeurd!",

                description=f"De eigenaar van de bot heeft zojuist toegang goedgekeurd voor de bot in jouw server **{guild.name}**! Vanaf nu kun je alle commando's gebruiken."

            )

        )

    except discord.Forbidden:

        print(f"Kon geen DM sturen naar de eigenaar van server {guild.name} ({guild_id_int})")

    embed = create_footer_embed(

        title="Toegang Goedgekeurd",

        description=f"De bot heeft nu toegang tot de server **{guild.name}** (`{guild_id_int}`)."

    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="denyaccess", description="Weigert toegang en verwijdert de bot uit de server. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(guild_id="ID van de server die geweigerd moet worden.")

async def deny_access(interaction: discord.Interaction, guild_id: str):

    try:

        guild_id_int = int(guild_id)

    except ValueError:

        embed = create_footer_embed(

            title="Fout",

            description="De opgegeven ID is ongeldig. Voer een numerieke ID in.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    guild = bot.get_guild(guild_id_int)

    if not guild:

        embed = create_footer_embed(

            title="Fout",

            description=f"Server met ID `{guild_id_int}` niet gevonden.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    if guild_id_int in approved_servers:

        approved_servers.remove(guild_id_int)

        save_approved_servers(approved_servers)

    if guild_id_int in pending_servers:

        pending_servers.remove(guild_id_int)

        save_pending_servers(pending_servers)

    if guild_id_int in pending_dms:

        dm_data = pending_dms[guild_id_int]

        try:

            user_dm_channel = await bot.fetch_channel(dm_data['channel_id'])

            original_dm_message = await user_dm_channel.fetch_message(dm_data['message_id'])

            embed_denied = create_footer_embed(

                title="❌ Toegang Geweigerd",

                description=f"Helaas is je verzoek om toegang tot **{guild.name}** geweigerd.",

                color=discord.Color.red()

            )

            await original_dm_message.edit(embed=embed_denied, view=None)

            del pending_dms[guild_id_int]

            save_pending_dms(pending_dms)

        except Exception as e:

            print(f"Kon DM bericht niet bewerken voor gilde {guild_id_int}: {e}")

    try:

        await guild.owner.send(

            embed=create_footer_embed(

                title="Toegang Geweigerd",

                description=f"De eigenaar van de bot heeft de toegang voor de bot in jouw server **{guild.name}** geweigerd. Als gevolg hiervan heeft de bot de server automatisch verlaten."

            )

        )

    except discord.Forbidden:

        print(f"Kon geen DM sturen naar de eigenaar van server {guild.name} ({guild_id_int})")

    await guild.leave()

    embed = create_footer_embed(

        title="Toegang Geweigerd",

        description=f"De bot heeft de server **{guild.name}** (`{guild_id_int}`) verlaten."

    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="requests", description="Toont alle servers die wachten op goedkeuring. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

async def requests_command(interaction: discord.Interaction):

    if not pending_servers:

        embed = create_footer_embed(

            title="Wachtende Servers",

            description="Er zijn momenteel geen servers in afwachting van goedkeuring."

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    requests_string = ""

    for guild_id in pending_servers:

        guild = bot.get_guild(guild_id)

        if guild:

            requests_string += f"**{guild.name}** (`{guild.id}`)\n"

        else:

            requests_string += f"Onbekende server (`{guild_id}`)\n"

    embed = create_footer_embed(

        title="Wachtende Servers",

        description=requests_string

    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="history",

                  description="Toont een overzicht van alle uitgevoerde moderatieacties. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

async def history_command(interaction: discord.Interaction):

    if not action_history:

        embed = create_footer_embed(

            title="Actie Geschiedenis",

            description="Er zijn nog geen acties gelogd."

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    history_string = ""

    for entry in reversed(action_history):

        user = await bot.fetch_user(entry['user_id'])

        guild = bot.get_guild(entry['guild_id'])

        user_name = user.name if user else f"Onbekende Gebruiker (ID: {entry['user_id']})"

        guild_name = guild.name if guild else f"Onbekende Server (ID: {entry['guild_id']})"

        timestamp = datetime.datetime.fromisoformat(entry['timestamp'])

        history_string += (

            f"**Gebruiker:** {user_name}\n"

            f"**Server:** {guild_name}\n"

            f"**Actie:** {entry['action']}\n"

            f"**Tijd:** {timestamp.strftime('%d-%m-%Y %H:%M:%S')}\n"

            "--------------------\n"

        )

    embeds = []

    current_string = ""

    for line in history_string.split("--------------------\n"):

        if len(current_string) + len(line) + 20 < 4096:

            current_string += line + "--------------------\n"

        else:

            embeds.append(create_footer_embed(

                title="Actie Geschiedenis",

                description=current_string

            ))

            current_string = line + "--------------------\n"

    if current_string:

        embeds.append(create_footer_embed(

            title="Actie Geschiedenis",

            description=current_string

        ))

    await interaction.response.send_message(embeds=embeds, ephemeral=True)

@bot.tree.command(name="add", description="Voegt een gebruiker toe aan de blacklist. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(user="Vermelding van de gebruiker die je wilt toevoegen.",

                               reason="De reden voor de blacklisting.")

async def add_to_blacklist(interaction: discord.Interaction, user: discord.User, reason: str):

    user_id_to_add = user.id

    existing_user = next((item for item in blacklist['blacklisted_users'] if item['id'] == user_id_to_add), None)

    if not existing_user:

        new_entry = {"id": user_id_to_add, "reason": reason}

        blacklist['blacklisted_users'].append(new_entry)

        save_blacklist(blacklist)

        embed = create_footer_embed(

            title="Gebruiker toegevoegd",

            description=f"Gebruiker met ID `{user_id_to_add}` is succesvol toegevoegd aan de blacklist."

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        if config["notify_on_update"] and interaction.guild.owner and interaction.guild.owner.id != OWNER_ID:

            dm_embed = create_footer_embed(

                title="Blacklist Update",

                description=f"Een gebruiker is toegevoegd aan de blacklist op jouw server, **{interaction.guild.name}**."

            )

            dm_embed.add_field(name="Gebruiker", value=f"<@{user_id_to_add}>", inline=False)

            dm_embed.add_field(name="Reden", value=reason, inline=False)

            await interaction.guild.owner.send(embed=dm_embed)

    else:

        embed = create_footer_embed(

            title="Gebruiker bestaat al",

            description=f"Gebruiker met ID `{user_id_to_add}` staat al op de blacklist.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="remove", description="Verwijdert een gebruiker van de blacklist. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(user="Vermelding van de gebruiker die je wilt verwijderen.")

async def remove_from_blacklist(interaction: discord.Interaction, user: discord.User):

    user_id_to_remove = user.id

    user_to_remove = next((item for item in blacklist['blacklisted_users'] if item['id'] == user_id_to_remove), None)

    if user_to_remove:

        blacklist['blacklisted_users'].remove(user_to_remove)

        save_blacklist(blacklist)

        embed = create_footer_embed(

            title="Gebruiker verwijderd",

            description=f"Gebruiker met ID `{user_id_to_remove}` is succesvol verwijderd van de blacklist."

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        if config["notify_on_update"] and interaction.guild.owner and interaction.guild.owner.id != OWNER_ID:

            dm_embed = create_footer_embed(

                title="Blacklist Update",

                description=f"Een gebruiker is verwijderd van de blacklist op jouw server, **{interaction.guild.name}**."

            )

            dm_embed.add_field(name="Gebruiker", value=f"<@{user_id_to_remove}>", inline=False)

            await interaction.guild.owner.send(embed=dm_embed)

    else:

        embed = create_footer_embed(

            title="Gebruiker niet gevonden",

            description=f"Gebruiker met ID `{user_id_to_remove}` staat niet op de blacklist.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="addmore",

                  description="Voegt meerdere gebruikers tegelijk toe aan de blacklist. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(user_ids_list="Lijst van ID's of vermeldingen, gescheiden door komma's.",

                               reason="De reden voor de blacklisting.")

async def add_multiple_to_blacklist(interaction: discord.Interaction, user_ids_list: str, reason: str):

    user_ids = [uid.strip() for uid in user_ids_list.split(',')]

    added_users = []

    already_on_list = []

    for user_input in user_ids:

        user_id_to_add = None

        if user_input.startswith('<@') and user_input.endswith('>'):

            try:

                user_id_to_add = int(user_input.strip('<@!>'))

            except ValueError:

                continue

        else:

            try:

                user_id_to_add = int(user_input)

            except ValueError:

                continue

        if user_id_to_add:

            existing_user = next((item for item in blacklist['blacklisted_users'] if item['id'] == user_id_to_add),

                                 None)

            if not existing_user:

                new_entry = {"id": user_id_to_add, "reason": reason}

                blacklist['blacklisted_users'].append(new_entry)

                added_users.append(user_id_to_add)

            else:

                already_on_list.append(user_id_to_add)

    save_blacklist(blacklist)

    description = ""

    if added_users:

        mentions = [f"<@{uid}>" for uid in added_users]

        description += f"De volgende gebruikers zijn succesvol toegevoegd aan de blacklist:\n> {', '.join(mentions)}\n\n"

    if already_on_list:

        mentions = [f"<@{uid}>" for uid in already_on_list]

        description += f"De volgende gebruikers stonden al op de blacklist:\n> {', '.join(mentions)}\n\n"

    if not added_users and not already_on_list:

        description = "Geen geldige gebruikers-ID's of vermeldingen gevonden in de lijst."

    embed = create_footer_embed(

        title="Blacklist Bulk Update",

        description=description

    )

    if added_users:

        embed.add_field(name="Reden", value=reason, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="removemore",

                  description="Verwijdert meerdere gebruikers tegelijk van de blacklist. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(user_ids_list="Lijst van ID's of vermeldingen, gescheiden door komma's.")

async def remove_multiple_from_blacklist(interaction: discord.Interaction, user_ids_list: str):

    user_ids = [uid.strip() for uid in user_ids_list.split(',')]

    removed_users = []

    not_found_users = []

    for user_input in user_ids:

        user_id_to_remove = None

        if user_input.startswith('<@') and user_input.endswith('>'):

            try:

                user_id_to_remove = int(user_input.strip('<@!>'))

            except ValueError:

                continue

        else:

            try:

                user_id_to_remove = int(user_input)

            except ValueError:

                continue

        if user_id_to_remove:

            user_to_remove = next((item for item in blacklist['blacklisted_users'] if item['id'] == user_id_to_remove),

                                  None)

            if user_to_remove:

                blacklist['blacklisted_users'].remove(user_to_remove)

                removed_users.append(user_id_to_remove)

            else:

                not_found_users.append(user_id_to_remove)

    save_blacklist(blacklist)

    description = ""

    if removed_users:

        mentions = [f"<@{uid}>" for uid in removed_users]

        description += f"De volgende gebruikers zijn succesvol verwijderd van de blacklist:\n> {', '.join(mentions)}\n\n"

    if not_found_users:

        mentions = [f"<@{uid}>" for uid in not_found_users]

        description += f"De volgende gebruikers stonden al op de blacklist:\n> {', '.join(mentions)}\n\n"

    if not removed_users and not not_found_users:

        description = "Geen geldige gebruikers-ID's of vermeldingen gevonden in de lijst."

    embed = create_footer_embed(

        title="Blacklist Bulk Verwijdering",

        description=description

    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="addserver", description="Voegt een server toe aan de blacklist. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(guild_id="ID van de server die je wilt toevoegen.",

                               reason="De reden voor de blacklisting.")

async def add_server_to_blacklist(interaction: discord.Interaction, guild_id: str, reason: str):

    try:

        guild_id_int = int(guild_id)

    except ValueError:

        embed = create_footer_embed(

            title="Fout",

            description="Het opgegeven ID is ongeldig. Voer een numerieke ID in.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    existing_server = next((item for item in blacklist['blacklisted_servers'] if item['id'] == guild_id_int), None)

    if existing_server:

        embed = create_footer_embed(

            title="Server bestaat al",

            description=f"Server met ID `{guild_id_int}` staat al op de blacklist.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    else:

        new_entry = {"id": guild_id_int, "reason": reason}

        blacklist["blacklisted_servers"].append(new_entry)

        save_blacklist(blacklist)

        embed = create_footer_embed(

            title="Server toegevoegd",

            description=f"Server met ID `{guild_id_int}` is succesvol toegevoegd aan de blacklist."

        )

        embed.add_field(name="Reden", value=reason, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="removeserver", description="Verwijdert een server van de blacklist. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(guild_id="ID van de server die je wilt verwijderen.")

async def remove_server_from_blacklist(interaction: discord.Interaction, guild_id: str):

    try:

        guild_id_int = int(guild_id)

    except ValueError:

        embed = create_footer_embed(

            title="Fout",

            description="Het opgegeven ID is ongeldig. Voer een numerieke ID in.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    server_to_remove = next((item for item in blacklist['blacklisted_servers'] if item['id'] == guild_id_int), None)

    if not server_to_remove:

        embed = create_footer_embed(

            title="Server niet gevonden",

            description=f"Server met ID `{guild_id_int}` staat niet op de blacklist.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    else:

        blacklist["blacklisted_servers"].remove(server_to_remove)

        save_blacklist(blacklist)

        embed = create_footer_embed(

            title="Server verwijderd",

            description=f"Server met ID `{guild_id_int}` is succesvol verwijderd van de blacklist."

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="servers", description="Toont alle goedgekeurde en wachtende servers. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

async def show_all_servers_command(interaction: discord.Interaction):

    approved_servers_list = []

    if approved_servers:

        for guild_id in approved_servers:

            guild = bot.get_guild(guild_id)

            if guild:

                approved_servers_list.append(f"**{guild.name}** (`{guild.id}`)")

            else:

                approved_servers_list.append(f"**Onbekende server** (`{guild_id}`)")

    pending_servers_list = []

    if pending_servers:

        for guild_id in pending_servers:

            guild = bot.get_guild(guild_id)

            if guild:

                pending_servers_list.append(f"**{guild.name}** (`{guild.id}`)")

            else:

                pending_servers_list.append(f"**Onbekende server** (`{guild_id}`)")

    description = ""

    if approved_servers_list:

        description += "**Goedgekeurde Servers:**\n" + "\n".join(approved_servers_list) + "\n\n"

    else:

        description += "**Goedgekeurde Servers:**\nGeen\n\n"

    if pending_servers_list:

        description += "**Wachtende Servers:**\n" + "\n".join(pending_servers_list)

    else:

        description += "**Wachtende Servers:**\nGeen"

    embed = create_footer_embed(

        title="Bot Serverstatus",

        description=description

    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="show", description="Toont alle geblackliste gebruikers en servers. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

async def show_blacklisted_items(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    try:

        user_list = sorted(blacklist["blacklisted_users"], key=lambda x: x['id'])

        users_embeds = []

        current_description = ""

        chunk_count = 1

        if not user_list:

            users_embeds.append(create_footer_embed(

                title="Geblackliste gebruikers",

                description="Er staan momenteel geen gebruikers op de blacklist.",

                color=discord.Color.red()

            ))

        else:

            for user_entry in user_list:

                user_id = user_entry['id']

                reason = user_entry.get('reason', 'Geen reden opgegeven.')

                user_string = f"**Gebruiker:** <@{user_id}> (`{user_id}`)\n> **Reden:** {reason}\n\n"

                if len(current_description) + len(user_string) > 3900:

                    users_embeds.append(create_footer_embed(

                        title=f"Geblackliste gebruikers (Deel {chunk_count})",

                        description=current_description,

                        color=discord.Color.red()

                    ))

                    current_description = ""

                    chunk_count += 1

                current_description += user_string

            if current_description:

                users_embeds.append(create_footer_embed(

                    title=f"Geblackliste gebruikers (Deel {chunk_count})",

                    description=current_description,

                    color=discord.Color.red()

                ))

        server_list = sorted(blacklist["blacklisted_servers"], key=lambda x: x['id'])

        servers_embeds = []

        current_description = ""

        chunk_count = 1

        if not server_list:

            servers_embeds.append(create_footer_embed(

                title="Geblackliste servers",

                description="Er staan momenteel geen servers op de blacklist.",

                color=discord.Color.dark_red()

            ))

        else:

            for server_entry in server_list:

                server_id = server_entry['id']

                reason = server_entry.get('reason', 'Geen reden opgegeven.')

                guild = bot.get_guild(server_id)

                server_name = guild.name if guild else "Onbekende Server"

                server_string = f"**Server:** {server_name} (`{server_id}`)\n> **Reden:** {reason}\n\n"

                if len(current_description) + len(server_string) > 3900:

                    servers_embeds.append(create_footer_embed(

                        title=f"Geblackliste servers (Deel {chunk_count})",

                        description=current_description,

                        color=discord.Color.dark_red()

                    ))

                    current_description = ""

                    chunk_count += 1

                current_description += server_string

            if current_description:

                servers_embeds.append(create_footer_embed(

                    title=f"Geblackliste servers (Deel {chunk_count})",

                    description=current_description,

                    color=discord.Color.dark_red()

                ))

        await interaction.followup.send(embeds=users_embeds + servers_embeds)

    except Exception as e:

        print(f"Fout bij het uitvoeren van /show commando: {e}")

        error_embed = create_footer_embed(

            title="Fout",

            description="Er is een onverwachte fout opgetreden bij het weergeven van de blacklist. Probeer het later opnieuw.",

            color=discord.Color.red()

        )

        await interaction.followup.send(embed=error_embed, ephemeral=True)

@bot.tree.command(name="leave", description="Laat de bot een specifieke server verlaten. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(guild_id="ID van de server die de bot moet verlaten.")

async def leave_server(interaction: discord.Interaction, guild_id: str):

    try:

        guild_id_int = int(guild_id)

    except ValueError:

        embed = create_footer_embed(

            title="Fout",

            description="De opgegeven ID is ongeldig. Voer een numerieke ID in.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    guild = bot.get_guild(guild_id_int)

    if guild:

        await guild.leave()

        embed = create_footer_embed(

            title="Server verlaten",

            description=f"De bot heeft server `{guild.name}` verlaten."

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    else:

        embed = create_footer_embed(

            title="Fout",

            description=f"Server met ID `{guild_id_int}` niet gevonden.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="toggledmowner",

                  description="Schakelt DM-notificaties voor servereigenaren in/uit bij aanpassingen. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

async def toggle_dm_to_owner(interaction: discord.Interaction):

    config["notify_on_update"] = not config["notify_on_update"]

    save_config(config)

    status = "ingeschakeld" if config["notify_on_update"] else "uitgeschakeld"

    embed = create_footer_embed(

        title="Notificaties bijgewerkt",

        description=f"DM-notificaties voor servereigenaren bij aanpassingen zijn nu **{status}**."

    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="invite", description="Genereert een invite link met administrator rechten. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

async def invite_command(interaction: discord.Interaction):

    """
    Genereert een invite link voor de bot met administrator permissies.
    Dit commando is alleen beschikbaar voor de botontwikkelaar.
    """

    permissions = discord.Permissions(administrator=True)

    invite_url = discord.utils.oauth_url(

        bot.user.id,

        permissions=permissions

    )

    embed = create_footer_embed(

        title="Bot Invite Link",

        description=f"Klik op de onderstaande link om de bot uit te nodigen voor een server:\n\n[Klik hier om de bot uit te nodigen]({invite_url})"

    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="dmserverowners",

                  description="Stuurt een bericht naar alle servereigenaren waar de bot in zit. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(message="Het bericht dat je wilt versturen.")

async def dm_server_owners(interaction: discord.Interaction, message: str):

    """
    Verstuurt een privébericht naar de eigenaar van elke server waar de bot in zit.
    Alleen de botontwikkelaar kan dit commando uitvoeren.
    """

    await interaction.response.send_message("Bezig met het versturen van updates naar servereigenaren...",

                                            ephemeral=True)

    success_count = 0

    fail_guilds = []

    embed_to_send = create_footer_embed(

        title="Belangrijke Bot Update",

        description=message

    )

    for guild in bot.guilds:

        owner = guild.owner

        if owner and owner.id != OWNER_ID:

            try:

                await owner.send(embed=embed_to_send)

                success_count += 1

            except discord.Forbidden:

                fail_guilds.append(guild.name)

            await asyncio.sleep(1)

    summary_description = f"Updates succesvol verstuurd naar **{success_count}** servereigenaren."

    if fail_guilds:

        summary_description += f"\n\nKon geen bericht sturen naar de eigenaar van de volgende servers:\n> " + "\n> ".join(

            fail_guilds)

    summary_embed = create_footer_embed(

        title="Update Verstuurd",

        description=summary_description,

        color=discord.Color.red() if fail_guilds else discord.Color.blue()

    )

    await interaction.followup.send(embed=summary_embed, ephemeral=True)

@bot.tree.command(name="clearall", description="Verwijdert alle slash commands wereldwijd. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

async def clear_global_commands(interaction: discord.Interaction):

    """
    Verwijdert alle wereldwijde slash commands. Let op: dit kan even duren.
    """

    await interaction.response.send_message("Bezig met het wissen van alle slash commands...", ephemeral=True)

    bot.tree.clear_commands(guild=None)

    await bot.tree.sync()

    await interaction.followup.send(

        "Alle wereldwijde slash commands zijn succesvol gewist. Het kan tot een uur duren voordat de wijzigingen overal zichtbaar zijn.",

        ephemeral=True)

@bot.tree.command(name="search", description="Controleert of een gebruiker op de blacklist staat. (ALLEEN BOT DEV)")

@discord.app_commands.check(is_bot_dev)

@discord.app_commands.describe(user_id="ID van de gebruiker die je wilt zoeken.")

async def search_command(interaction: discord.Interaction, user_id: str):

    try:

        user_id_int = int(user_id)

    except ValueError:

        embed = create_footer_embed(

            title="Fout",

            description="Het opgegeven ID is ongeldig. Voer een numerieke ID in.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    user_data = next((item for item in blacklist['blacklisted_users'] if item['id'] == user_id_int), None)

    if user_data:

        reason = user_data.get('reason', 'Geen reden opgegeven.')

        embed = create_footer_embed(

            title="Gebruiker Gevonden",

            description=f"Gebruiker met ID `{user_id_int}` staat op de blacklist.",

            color=discord.Color.red()

        )

        embed.add_field(name="Reden", value=reason, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    else:

        embed = create_footer_embed(

            title="Gebruiker Niet Gevonden",

            description=f"Gebruiker met ID `{user_id_int}` staat NIET op de blacklist.",

            color=discord.Color.green()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="info", description="Laat algemene informatie over de bot zien.")

async def slash_info(interaction: discord.Interaction):

    is_approved = interaction.guild and interaction.guild.id in approved_servers

    if not is_approved and interaction.guild:

        embed = create_footer_embed(

            title="Bot is niet geactiveerd in deze server",

            description=f"Deze bot is nog niet geactiveerd voor de server **{interaction.guild.name}**. Neem contact op met de servereigenaar om de bot-ontwikkelaar te benaderen voor toegang.",

            color=discord.Color.red()

        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        return

    owner = await bot.fetch_user(OWNER_ID)

    owner_name = owner.name if owner else "Onbekende ontwikkelaar"

    embed = create_footer_embed(

        title="Over de Blacklist Bot",

        description=f"Hallo! Ik ben een geautomatiseerde bot, ontwikkeld door **{owner_name}** (<@{OWNER_ID}>), om servers te helpen beschermen tegen ongewenste gebruikers."

    )

    embed.add_field(name="Status", value="Ik ben **online** en luister naar jouw commando's.", inline=False)

    embed.add_field(name="Leuk Weetje",

                    value="Wist je dat ik de beveiliging van meerdere servers tegelijkertijd kan bewaken? Ik ben als een waakhond, maar dan digitaal!",

                    inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="showinserver",

                  description="Toont alle geblackliste leden in de huidige server. (ALLEEN SERVER EIGENAAR EN BOT DEV)")

@discord.app_commands.check(is_access_approved)

@discord.app_commands.check(lambda i: is_bot_dev(i) or is_server_owner(i))

async def show_in_server(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    try:

        guild = interaction.guild

        blacklisted_members_data = []

        for member in guild.members:

            user_entry = next((item for item in blacklist['blacklisted_users'] if item['id'] == member.id), None)

            if user_entry:

                reason = user_entry.get('reason', 'Geen reden opgegeven.')

                blacklisted_members_data.append({"name": member.name, "id": member.id, "reason": reason})

        if not blacklisted_members_data:

            embed = create_footer_embed(

                title="Geen geblackliste leden gevonden",

                description=f"Er zijn momenteel geen geblackliste leden in de server **{guild.name}**."

            )

            await interaction.followup.send(embed=embed)

            return

        max_embed_description_length = 3900

        embeds = []

        current_description = ""

        chunk_count = 1

        for member_data in sorted(blacklisted_members_data, key=lambda x: x['name']):

            member_string = f"**Gebruiker:** <@{member_data['id']}> (`{member_data['id']}`)\n> **Reden:** {member_data['reason']}\n\n"

            if len(current_description) + len(member_string) > max_embed_description_length:

                embeds.append(create_footer_embed(

                    title=f"Geblackliste leden in **{guild.name}** (Deel {chunk_count})",

                    description=current_description,

                    color=discord.Color.red()

                ))

                current_description = ""

                chunk_count += 1

            current_description += member_string

        if current_description:

            embeds.append(create_footer_embed(

                title=f"Geblackliste leden in **{guild.name}** (Deel {chunk_count})",

                description=current_description,

                color=discord.Color.red()

            ))

        await interaction.followup.send(embeds=embeds)

    except Exception as e:

        print(f"Fout bij het uitvoeren van /showinserver commando: {e}")

        error_embed = create_footer_embed(

            title="Fout",

            description="Er is een onverwachte fout opgetreden bij het weergeven van geblackliste leden in deze server. Probeer het later opnieuw.",

            color=discord.Color.red()

        )

        await interaction.followup.send(embed=error_embed, ephemeral=True)

@bot.event

async def on_ready():

    """Wordt geactiveerd wanneer de bot succesvol verbonden is."""

    print(f"Bot is online! Ingelogd als {bot.user}")

    print("Slash commands synchroniseren...")

    try:

        synced = await bot.tree.sync()

        print(f"Commando's succesvol gesynchroniseerd! ({len(synced)} commando's)")

        await restore_pending_dms()

    except Exception as e:

        print(f"Kon slash commands niet synchroniseren: {e}")

    status_map = {

        "online": discord.Status.online,

        "dnd": discord.Status.dnd,

        "idle": discord.Status.idle,

        "invisible": discord.Status.invisible

    }

    status_type = status_map.get(BOT_STATUS_TYPE, discord.Status.online)

    guild_count = len(bot.guilds)

    member_count = sum(guild.member_count for guild in bot.guilds)

    formatted_activity_message = BOT_ACTIVITY_MESSAGE.replace('{guildcount}', str(guild_count)).replace('{membercount}',

                                                                                                        str(member_count))

    activity_type = BOT_ACTIVITY_TYPE.lower()

    activity_message = formatted_activity_message

    if activity_type == "playing":

        activity = discord.Game(name=activity_message)

    elif activity_type == "watching":

        activity = discord.Activity(type=discord.ActivityType.watching, name=activity_message)

    elif activity_type == "listening":

        activity = discord.Activity(type=discord.ActivityType.listening, name=activity_message)

    elif activity_type == "streaming":

        activity = discord.Streaming(name=activity_message, url="https://www.twitch.tv")

    else:

        activity = None

    await bot.change_presence(status=status_type, activity=activity)

    print(

        f"Status ingesteld op: {status_type.name.capitalize()} | Activiteit: {activity_type.capitalize()} {activity_message}")

async def restore_pending_dms():

    """Herstelt de DM berichten na een herstart van de bot."""

    dms_to_remove = []

    for guild_id, dm_data in pending_dms.items():

        try:

            guild = bot.get_guild(guild_id)

            if not guild:

                dms_to_remove.append(guild_id)

                continue

            dm_channel = await bot.fetch_channel(dm_data['channel_id'])

            original_dm_message = await dm_channel.fetch_message(dm_data['message_id'])

            await original_dm_message.edit(view=AccessButtons(guild.owner, original_dm_message))

        except discord.NotFound:

            dms_to_remove.append(guild_id)

        except Exception as e:

            print(f"Kon DM bericht niet herstellen voor gilde {guild_id}: {e}")

            dms_to_remove.append(guild_id)

    for guild_id in dms_to_remove:

        if guild_id in pending_dms:

            del pending_dms[guild_id]

    save_pending_dms(pending_dms)

@bot.event

async def on_guild_join(guild):

    """Wordt geactiveerd wanneer de bot wordt toegevoegd aan een nieuwe server."""

    if guild.owner.id == OWNER_ID:

        if guild.id not in approved_servers:

            approved_servers.append(guild.id)

            save_approved_servers(approved_servers)

        owner = await bot.fetch_user(OWNER_ID)

        if owner:

            await owner.send(

                embed=create_footer_embed(

                    title="Bot toegevoegd aan nieuwe server",

                    description=f"Je hebt de bot zojuist toegevoegd aan de server **{guild.name}** (`{guild.id}`). Deze is automatisch goedgekeurd."

                )

            )

    else:

        if guild.id not in pending_servers:

            pending_servers.append(guild.id)

            save_pending_servers(pending_servers)

        owner = await bot.fetch_user(OWNER_ID)

        if owner:

            dm_message = await owner.send(

                embed=create_footer_embed(

                    title="Verzoek om Toegang",

                    description=f"De bot is zojuist toegevoegd aan de server **{guild.name}** (`{guild.id}`). De bot is inactief totdat je toegang goedkeurt."

                )

            )

            await owner.send(

                f"Gebruik `/approveaccess {guild.id}` om de bot te activeren, of `/denyaccess {guild.id}` om de bot de server te laten verlaten."

            )

@bot.event

async def on_member_join(member):

    """Wordt geactiveerd wanneer een nieuw lid zich bij een server voegt."""

    user_id = member.id

    guild_id = member.guild.id

    guild_owner = member.guild.owner

    main_owner = bot.get_user(OWNER_ID)

    is_user_blacklisted = any(user_entry['id'] == user_id for user_entry in blacklist["blacklisted_users"])

    is_server_blacklisted = any(server_entry['id'] == guild_id for server_entry in blacklist["blacklisted_servers"])

    if is_user_blacklisted and is_server_blacklisted:

        user_reason = next((item['reason'] for item in blacklist['blacklisted_users'] if item['id'] == user_id),

                           "Geen reden opgegeven.")

        server_reason = next((item['reason'] for item in blacklist['blacklisted_servers'] if item['id'] == guild_id),

                             "Geen reden opgegeven.")

        embed = create_footer_embed(

            title="Dubbele Blacklist Waarschuwing!",

            description=f"Een **geblackliste gebruiker** heeft een **geblackliste server** gejoined. Dit kan duiden op een ernstig probleem.",

            color=discord.Color.red()

        )

        embed.add_field(name="Gebruiker", value=f"{member.name} (`{user_id}`)", inline=False)

        embed.add_field(name="Server", value=f"{member.guild.name} (`{guild_id}`)", inline=False)

        embed.add_field(name="Reden voor Gebruiker Blacklist", value=user_reason, inline=False)

        embed.add_field(name="Reden voor Server Blacklist", value=server_reason, inline=False)

        if main_owner:

            await main_owner.send(embed=embed)

        if guild_owner and guild_owner.id != OWNER_ID:

            try:

                await guild_owner.send(embed=embed)

            except discord.Forbidden:

                print(f"Kon geen DM sturen naar de eigenaar van server {member.guild.name}")

    elif is_user_blacklisted and guild_id in approved_servers:

        reason = next((item['reason'] for item in blacklist['blacklisted_users'] if item['id'] == user_id),

                      "Geen reden opgegeven.")

        embed = create_footer_embed(

            title="Blacklist Waarschuwing!",

            description=f"Een geblackliste gebruiker heeft **{member.guild.name}** gejoined.",

            color=discord.Color.red()

        )

        embed.add_field(name="Gebruiker", value=f"{member.name} (`{user_id}`)", inline=False)

        embed.add_field(name="Server", value=f"{member.guild.name} (`{guild_id}`)", inline=False)

        embed.add_field(name="Mention", value=f"<@{user_id}>", inline=False)

        embed.add_field(name="Reden voor Blacklist", value=reason, inline=False)

        view = ModerationView(member, member.guild)

        if main_owner:

            await main_owner.send(embed=embed, view=view)

        if guild_owner and guild_owner.id != OWNER_ID:

            try:

                await guild_owner.send(embed=embed, view=view)

            except discord.Forbidden:

                print(f"Kon geen DM sturen naar de eigenaar van server {member.guild.name}")

    elif not is_user_blacklisted and guild_id in approved_servers:

        blacklisted_servers_found = []

        for bot_guild in bot.guilds:

            if bot_guild.id == guild_id:

                continue

            if any(s['id'] == bot_guild.id for s in blacklist['blacklisted_servers']) and bot_guild.get_member(user_id):

                blacklisted_servers_found.append(bot_guild)

        if blacklisted_servers_found:

            found_server_names = ", ".join([s.name for s in blacklisted_servers_found])

            embed = create_footer_embed(

                title="Waarschuwing: Lid van Geblackliste Server Gedetecteerd!",

                description=f"Een gebruiker die **niet op de blacklist staat** heeft **{member.guild.name}** gejoined, maar is wel lid van de volgende geblackliste servers:",

                color=discord.Color.orange()

            )

            embed.add_field(name="Gebruiker", value=f"{member.name} (`{user_id}`)", inline=False)

            embed.add_field(name="Gedetecteerde geblackliste servers", value=found_server_names, inline=False)

            if main_owner:

                await main_owner.send(embed=embed)

            if guild_owner and guild_owner.id != OWNER_ID:

                try:

                    await guild_owner.send(embed=embed)

                except discord.Forbidden:

                    print(f"Kon geen DM sturen naar de eigenaar van server {member.guild.name}")

bot.run(BOT_TOKEN)
