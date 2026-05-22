import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db import init_db
from scheduler import start_scheduler

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NOTICE_CHANNEL_ID = int(os.getenv("NOTICE_CHANNEL_ID", 0))
ATTENDANCE_CHANNEL_ID = int(os.getenv("ATTENDANCE_CHANNEL_ID", 0))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    init_db()
    start_scheduler(bot)
    await bot.tree.sync()
    print(f"✅ 봇 실행 중: {bot.user}")


@bot.command(name="세션")
async def register_session(ctx, *, args: str):
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 4:
        await ctx.send("❌ 형식: `!세션 제목|날짜|시간|장소|자료URL(선택)`")
        return

    title, date, time_, location = parts[0], parts[1], parts[2], parts[3]
    material_url = parts[4] if len(parts) > 4 else None

    from db import save_session, get_late_members
    session_id = save_session(title, date, time_, location, material_url)

    # 공지 채널에 발송
    notice_channel = bot.get_channel(NOTICE_CHANNEL_ID)
    msg = (
        f"📢 **{title}** 세션 공지\n"
        f"📅 날짜: {date}\n"
        f"⏰ 시간: {time_}\n"
        f"📍 장소: {location}\n"
    )
    if material_url:
        msg += f"📎 자료: {material_url}\n"

    if notice_channel:
        await notice_channel.send(msg)
    else:
        await ctx.send(msg)

    from datetime import datetime, timedelta
    late_members = get_late_members(threshold=int(os.getenv("EARLY_NOTIFY_COUNT", 3)))
    if late_members:
        early_time = (datetime.strptime(time_, "%H:%M") - timedelta(minutes=30)).strftime("%H:%M")
        for m in late_members:
            user = discord.utils