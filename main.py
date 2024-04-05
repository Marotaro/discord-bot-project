import discord
from servermc import *
from db.db import *
import sqlite3
import asyncio

from discord.ext import commands

intents = discord.Intents.default()


intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents, description = "Minecraft Bot")

@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")

@bot.event
async def on_message(message):
    if message.author != bot.user and message.content.lower() == "ping":
        await message.channel.send("pong")
    if message.content == "minecraft":
        await message.channel.send(getstatus())
        await message.channel.send(getplayers())
        com(f"say lol {getstatus()}")
    if message.content == "add":
        db = get_db()
        db.execute("INSERT INTO Players (discord_id, uuid) VALUES (?,?)", (message.author.id, 'test'))
        db.commit()
    await bot.process_commands(message)

@bot.command()
async def addme(ctx, pseudo: str ):    
    db = get_db()
    try:
        already_register = db.execute("SELECT CASE WHEN EXISTS (SELECT * FROM Players WHERE discord_id = ? ) THEN 1 ELSE 0 END", (ctx.author.id, )).fetchone()[0]
        uuid_already_used = db.execute("SELECT CASE WHEN EXISTS (SELECT * FROM Players WHERE uuid = ?) THEN 1 ELSE 0 END", (get_player_uuid(pseudo),)).fetchone()[0]
        message = ""
        if not already_register and not uuid_already_used:
            db.execute("INSERT INTO Players (discord_id, uuid) VALUES (?,?)", (ctx.author.id, get_player_uuid(pseudo),))
            db.commit()
            message = f"Votre pseudo a été lié à votre compte discord.\n"
        else:
            message ='Vous êtes déjà enregistré.\n'

        resp = com(f"whitelist add {pseudo}")
        if resp == f"Added {pseudo} to the whitelist":
            message += f"Vous avez été ajouté à la whitelist."
        if resp == "Player is already whitelisted":
            message += f"Vous êtes déjà dans la whitelist."
        await ctx.channel.send(message)
    except:
        await ctx.channel.send(f'Votre pseudo n\'existe pas.')

@bot.command()
@commands.has_role("admin")
async def add(ctx, user: discord.User, pseudo: str):
    db = get_db()
    try:
        already_register = db.execute("SELECT CASE WHEN EXISTS (SELECT * FROM Players WHERE discord_id = ? ) THEN 1 ELSE 0 END", (user.id, )).fetchone()[0]
        uuid_already_used = db.execute("SELECT CASE WHEN EXISTS (SELECT * FROM Players WHERE uuid = ?) THEN 1 ELSE 0 END", (get_player_uuid(pseudo),)).fetchone()[0]
        message = ""
        if not already_register and not uuid_already_used:
            db.execute("INSERT INTO Players (discord_id, uuid) VALUES (?,?)", (user.id, get_player_uuid(pseudo),))
            db.commit()
            message = f"Le pseudo de <@{user.id}> a été lié à son compte discord.\n"
        else:
            message = f'<@{user.id}> est déjà enregistré.\n'

        resp = com(f"whitelist add {pseudo}")
        if resp == f"Added {pseudo} to the whitelist":
            message += f"<@{user.id}> a été ajouté à la whitelist."
        if resp == "Player is already whitelisted":
            message += f"<@{user.id}> est déjà dans la whitelist."
        await ctx.channel.send(message)
    except:
        await ctx.channel.send(f'Le pseudo de <@{user.id}> n\'existe pas.')

@add.error
async def add_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")
    
@bot.command()
@commands.has_role("admin")
async def remove(ctx, user: discord.User):
    try:
        db = get_db()
        player_exists = db.execute("SELECT CASE WHEN EXISTS (SELECT * FROM Players WHERE discord_id = ? ) THEN 1 ELSE 0 END", (user.id, )).fetchone()[0]
        if player_exists:
            uuid = get_db().execute("SELECT * FROM Players WHERE discord_id = ?", (user.id, )).fetchone()['uuid']
            db.execute("DELETE FROM Players WHERE discord_id =?", (user.id,))
            db.commit()
            message = f"Le pseudo de <@{user.id}> a été délié de son compte discord.\n"

            pseudo = get_player_name(uuid)
            resp = com(f"whitelist remove {pseudo}")
            if resp == f"Removed {pseudo} from the whitelist":
                message += f"<@{user.id}> a été enlevé de la whitelist."
            if resp == "Player is not whitelisted":
                message += f"<@{user.id}> n\'est pas dans la whitelist."
            if resp == "That player does not exist":
                message += f"Le pseudo de <@{user.id}> n\'existe pas."
        else:
            message = f'<@{user.id}> n\'est pas enregistré.'
        await ctx.channel.send(message)
    except:
        await ctx.channel.send(f'Une erreur est survenue. Demandez à un administrateur de faire votre action manuellement.') 

@remove.error
async def remove_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")

@bot.command()
async def removeme(ctx):
    try:
        db = get_db()
        player_exists = db.execute("SELECT CASE WHEN EXISTS (SELECT * FROM Players WHERE discord_id = ? ) THEN 1 ELSE 0 END", (ctx.author.id, )).fetchone()[0]
        if player_exists:
            uuid = get_db().execute("SELECT * FROM Players WHERE discord_id = ?", (ctx.author.id, )).fetchone()['uuid']
            db.execute("DELETE FROM Players WHERE discord_id =?", (ctx.author.id,))
            db.commit()
            message = f"Votre pseudo a été délié de votre compte discord.\n"

            pseudo = get_player_name(uuid)
            resp = com(f"whitelist remove {pseudo}")
            if resp == f"Removed {pseudo} from the whitelist":
                message += f"Vous avez été enlevé de la whitelist."
            if resp == "Player is not whitelisted":
                message += f"Vous n'êtes pas dans la whitelist."
            if resp == "That player does not exist":
                message += f"Votre pseudo n\'existe pas."
        else:
            message = f'Vous n\'êtes pas enregistré.'
        await ctx.channel.send(message)
    except:
        await ctx.channel.send(f'Une erreur est survenue. Demandez à un administrateur de faire votre action manuellement.') 

@bot.command()
@commands.has_role("admin")
async def stop(ctx):
    com("stop")
    await ctx.channel.send("Le serveur a bien été arrêté.")

@stop.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")

    
@bot.command()
@commands.has_role("admin")
async def restart(ctx):
    com("restart")
    await ctx.channel.send("Le serveur est entrain de redémarrer.")
    print("restarting")
    redo = True
    while redo == True:
        await asyncio.sleep(5)
        try:
            get_if_up()
            await asyncio.sleep(2)
            redo = False
        except:
            print("restarting")
        
    print("restarted")
    await ctx.channel.send("Le serveur a bien été redémarré.")

@restart.error
async def restart_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")

@bot.command()
async def pad(ctx, pseudo: str):
    db = get_db()
    uuid = get_player_uuid(pseudo)
    try:
        discord_id = db.execute("SELECT * FROM Players WHERE uuid =?", (uuid,)).fetchone()['discord_id']
        await ctx.channel.send(f'<@{discord_id}> possède le pseudo {pseudo}.')
    except:
        await ctx.channel.send(f'Le pseudo {pseudo} n\'est pas lié à un compte discord ou n\'existe pas.')
bot.run("")