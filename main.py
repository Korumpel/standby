import discord
import os
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

# Lade die .env Datei
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents aktivieren
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Bot erstellen
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Slash-Command Handler

# Konfiguration
LOG_CHANNEL_ID = 1145448901743222824  # Ersetze mit deiner Log-Channel-ID
ABMELDUNG_CHANNEL_ID = 1313856040600604682  # Ersetze mit deiner Abmeldung-Channel-ID
REQUIRED_ROLE = "Mitglied"  # Ersetze mit der Rolle, die den Befehl nutzen darf
BEWERBUNGEN_CHANNEL_ID = 1145443562167746630  # Ersetze mit der ID des Bewerbungs-Channels
BEWERBUNGEN_LOG_CHANNEL_ID = 1336053499439353917  # Ersetze mit der ID des Channels, wo die Nachricht kopiert wird


# Event: Ein User joint dem Server
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"👋 {member.mention} ist dem Server beigetreten!")


# Event: Ein User verlässt den Server
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"❌ {member.mention} hat den Server verlassen.")


# Event: Ein User wird gebannt
@bot.event
async def on_member_ban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"⛔ {user.mention} wurde vom Server gebannt!")


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
    # Prüfen, ob der Nutzer die erforderliche Rolle hat
    has_permission = any(role.name == REQUIRED_ROLE
                         for role in interaction.user.roles)
    if not has_permission:
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.",
            ephemeral=True)
        return

    await interaction.response.send_modal(AbmeldungModal())


# Bewerbungsnachricht kopieren und Emojis hinzufügen
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignoriere Bot-Nachrichten

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
            await log_message.add_reaction("👍")  # Daumen hoch Emoji
            await log_message.add_reaction("👎")  # Daumen runter Emoji

    await bot.process_commands(message)


# Slash-Commands synchronisieren
@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"✅ {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren: {e}")
    print(f"✅ Bot {bot.user} ist online!")


# Keep Alive starten (verhindert, dass Replit den Bot stoppt)
keep_alive()

# Bot starten
bot.run(TOKEN)
