import os
import asyncio
from discord.ext import tasks
from datetime import datetime, timedelta


def start_scheduler(bot):
    daily_check.start(bot)
    weekly_ranking.start(bot)
    print("✅ 스케줄러 시작")


@tasks.loop(hours=24)
async def daily_check(bot):
    """매일 오전 9시 — 내일 세션 있으면 자동 리마인드"""
    now = datetime.now()
    if now.hour != 9:
        return

    channel_id = os.getenv("ANNOUNCE_CHANNEL_ID")
    if not channel_id:
        return

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return

    from db import get_all_sessions
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    sessions = get_all_sessions()

    for s in sessions:
        if s["date"] == tomorrow:
            msg = (
                f"🔔 **내일 세션 리마인드!**\n"
                f"📌 {s['title']}\n"
                f"📅 날짜: {s['date']}\n"
                f"⏰ 시간: {s['time']}\n"
                f"📍 장소: {s['location']}\n"
            )
            if s["material_url"]:
                msg += f"📎 자료: {s['material_url']}\n"
            await channel.send(msg)


@tasks.loop(hours=168)
async def weekly_ranking(bot):
    """매주 월요일 오전 9시에 지각 순위 자동 공지"""
    now = datetime.now()
    if now.weekday() != 0 or now.hour != 9:
        return

    channel_id = os.getenv("ANNOUNCE_CHANNEL_ID")
    if not channel_id:
        return

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return

    from db import get_late_ranking
    ranking = get_late_ranking()
    if not ranking:
        return

    medals = ["🥇", "🥈", "🥉"]
    msg = "📊 **이번 주 지각 순위**\n"
    for i, row in enumerate(ranking):
        medal = medals[i] if i < 3 else f"{i+1}위"
        msg += f"{medal} {row['name']} — {row['late_count']}회\n"

    await channel.send(msg)


@daily_check.before_loop
async def before_daily():
    await asyncio.sleep(0)


@weekly_ranking.before_loop
async def before_weekly():
    await asyncio.sleep(0)