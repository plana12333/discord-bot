import discord
from discord.ext import commands, tasks
import time
from datetime import datetime, timedelta
import asyncio
from flask import Flask
from threading import Thread

# --- ١. دروستکردنی Web Server بۆ ئەوەی Render بۆتەکە ئۆنلاین بهێڵێتەوە ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online and Ready!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ٢. کۆدی سەرەکی بۆتی دیسکۆرد ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

vc_start_times = {}
user_vc_duration = {}

@bot.event
async def on_ready():
    print(f'بۆتەکە چالاک بوو وەک: {bot.user.name}')
    reset_daily_stats.start()

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        vc_start_times[member.id] = time.time()
        
    elif before.channel is not None and after.channel is None:
        if member.id in vc_start_times:
            start_time = vc_start_times.pop(member.id)
            duration = time.time() - start_time
            user_vc_duration[member.id] = user_vc_duration.get(member.id, 0) + duration

@tasks.loop(hours=24)
async def reset_daily_stats():
    user_vc_duration.clear()
    now = time.time()
    for user_id in vc_start_times:
        vc_start_times[user_id] = now
    print("داتاکان لە سەعات ١٢ی شەو سفر کرانەوە.")

@reset_daily_stats.before_loop
async def before_reset():
    await bot.wait_until_ready()
    now = datetime.now()
    next_midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    seconds_until_midnight = (next_midnight - now).total_seconds()
    await asyncio.sleep(seconds_until_midnight)

@bot.command(name="time")
async def user_time(ctx):
    user = ctx.author
    
    total_seconds = user_vc_duration.get(user.id, 0)
    if user.id in vc_start_times:
        total_seconds += (time.time() - vc_start_times[user.id])
        
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    points = 1 if hours >= 3 else 0

    embed = discord.Embed(
        title="👑 Staff Activity Profile",
        description=f"ئاماری چالاکی کاتی دەنگی بۆ **{user.display_name}**",
        color=discord.Color.blurple()
    )
    
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    
    embed.add_field(
        name="⭐ Daily Score",
        value=f"> **{points} / 1** Point",
        inline=True
    )
    
    embed.add_field(
        name="🎙️ Voice Time",
        value=f"> **{hours}h {minutes}m {seconds}s**",
        inline=True
    )
    
    embed.set_footer(
        text=f"Requested by {user.name} • Daily Max: 1 Point (Resets at 12:00 AM)", 
        icon_url=ctx.guild.icon.url if ctx.guild.icon else None
    )
    
    await ctx.send(embed=embed)

# بەگەڕخستنی وێب سێرڤەر و بۆتەکە
keep_alive()
bot.run("MTUzMDUzOTQ4MTM0NDc3MDEzMQ.GEKr0u.GL6XbAZJgjzZAq_RRX-PpyM6yKX4lDDonGvSFs")
