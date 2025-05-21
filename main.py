import discord
import os
import asyncio
import re
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Lade die .env Datei
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents aktivieren
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.dm_messages = True
intents.guilds = True

# Bot erstellen
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Slash-Command Handler

# Konfiguration
LOG_CHANNEL_ID = 1145448901743222824
ABMELDUNG_CHANNEL_ID = 1313856040600604682
REQUIRED_ROLE = "Mitglied"
BEWERBUNGEN_CHANNEL_ID = 1145443562167746630
BEWERBUNGEN_LOG_CHANNEL_ID = 1336053499439353917
TIMER_RESULT_CHANNEL_ID = 1303765669489152032  # Ersetze mit Ziel-Channel-ID

# Event: Ein User joint dem Server
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"👋 {member.mention} ({member.name}) ist dem Server beigetreten!")

# Event: Ein User verlässt den Server
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"❌ {member.mention} ({member.name}) hat den Server verlassen.")

# Event: Ein User wird gebannt
@bot.event
async def on_member_ban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"⛔ {user.mention} ({user.name}) wurde vom Server gebannt!")

# Slash-Command: /ping
@tree.command(name="ping", description="Testet, ob der Bot online ist.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! Latenz: {round(bot.latency * 1000)}ms", ephemeral=True)

# Modal für /abmeldung erstellen
class AbmeldungModal(discord.ui.Modal, title="Abmeldung eintragen"):
    zeitraum = discord.ui.TextInput(
        label="Zeitraum", placeholder="z. B. 30.04.2025 bis 18.05.2025")
    grund = discord.ui.TextInput(label="Grund",
                                 placeholder="Warum meldest du dich ab?",
                                 style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        abmeldung_channel = interaction.guild.get_channel(ABMELDUNG_CHANNEL_ID)
        if abmeldung_channel:
            embed = discord.Embed(title="📌 Abmeldung",
                                  color=discord.Color.red())
            embed.add_field(name="👤 Nutzer",
                            value=interaction.user.mention,
                            inline=False)
            embed.add_field(name="📅 Zeitraum",
                            value=self.zeitraum.value,
                            inline=False)
            embed.add_field(name="📝 Grund",
                            value=self.grund.value,
                            inline=False)
            embed.set_footer(text=f"Abmeldung von {interaction.user}")
            await abmeldung_channel.send(embed=embed)
            await interaction.response.send_message(
                "✅ Deine Abmeldung wurde eingetragen!", ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Fehler: Der Abmeldungs-Channel wurde nicht gefunden.",
                ephemeral=True)

# Slash-Command: /abmeldung
@tree.command(name="abmeldung", description="Trage eine Abmeldung ein.")
async def abmeldung(interaction: discord.Interaction):
    has_permission = any(role.name == REQUIRED_ROLE for role in interaction.user.roles)
    if not has_permission:
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.", ephemeral=True)
        return
    await interaction.response.send_modal(AbmeldungModal())

# Bewerbungsnachricht kopieren und Emojis hinzufügen
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == BEWERBUNGEN_CHANNEL_ID:
        log_channel = bot.get_channel(BEWERBUNGEN_LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="📩 Neue Bewerbung",
                                  color=discord.Color.blue())
            embed.add_field(name="👤 Bewerber",
                            value=message.author.mention,
                            inline=False)
            embed.add_field(name="📝 Nachricht",
                            value=message.content,
                            inline=False)
            embed.set_footer(text=f"Bewerbung von {message.author}")
            log_message = await log_channel.send(embed=embed)
            await log_message.add_reaction("👍")
            await log_message.add_reaction("👎")

    if message.content.startswith("/"):
        return

    await bot.process_commands(message)

# Timer-Funktion
def parse_time_input(input_str):
    pattern = r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
    match = re.match(pattern, input_str.strip().lower())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

class TimerModal(discord.ui.Modal, title="Timer einstellen"):
    time_input = discord.ui.TextInput(label="Zeit (z. B. 5m, 30s)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        seconds = parse_time_input(self.time_input.value)
        if not seconds or seconds <= 0:
            await interaction.response.send_message("Ungültige Zeitangabe.", ephemeral=True)
            return

        await interaction.response.send_message("Sende mir nun bitte ein Bild in dieser Unterhaltung.", ephemeral=True)

        def image_check(msg):
            return msg.author == interaction.user and msg.attachments and msg.guild is None

        try:
            msg = await bot.wait_for("message", timeout=120, check=image_check)
            image = msg.attachments[0]

            await interaction.followup.send(f"✅ Timer mit Bild gesetzt. Ich erinnere dich in {self.time_input.value}.", ephemeral=True)

            await asyncio.sleep(seconds)

            target_channel = bot.get_channel(TIMER_RESULT_CHANNEL_ID)
            if target_channel:
                await target_channel.send(
                    content=f"⏰ {interaction.user.mention}, dein Timer ist abgelaufen!",
                    file=await image.to_file()
                )
        except asyncio.TimeoutError:
            await interaction.followup.send("⛔ Zeit zum Hochladen des Bildes ist abgelaufen.", ephemeral=True)

class TimerView(discord.ui.View):
    @discord.ui.button(label="Timer starten", style=discord.ButtonStyle.blurple)
    async def start_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.user.send("Bitte gib deine Zeit ein:")
            await interaction.response.send_message("📩 Ich habe dir eine DM geschickt!", ephemeral=True)
            await interaction.user.send_modal(TimerModal())
        except discord.Forbidden:
            await interaction.response.send_message("❌ Ich kann dir keine DM senden. Bitte aktiviere DMs.", ephemeral=True)

@tree.command(name="timer", description="Erstelle einen Timer mit Bild-Erinnerung.")
async def timer(interaction: discord.Interaction):
    await interaction.response.send_message("Klicke auf den Button, um einen Timer mit Bild zu erstellen:", view=TimerView(), ephemeral=True)

# Slash-Commands synchronisieren
@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"✅ {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren: {e}")
    print(f"✅ Bot {bot.user} ist online!")

# Bot starten
bot.run(TOKEN)
