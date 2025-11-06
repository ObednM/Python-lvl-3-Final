import discord
from discord.ext import commands
from discord.ext.tasks import loop
from datetime import datetime, timedelta
from discord.ui import View, Button, button, Modal, TextInput
from typing import Optional
import asyncio
import database  
from config import TOKEN  

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def addtask(ctx, name: str, date: str, time: str):
    try:
        due_time = f"{date} {time}"
        datetime.strptime(due_time, "%Y-%m-%d %H:%M")
        database.add_task(str(ctx.author.id), name, due_time)
        await ctx.send(f"Tugas **{name}** ditambahkan untuk `{due_time}`!")
    except ValueError:
        await ctx.send("Format salah! Gunakan: `!addtask \"Nama_Tugas\" YYYY-MM-DD HH:MM`")

@bot.command()
async def tasklist(ctx):
    await list_tasks(ctx)

@bot.command()
async def removetask(ctx, index: int):
    user_id = str(ctx.author.id)
    db_id = database.get_task_id_by_index(user_id, index)
    if db_id is None:
        await ctx.send(f"Tidak ada tugas dengan nomor `{index}`.")
        return
    database.remove_task(db_id, user_id)
    await ctx.send(f"Tugas nomor `{index}` (id:{db_id}) sudah dihapus.")


@bot.command()
async def edittask(ctx, task_id: int, field: str, *, value: str):
    user_id = str(ctx.author.id)
    field = field.lower()
    if field not in ("name", "reminder"):
        await ctx.send("Field harus 'name' atau 'reminder'. Contoh: `!edittask 3 name Belajar`")
        return

    if field == "reminder":
        try:
            datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            await ctx.send("Format tanggal salah. Gunakan: `YYYY-MM-DD HH:MM`")
            return

    success = False
    if field == "name":
        success = database.update_task(task_id, user_id, new_name=value)
    else:
        success = database.update_task(task_id, user_id, new_reminder=value)

    if success:
        await ctx.send(f"Tugas ID `{task_id}` berhasil diperbarui.")
    else:
        await ctx.send(f"Gagal memperbarui tugas ID `{task_id}`. Pastikan ID benar dan tugas milikmu.")

class EditTaskModal(Modal, title="Edit Task"):
    def __init__(self, task_id: int, user_id: str, original_name: str, original_time: str):
        super().__init__()
        self.task_id = task_id
        self.user_id = user_id
        
        self.name = TextInput(
            label="Task Name",
            placeholder="Enter new task name...",
            default=original_name,
            required=False,
            max_length=100
        )
        self.time = TextInput(
            label="Due Time (YYYY-MM-DD HH:MM)",
            placeholder="Enter new due time...",
            default=original_time,
            required=False
        )
        self.add_item(self.name)
        self.add_item(self.time)

    async def on_submit(self, interaction: discord.Interaction):
        changes = []
        if self.name.value != "":
            success = database.update_task(self.task_id, self.user_id, new_name=self.name.value)
            if success:
                changes.append("name")

        if self.time.value != "":
            try:
                datetime.strptime(self.time.value, "%Y-%m-%d %H:%M")
                success = database.update_task(self.task_id, self.user_id, new_reminder=self.time.value)
                if success:
                    changes.append("due time")
            except ValueError:
                await interaction.response.send_message("Invalid date format. Use: YYYY-MM-DD HH:MM", ephemeral=True)
                return

        if changes:
            await interaction.response.send_message(
                f"Updated task {self.task_id}'s {' and '.join(changes)}!", ephemeral=True
            )
        else:
            await interaction.response.send_message("No changes were made.", ephemeral=True)

class TaskView(View):
    def __init__(self, task_id: int, task_name: str, due_time: str, user_id: str):
        super().__init__(timeout=180)  # Buttons expire after 3 minutes
        self.task_id = task_id
        self.task_name = task_name
        self.due_time = due_time
        self.user_id = user_id

    @button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("You can only edit your own tasks!", ephemeral=True)
            return
            
        modal = EditTaskModal(self.task_id, self.user_id, self.task_name, self.due_time)
        await interaction.response.send_modal(modal)

    @button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("You can only delete your own tasks!", ephemeral=True)
            return
            
        database.remove_task(self.task_id, self.user_id)
        await interaction.response.send_message(f"Task **{self.task_name}** deleted!", ephemeral=True)
        self.disable_all_items()
        await interaction.message.edit(view=self)

    @button(label="Done", style=discord.ButtonStyle.success)
    async def done_button(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("You can only complete your own tasks!", ephemeral=True)
            return
            
        database.remove_task(self.task_id, self.user_id)
        await interaction.response.send_message(f"Task **{self.task_name}** marked as done! 🎉", ephemeral=True)
        self.disable_all_items()
        await interaction.message.edit(view=self)

@bot.command(name="tasks")
async def list_tasks(ctx):
    """List tasks showing a 1-based index and the underlying DB id."""
    data = database.get_tasks(str(ctx.author.id))
    if not data:
        await ctx.send("Kamu tidak punya tugas yang tersimpan.")
        return

    await ctx.send("**Your Tasks:**")
    for i, (tid, name, due) in enumerate(data, start=1):
        view = TaskView(tid, name, due, str(ctx.author.id))
        await ctx.send(
            f"Task {i}:\n"
            f"**{name}**\n"
            f"Due: {due}",
            view=view
        )

@bot.command()
async def cleartasks(ctx):
    database.clear_tasks(str(ctx.author.id))
    await ctx.send("Semua tugas kamu sudah dihapus!")

class ReminderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    @loop(minutes=1)
    async def check_reminders(self):
        now = datetime.now()
        with database.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, user_id, task_name, reminder FROM tasks")
            for task_id, user_id, task_name, reminder_time in c.fetchall():
                try:
                    remind_time = datetime.strptime(reminder_time, "%Y-%m-%d %H:%M")
                    if now >= remind_time:
                        try:
                            user = await self.bot.fetch_user(int(user_id))
                            await user.send(f"Reminder: task **{task_name}** is due!")
                            database.remove_task(task_id, user_id)
                        except discord.NotFound:
                            print(f"User {user_id} not found")
                        except discord.HTTPException as e:
                            print(f"Failed to send reminder to user {user_id}: {e}")
                except ValueError as e:
                    print(f"Invalid date format for task {task_id}: {e}")

    def cog_unload(self):
        self.check_reminders.cancel()

async def setup(bot):
    await bot.add_cog(ReminderCog(bot))

@bot.event
async def on_ready():
    database.create_table()
    await setup(bot)
    print(f" {bot.user} ready")

bot.run(TOKEN)

