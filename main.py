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

    from db import save_session
    session_id = save_session(title, date, time_, location, material_url)

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

    # 개인별 DM - 지각 3회 이상이면 30분 일찍 공지
    from datetime import datetime, timedelta
    try:
        from late_manager import get_late_records
        session_start = datetime.strptime(f"{date} {time_}", "%Y-%m-%d %H:%M")
        early_time = (session_start - timedelta(minutes=30)).strftime("%H:%M")

        for member in ctx.guild.members:
            if member.bot:
                continue
            try:
                records = get_late_records(member.id)
                if len(records) >= 3:
                    notify_time = early_time
                else:
                    notify_time = time_

                dm_msg = (
                    f"📢 **{title}** 세션 공지\n"
                    f"📅 날짜: {date}\n"
                    f"⏰ 시간: **{notify_time}**\n"
                    f"📍 장소: {location}\n"
                )
                await member.send(dm_msg)
            except Exception:
                pass
    except ImportError:
        pass

    await ctx.send(f"✅ 세션 등록 완료 (ID: {session_id})")


@bot.command(name="출석")
async def check_attendance(ctx, session_id: int, arrived_at: str):
    if ctx.channel.id != ATTENDANCE_CHANNEL_ID:
        await ctx.send(f"❌ 출석 체크는 <#{ATTENDANCE_CHANNEL_ID}> 채널에서만 가능해요!")
        return

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


@bot.tree.command(name="late", description="운영진: 지각 기록 입력")
async def late_record(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: int,
    session_date: str
):
    try:
        from late_manager import add_late_record, make_late_record_dm
        add_late_record(
            member_id=member.id,
            name=member.display_name,
            session_date=session_date,
            minutes=minutes,
        )
        dm_message = make_late_record_dm(session_date, minutes)
        await member.send(dm_message)
        await interaction.response.send_message(
            f"✅ {member.display_name} {minutes}분 지각 기록 완료!", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ 오류 발생: {e}", ephemeral=True
        )


@bot.tree.command(name="late_rank", description="운영진: 전체 지각 순위 확인")
async def late_rank(interaction: discord.Interaction):
    try:
        from late_manager import make_late_rank_report
        report = make_late_rank_report()
        await interaction.response.send_message(report, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(
            f"❌ 오류 발생: {e}", ephemeral=True
        )


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


@bot.tree.command(name="upload_material", description="발표자료를 업로드하고 퀴즈를 생성합니다.")
async def upload_material(
    interaction: discord.Interaction,
    file: discord.Attachment
):
    await interaction.response.defer(ephemeral=True)
    try:
        from material_reader import extract_text_from_discord_attachment
        from quiz_ai import generate_quizzes

        text = await extract_text_from_discord_attachment(file)
        if not text:
            await interaction.followup.send("❌ 파일에서 텍스트를 읽을 수 없어요.", ephemeral=True)
            return

        quizzes = await generate_quizzes(text, count=10)
        quiz_message = "\n".join([
            f"Q{i+1}. {q['question']}\n정답: {q['answer']}"
            for i, q in enumerate(quizzes)
        ])

        def split_message(msg, limit=1800):
            return [msg[i:i+limit] for i in range(0, len(msg), limit)]

        sent_count = 0
        failed_count = 0
        for user in interaction.guild.members:
            if user.bot:
                continue
            try:
                for chunk in split_message(quiz_message):
                    await user.send(chunk)
                sent_count += 1
            except Exception:
                failed_count += 1

        await interaction.followup.send(
            f"✅ 퀴즈 생성 완료!\nDM 발송 성공: {sent_count}명\nDM 발송 실패: {failed_count}명",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ 오류 발생: {e}", ephemeral=True)


@bot.command(name="도움말")
async def help_command(ctx):
    msg = (
        "**AI학회 알리미 봇 명령어**\n\n"
        "`!세션 제목|날짜|시간|장소|자료URL` — 세션 등록 + 공지\n"
        "`!출석 세션ID 도착시간` — 출석 체크 (출석채널에서만)\n"
        "`!순위` — 지각 순위 조회\n"
        "`/late member minutes session_date` — 지각 기록 입력 (운영진)\n"
        "`/late_rank` — 전체 지각 순위 (운영진)\n"
        "`/upload_material file` — 발표자료 업로드 + 퀴즈 생성\n"
    )
    await ctx.send(msg)


bot.run(TOKEN)