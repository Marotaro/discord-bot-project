import discord
from servermc import *
from db.db import *
from config import *
import sqlite3
import asyncio

from discord.ext import commands
from discord.ext.commands import check, Context

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

def is_channel(ctx: Context):
    return ctx.channel.id in [1225844630948417617,1225487143288180795]

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.command()
@commands.check(is_channel)
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
@commands.has_any_role('Fondateur','mods')
@commands.check(is_channel)
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
@commands.has_any_role('Fondateur','mods')
@commands.check(is_channel)
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
@commands.check(is_channel)
@commands.has_any_role('Fondateur','mods')
async def removeall(ctx):
    db = get_db()
    players = db.execute("SELECT * FROM Players")
    db.execute("DELETE FROM Players")
    db.commit()
    for player in players:
        com(f"whitelist remove {get_player_name(player['uuid'])}")
    await ctx.channel.send(f"Tous les joueurs ont été enlevés de la whitelist et déliés de leur compte discord.")

@bot.command()
@commands.check(is_channel)
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
@commands.check(is_channel)
@commands.has_any_role('Fondateur','mods')
async def stop(ctx):
    com("stop")
    await ctx.channel.send("Le serveur va s'arrêter.")
    await asyncio.sleep(30)
    try:
        get_if_up()
        await ctx.channel.send("Le serveur n'a pas été arrêté")
    except:
        await ctx.channel.send("Le serveur a bien été arrêté.")


@stop.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")

    
@bot.command()
@commands.check(is_channel)
@commands.has_any_role('Fondateur','mods')
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
@commands.check(is_channel)
async def pad(ctx, selector):
    db = get_db()
    try:
        discord_id = int(selector[2:-1])
        print(selector)
        print(discord_id)
        discord_id, uuid = db.execute("SELECT discord_id, uuid FROM Players WHERE discord_id =?", (discord_id,)).fetchone()
    except:
        try:
            discord_id, uuid = db.execute("SELECT discord_id, uuid FROM Players WHERE uuid =?", (get_player_uuid(selector),)).fetchone()
        except:
            await ctx.channel.send(f'Le joueur n\'est pas enregistrer ou n\'existe pas.')
            return
    
    embedVar = discord.Embed(title=f"{get_player_name(uuid)}", description=f"<@{discord_id}>", color=0x2a7c1d)
    embedVar.set_image(url = f"https://mc-heads.net/avatar/{uuid}/150")
    await ctx.channel.send(embed=embedVar)

@bot.command()
@commands.check(is_channel)
async def listpad(ctx):
    db = get_db()
    players = db.execute("SELECT discord_id, uuid FROM Players").fetchall()
    await ctx.channel.send(f"Liste des {len(players)} joueurs enregistrés :")
    embs = []
    for player in players:
        embedVar = discord.Embed(title=f"{get_player_name(player['uuid'])}", description=f"<@{player['discord_id']}>", color=0x2a7c1d)
        embedVar.set_image(url = f"https://mc-heads.net/avatar/{player['uuid']}/150")
        embs.append(embedVar)
    await ctx.channel.send(embeds=embs)

@bot.command()
@commands.check(is_channel)
@commands.has_any_role('Fondateur','mods')
async def clear(ctx, number: str):
    if number == "all":
        await ctx.channel.purge(limit=None)
    else:
        await ctx.channel.purge(limit = int(number)+1)


@bot.command()
@commands.check(is_channel)
async def info(ctx):
    embtitre = discord.Embed(title="Info sur les commandes", color=0x2a7c1d)

    embuser = discord.Embed(title="Commandes pour les utilisateurs",color=0x2a7c1d)
    embuser.add_field(name="addme", value="S'ajouter à la whitelist\n\t$addme <pseudo>", inline = False)
    embuser.add_field(name="removeme", value="S'enlever de la whitelist\n\t$removeme",inline = False)
    embuser.add_field(name="pad", value="Retourne les informations d'un joueur\n\t$pad <pseudo> ou <@user>",inline = False)
    embuser.add_field(name="listpad", value="Retourne la liste des joueurs enregistrés\n\t$listpad",inline = False)

    embmodo = discord.Embed(title="Commandes pour les modos",color=0x2a7c1d)
    embmodo.add_field(name="add", value="Ajoute un joueur à la whitelist\n\t$add <@user> <pseudo>",inline = False)
    embmodo.add_field(name="remove", value="Enleve un joueur de la whitelist\n\t$remove <@user>",inline = False)
    embmodo.add_field(name="clear", value="Efface les messages\n\t$clear <number> ou all",inline = False)
    embmodo.add_field(name="stop", value="Arrête le serveur\n\t$stop",inline = False)
    embmodo.add_field(name="restart", value="Redémarre le serveur\n\t$restart",inline = False)

    await ctx.channel.send(embeds=[embtitre,embuser,embmodo])


bot.run(token)