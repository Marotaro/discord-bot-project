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

async def delete_user_message(ctx: Context):
    msg = await ctx.channel.fetch_message(ctx.message.id)
    await msg.delete()

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.command()
@commands.check(is_channel)
async def addme(ctx, pseudo: str ):    
    db = get_db()
    try:
        if get_if_up() == 'on':
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
        else:
            ctx.channel.send("Impossible d'effectuer cette action lorsque le serveur est arrêté.")
        db.close()
    except:
        await ctx.channel.send(f'Votre pseudo n\'existe pas.')
        db.close()

@bot.command()
@commands.has_any_role('Fondateur','mods')
@commands.check(is_channel)
async def add(ctx, user: discord.User, pseudo: str):
    db = get_db()
    try:
        if get_if_up() == 'on':
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
        else:
            ctx.channel.send("Impossible d'effectuer cette action lorsque le serveur est arrêté.")
        db.close()
    except:
        await ctx.channel.send(f'Le pseudo de <@{user.id}> n\'existe pas.')
        db.close()

@add.error
async def add_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")
    
@bot.command()
@commands.has_any_role('Fondateur','mods')
@commands.check(is_channel)
async def remove(ctx, user: discord.User):
    try:
        if get_if_up() == 'on':
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
            db.close()
        else:
            ctx.channel.send("Impossible d'effectuer cette action lorsque le serveur est arrêté.")
    except:
        await ctx.channel.send(f'Une erreur est survenue. Demandez à un administrateur de faire votre action manuellement.') 

@remove.error
async def remove_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")

@bot.command()
@commands.check(is_channel)
@commands.has_any_role('Fondateur')
async def removeall(ctx):
    if get_if_up() == 'on':
        db = get_db()
        players = db.execute("SELECT * FROM Players")
        db.execute("DELETE FROM Players")
        db.commit()
        for player in players:
            com(f"whitelist remove {get_player_name(player['uuid'])}")
        await ctx.channel.send(f"Tous les joueurs ont été enlevés de la whitelist et déliés de leur compte discord.")
        db.close()
    else:
        ctx.channel.send("Impossible d'effectuer cette action lorsque le serveur est arrêté.")

@bot.command()
@commands.check(is_channel)
async def removeme(ctx):
    try:
        if get_if_up() == 'on':
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
            db.close()
        else:
            ctx.channel.send("Impossible d'effectuer cette action lorsque le serveur est arrêté.")
    except:
        await ctx.channel.send(f'Une erreur est survenue. Demandez à un administrateur de faire votre action manuellement.')

@bot.command()
@commands.check(is_channel)
@commands.has_any_role('Fondateur','mods')
async def stop(ctx):
    if get_if_up() == 'on':
        server_action('stop')
        await ctx.channel.send("Le serveur va s'arrêter.")
        await asyncio.sleep(30)
        if get_if_up() == "off":
            await ctx.channel.send("Le serveur est arrêté.")
        else:
            await ctx.channel.send("Une erreur est survenue lors de l'arrêt du serveur.")
    else:
        await ctx.channel.send("Le serveur est déjà arrêté.")


@stop.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")

    
@bot.command()
@commands.check(is_channel)
@commands.has_any_role('Fondateur','mods')
async def restart(ctx):
    if get_if_up() == 'on':
        server_action('restart')
        await ctx.channel.send("Le serveur est entrain de redémarrer.")
        print("restarting")
        redo = True
        while redo == True:
            await asyncio.sleep(5)
            status = get_if_up()
            if status == 'on':
                redo = False
                await asyncio.sleep(1)
                print("restarted")
                await ctx.channel.send("Le serveur a bien été redémarré.")
            elif status == 'error':
                redo = False
                print("error")
                await ctx.channel.send("Une erreur est survenue lors du redémarrage du serveur.")
            else:
                print('restarting')
    else:
        await ctx.channel.send("Le serveur est arrêté")
        
    

@restart.error
async def restart_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle nécessaire pour exécuter cette commande.")


@bot.command()
@commands.check(is_channel)
@commands.has_any_role('Fondateur','mods')
async def start(ctx):
    if get_if_up() == 'off':
        server_action('start')
        await ctx.channel.send("Le serveur est entrain de démarrer.")
        print("starting")
        redo = True
        while redo == True:
            await asyncio.sleep(5)
            status = get_if_up()
            if status == 'on':
                redo = False
                await asyncio.sleep(1)
                print("started")
                await ctx.channel.send("Le serveur a bien été démarré.")
            elif status == 'error':
                redo = False
                print("error")
                await ctx.channel.send("Une erreur est survenue lors du démarrage du serveur.")
            else:
                print('starting')
    else:
        await ctx.channel.send("Le serveur est déjà démarré.")

@start.error
async def start_error(ctx, error):
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
        db.close()
    except:
        try:
            discord_id, uuid = db.execute("SELECT discord_id, uuid FROM Players WHERE uuid =?", (get_player_uuid(selector),)).fetchone()
            db.close()
        except:
            await ctx.channel.send(f'Le joueur n\'est pas enregistrer ou n\'existe pas.')
            db.close()
            return
    
    embedVar = discord.Embed(title=f"{get_player_name(uuid)}", description=f"<@{discord_id}>", color=0x2a7c1d)
    embedVar.set_image(url = f"https://api.mineatar.io/body/full/{uuid}?scale=10")
    await ctx.channel.send(embed=embedVar)

@bot.command()
@commands.check(is_channel)
async def listpad(ctx):
    db = get_db()
    players = db.execute("SELECT discord_id, uuid FROM Players").fetchall()
    embtitle = discord.Embed(title=f"Liste des {len(players)} joueurs enregistrés", color=0x2a7c1d)
    await ctx.channel.send(embed=embtitle)
    for player in players:
        embedVar = discord.Embed(title=f"{get_player_name(player['uuid'])}", description=f"<@{player['discord_id']}>", color=0x2a7c1d)
        embedVar.set_image(url = f"https://api.mineatar.io/body/full/{player['uuid']}?scale=10")
        await ctx.channel.send(embed=embedVar)

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
async def send(ctx, *message: str):
    message = " ".join(message)
    db = get_db()
    if db.execute("SELECT CASE WHEN EXISTS (SELECT * FROM Players WHERE discord_id = ? ) THEN 1 ELSE 0 END", (ctx.author.id, )).fetchone()[0]:
        uuid = db.execute("SELECT uuid FROM Players WHERE discord_id =?", (ctx.author.id,)).fetchone()['uuid']
        player_name = get_player_name(uuid)
        first_part = "tellraw @a [\"\",{"
        name_part = f"\"text\":\"[{player_name}]\",\"color\":\"#6245F2\""
        message_part = f"\"text\":\" {message}\",\"color\":\"#ffffff\""
        middle_part = "},{".join([name_part, message_part])
        print(middle_part)
        last_part = "}]"
        final_message = "".join([first_part, middle_part, last_part])
        print(final_message)
        com(final_message)
        db.close()


@bot.command()
@commands.check(is_channel)
@commands.has_any_role('Fondateur','mods')
async def kick(ctx, selector):
    print(ctx.message.id)
    db = get_db()
    try:
        discord_id = int(selector[2:-1])
        print(selector)
        print(discord_id)
        discord_id, uuid = db.execute("SELECT discord_id, uuid FROM Players WHERE discord_id =?", (discord_id,)).fetchone()
        db.close()
    except:
        try:
            discord_id, uuid = db.execute("SELECT discord_id, uuid FROM Players WHERE uuid =?", (get_player_uuid(selector),)).fetchone()
            db.close()
        except:
            await ctx.author.send(f'Le joueur n\'est pas enregistrer ou n\'existe pas.')
            db.close()
            return
        
@bot.command()
@commands.check(is_channel)
@commands.has_any_role('Fondateur')
async def change_info(ctx, type : str, info: str):
    change_server_info(type, info)
    await ctx.channel.send(f"{type} du serveur modifiées avec succès.")


@bot.command()
@commands.check(is_channel)
async def statut(ctx):
    if get_if_up() == 'on':
        def bar(live, maximum, nb_bar):
            progress = live/maximum
            bold_bar = [ '\|' for i in range(nb_bar) if progress>i/nb_bar]
            bold = "**" + "".join(bold_bar) + "**"
            normal_bar = ['I']*(nb_bar-len(bold_bar))
            normal = "".join(normal_bar)
            return bold+normal
        ressources = get_ressources()
        embstatut = discord.Embed(title="Statut du serveur:",description="Démarrer" ,color=0x2a7c1d)
        livecpu = int(ressources['cpu']['live'])
        maxcpu = int(ressources['cpu']['max'])
        embstatut.add_field(name="CPU:", value=f"{bar(livecpu,maxcpu,20)} {round(100*livecpu/maxcpu,2)}%")
        liveram = int(ressources['memory']['live'])
        maxram = int(ressources['memory']['max'])
        embstatut.add_field(name="RAM:", value=f"{bar(liveram,maxram,20)} {round(100*liveram/maxram,2)}%")
        livedisk = int(ressources['disk']['live'])
        maxdisk = int(ressources['disk']['max'])
        embstatut.add_field(name="DISQUE:", value=f"{bar(livedisk,maxdisk,20)} {round(100*livedisk/maxdisk,2)}%")
        embstatut.add_field(name="PING:", value=f"**{round(get_ping(),2)}**ms")
        content=get_content()
        embstatut.add_field(name="VERSION:", value=f"{content['version'].split()[1]}")
        embstatut.add_field(name="JOUEURS:", value=f"**{content['players']['online']}**/{content['players']['max']}")
        await ctx.channel.send(embed=embstatut)
        print(get_content())
    elif get_if_up() == 'off':
        embstatut = discord.Embed(title="Statut du serveur:",description="Arrêter" ,color=0x9c0000)
        await ctx.channel.send(embed=embstatut)

@bot.command()
@commands.check(is_channel)
async def players(ctx):
    if get_if_up() == 'on':
        content=get_content()
        embstatut = discord.Embed(title=f"Joueurs en ligne: **{content['players']['online']}**/{content['players']['max']}",color=0x2a7c1d)
        db = get_db()
        for name in get_players():
            try:
                uuid = get_player_uuid(name)
                discord_id, uuid = db.execute("SELECT discord_id, uuid FROM Players WHERE uuid =?", (uuid,)).fetchone()
                embstatut.add_field(name=name, value=f"<@{discord_id}>", inline = False)
            except:
                embstatut.add_field(name=name, value=f"INCONNU A LA BASE DE DONNES", inline = False)
        db.close()
        await ctx.channel.send(embed=embstatut)


@bot.command()
@commands.check(is_channel)
async def seed(ctx):
    if get_if_up() == 'on':
        embseed = discord.Embed(title = "Seed:", description = f"{com('seed').split()[1][1:-1]}", color=0x2a7c1d)
    else:
        embseed = discord.Embed(title="Seed:",description="Impossible de récupérer la seed du serveur lorsqu'il est éteint.\n Attendez qu'il soit allumé." ,color=0x9c0000)
    await ctx.channel.send(embed=embseed)
@bot.command()
@commands.check(is_channel)
async def info(ctx):
    embtitre = discord.Embed(title="Info sur les commandes", color=0x2a7c1d)

    embuser = discord.Embed(title="Commandes pour les joueurs",color=0x2a7c1d)
    embuser.add_field(name="$addme <pseudo>", value="S'ajouter à la whitelist", inline = False)
    embuser.add_field(name="$removeme", value="S'enlever de la whitelist",inline = False)
    embuser.add_field(name="$pad <pseudo> *ou* <@user>", value="Retourne les informations d'un joueur",inline = False)
    embuser.add_field(name="$listpad", value="Retourne la liste des joueurs enregistrés",inline = False)
    embuser.add_field(name="$send <message>", value="Envoie un message sur le serveur minecraft",inline = False)
    embuser.add_field(name="$statut", value="Retourne le statut du serveur",inline = False)
    embuser.add_field(name="$seed", value="Retourne la seed du serveur",inline = False)
    embuser.add_field(name="$players", value="Retourne la liste des joueurs en ligne",inline = False)

    embmodo = discord.Embed(title="Commandes pour les modos",color=0x2a7c1d)
    embmodo.add_field(name="$add <@user> <pseudo>", value="Ajoute un joueur à la whitelist",inline = False)
    embmodo.add_field(name="$remove <@user> <pseudo>", value="Enleve un joueur de la whitelist",inline = False)
    embmodo.add_field(name="$clear <number> *ou* all", value="Efface les messages",inline = False)
    embmodo.add_field(name="$start", value="Démarre le serveur",inline = False)
    embmodo.add_field(name="$stop", value="Arrête le serveur",inline = False)
    embmodo.add_field(name="$restart", value="Redémarre le serveur",inline = False)

    await ctx.channel.send(embeds=[embtitre,embuser,embmodo])




bot.run(token)