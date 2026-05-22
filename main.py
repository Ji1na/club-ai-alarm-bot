import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db import init_db
from scheduler import start_scheduler

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    init_db()
    start_scheduler(bot)
    print(f"✅ 봇 실행 중: {bot.user}")


# ── 세션 공지 등록 ──────────────────────────────────────
# 사용법: !세션 제목|날짜|시간|장소|자료URL(선택)
# 예시:   !세션 5월 정기세션|2026-06-01|14:00|공학관 203호|https://...
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

    msg = (
        f"📢 **{title}** 세션 공지\n"
        f"📅 날짜: {date}\n"
        f"⏰ 시간: {time_}\n"
        f"📍 장소: {location}\n"
    )
    if material_url:
        msg += f"📎 자료: {material_url}\n"
    await ctx.send(msg)

    # 지각 상습자 30분 일찍 공지
    from datetime import datetime, timedelta
    late_members = get_late_members(threshold=int(os.getenv("EARLY_NOTIFY_COUNT", 3)))
    if late_members:
        early_time = (datetime.strptime(time_, "%H:%M") - timedelta(minutes=30)).strftime("%H:%M")
        names = ", ".join([m["name"] for m in late_members])
        await ctx.send(
            f"⚠️ {names} — 지각 이력으로 인해 **{early_time}**까지 와주세요! (실제 시작: {time_})"
        )

    await ctx.send(f"✅ 세션 등록 완료 (ID: {session_id})")


# ── 출석 체크 ────────────────────────────────────────────
# 사용법: !출석 세션ID 도착시간
# 예시:   !출석 1 14:08
@bot.command(name="출석")
async def check_attendance(ctx, session_id: int, arrived_at: str):
    from db import record_attendance, get_session
    from late_manager import is_late

    session = get_session(session_id)
    if not session:
        await ctx.send("❌ 세션을 찾을 수 없어요.")
        return

    late = is_late(session["time"], arrived_at)
    record_attendance(
        member_id=ctx.author.id,
        member_name=ctx.author.display_name,
        session_id=session_id,
        arrived_at=arrived_at,
        is_late=late
    )

    if late:
        await ctx.send(f"⏰ {ctx.author.display_name} 지각 처리 ({arrived_at} 도착)")
    else:
        await ctx.send(f"✅ {ctx.author.display_name} 출석 완료!")


# ── 지각 순위 조회 ───────────────────────────────────────
@bot.command(name="순위")
async def show_ranking(ctx):
    from db import get_late_ranking
    ranking = get_late_ranking()

    if not ranking:
        await ctx.send("아직 출석 데이터가 없어요.")
        return

    medals = ["🥇", "🥈", "🥉"]
    msg = "🏆 **지각 순위**\n"
    for i, row in enumerate(ranking):
        medal = medals[i] if i < 3 else f"{i+1}위"
        msg += f"{medal} {row['name']} — {row['late_count']}회\n"

    last = ranking[-1]
    msg += f"\n💀 현재 꼴찌: **{last['name']}** ({last['late_count']}회)"
    await ctx.send(msg)


# ── 퀴즈 생성 ────────────────────────────────────────────
# 사용법: !퀴즈 세션ID
# 발표 자료 URL이 등록된 세션이어야 함
@bot.command(name="퀴즈")
async def generate_quiz(ctx, session_id: int):
    from db import get_session
    from material_reader import read_material
    from quiz_ai import generate_quizzes

    await ctx.send("🤖 퀴즈 생성 중...")

    session = get_session(session_id)
    if not session:
        await ctx.send("❌ 세션을 찾을 수 없어요.")
        return

    content = read_material(session["material_url"])
    if not content:
        await ctx.send("❌ 자료를 읽을 수 없어요. 세션에 자료 URL이 등록됐는지 확인해주세요.")
        return

    quizzes = await generate_quizzes(content)

    msg = "📝 **세션 퀴즈**\n"
    for i, q in enumerate(quizzes, 1):
        msg += f"\nQ{i}. {q['question']}\n> 정답: {q['answer']}\n"
    await ctx.send(msg)


# ── 도움말 ───────────────────────────────────────────────
@bot.command(name="도움말")
async def help_command(ctx):
    msg = (
        "**AI학회 알리미 봇 명령어**\n\n"
        "`!세션 제목|날짜|시간|장소|자료URL` — 세션 등록 + 공지\n"
        "`!출석 세션ID 도착시간` — 출석 체크 (예: `!출석 1 14:08`)\n"
        "`!순위` — 지각 순위 조회\n"
        "`!퀴즈 세션ID` — AI 퀴즈 자동 생성\n"
    )
    await ctx.send(msg)


bot.run(TOKEN)
