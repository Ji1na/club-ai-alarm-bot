import os
from discord.ext import tasks
from datetime import datetime


def start_scheduler(bot):
    """봇 시작 시 주기적 작업 등록"""
    weekly_ranking.start(bot)
    print("✅ 스케줄러 시작")


@tasks.loop(hours=168)  # 매주 실행 (7일 * 24시간)
async def weekly_ranking(bot):
    """매주 월요일 오전 9시에 지각 순위 자동 공지"""
    now = datetime.now()
    # 월요일(0) + 오전 9시 체크
    if now.weekday() != 0 or now.hour != 9:
        return

    from db import get_late_ranking

    channel_id = os.getenv("ANNOUNCE_CHANNEL_ID")
    if not channel_id:
        return

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return

    ranking = get_late_ranking()
    if not ranking:
        return

    medals = ["🥇", "🥈", "🥉"]
    msg = "📊 **이번 주 지각 순위**\n"
    for i, row in enumerate(ranking):
        medal = medals[i] if i < 3 else f"{i+1}위"
        msg += f"{medal} {row['name']} — {row['late_count']}회\n"

    await channel.send(msg)


@weekly_ranking.before_loop
async def before_weekly_ranking():
    import discord
    # 봇이 준비될 때까지 대기
    pass
