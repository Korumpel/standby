import discord
import os
import easyocr
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image
import requests
from io import BytesIO

# Lade die .env Datei
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents aktivieren
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Bot erstellen
bot = commands.Bot(command_prefix="!", intents=intents)

# Konfiguration
LOG_CHANNEL_ID = 1145448901743222824  # Ersetze mit deiner Log-Channel-ID
ABMELDUNG_CHANNEL_ID = 1313856040600604682  # Ersetze mit deiner Abmeldung-Channel-ID
REQUIRED_ROLE = "Mitglied"  # Ersetze mit der Rolle, die den Befehl nutzen darf
BEWERBUNGEN_CHANNEL_ID = 1145443562167746630  # Ersetze mit der ID des Bewerbungs-Channels
BEWERBUNGEN_LOG_CHANNEL_ID = 1336053499439353917  # Ersetze mit der ID des Channels, wo die Nachricht kopiert wird
SOURCE_CHANNEL_ID = 123456789012345678  # Ersetze mit der ID des Channels, in dem Bilder analysiert werden
TARGET_CHANNEL_ID = 987654321098765432  # Ersetze mit der ID des Channels, in dem Ergebnisse gepostet werden

# EasyOCR-Reader initialisieren
reader = easyocr.Reader(['en'], gpu=False)

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
@bot.command(name="abmeldung", help="Trage eine Abmeldung ein.")
@commands.has_role(REQUIRED_ROLE)
async def abmeldung(ctx):
    await ctx.send("Bitte fülle das folgende Formular aus:")
    await ctx.send_modal(AbmeldungModal())

# Bewerbungsnachricht kopieren und Emojis hinzufügen
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignoriere Bot-Nachrichten

    # Bewerbungsnachricht kopieren und Emojis hinzufügen
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

    # OCR-Funktion nur in SOURCE_CHANNEL_ID aktivieren
    if message.channel.id == SOURCE_CHANNEL_ID and message.attachments:
        mentioned_users = message.mentions  # Prüfe, ob jemand verlinkt wurde
        if not mentioned_users:
            return  # Falls niemand verlinkt wurde, OCR nicht ausführen

        target_user = mentioned_users[0]  # Der erste erwähnte Nutzer

        for attachment in message.attachments:
            if attachment.filename.lower().endswith(("png", "jpg", "jpeg")):
                response = requests.get(attachment.url)
                img = Image.open(BytesIO(response.content))

                # OCR-Analyse durchführen
                extracted_text = reader.readtext(img, detail=0)
                items = "\n".join(extracted_text)

                if not items:
                    return  # Falls keine Items erkannt wurden, abbrechen

                # Nachricht im Ziel-Channel senden
                target_channel = bot.get_channel(TARGET_CHANNEL_ID)
                if target_channel:
                    await target_channel.send(f"**{target_user.mention} hat folgende Items erhalten:**\n{items}")

    await bot.process_commands(message)

# Bot starten
bot.run(TOKEN)
