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

    msg = (
        f"📢 **{title}** 세션 공지\n"
        f"📅 날짜: {date}\n"
        f"⏰ 시간: {time_}\n"
        f"📍 장소: {location}\n"
    )
    if material_url:
        msg += f"📎 자료: {material_url}\n"
    await ctx.send(msg)

    from datetime import datetime, timedelta
    late_members = get_late_members(threshold=int(os.getenv("EARLY_NOTIFY_COUNT", 3)))
    if late_members:
        early_time = (datetime.strptime(time_, "%H:%M") - timedelta(minutes=30)).strftime("%H:%M")
        names = ", ".join([m["name"] for m in late_members])
        await ctx.send(
            f"⚠️ {names} — 지각 이력으로 인해 **{early_time}**까지 와주세요! (실제 시작: {time_})"
        )

    await ctx.send(f"✅ 세션 등록 완료 (ID: {session_id})")


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
    msg += f"\n💀 현재 꼴찌: **{last['name']}** ({last['last_count']}회)"
    await ctx.send(msg)


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
        await ctx.send("❌ 자료를 읽을 수 없어요.")
        return

    quizzes = await generate_quizzes(content)

    msg = "📝 **세션 퀴즈**\n"
    for i, q in enumerate(quizzes, 1):
        msg += f"\nQ{i}. {q['question']}\n> 정답: {q['answer']}\n"
    await ctx.send(msg)


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


@bot.tree.command(name="upload_material", description="발표자료를 업로드하고 퀴즈를 생성합니다.")
async def upload_material(
    interaction: discord.Interaction,
    session_id: int,
    file: discord.Attachment
):
    await interaction.response.defer(ephemeral=True)
    from material_reader import extract_text_from_discord_attachment
    from quiz_ai import generate_quizzes

    text = await extract_text_from_discord_attachment(file)
    if not text:
        await interaction.followup.send("❌ 파일에서 텍스트를 읽을 수 없어요.", ephemeral=True)
        return

    quizzes = await generate_quizzes(text, count=10)
    msg = "\n".join([f"Q{i+1}. {q['question']}\n정답: {q['answer']}" for i, q in enumerate(quizzes)])
    await interaction.followup.send("✅ 퀴즈 생성 완료! DM으로 보냈어요.", ephemeral=True)
    await interaction.user.send(msg)


bot.run(TOKEN)