import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import database  
from config import TOKEN  

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    database.create_table() 
    print(f" {bot.user} sudah online dan database siap!")

@bot.command()
async def addtask(ctx, *, args):
    try:
        name, date_str = args.split(",", 1)
        due_time = date_str.strip()
        database.add_task(str(ctx.author.id), name.strip(), due_time)
        await ctx.send(f"Tugas **{name.strip()}** ditambahkan! deadline: `{due_time}`")
    except ValueError:
        await ctx.send("Format salah! Gunakan: `!addtask Nama tugas, YYYY-MM-DD HH:MM`")

@bot.command()
async def tasks(ctx):
    """Lihat semua tugasmu"""
    data = database.get_tasks(str(ctx.author.id))
    if not data:
        await ctx.send("Kamu tidak punya tugas yang tersimpan.")
    else:
        msg = "\n".join([f"{tid}. **{name}** ({due})" for tid, name, due in data])
        await ctx.send(f"**Daftar tugasmu:**\n{msg}")

@bot.command()
async def removetask(ctx, task_id: int):
    database.remove_task(task_id, str(ctx.author.id))
    await ctx.send(f"Tugas ID `{task_id}` sudah dihapus.")

bot.run(TOKEN)

