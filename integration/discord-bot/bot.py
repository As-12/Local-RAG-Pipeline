import os

import discord
import httpx
from discord.ext import commands


DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
RAG_API_URL = os.getenv("RAG_API_URL", "http://rag-api:8080")


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


async def ask_rag_api(question: str) -> dict:
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{RAG_API_URL}/query",
            json={"query": question},
        )
        response.raise_for_status()
        return response.json()


def format_sources(sources: list[dict]) -> str:
    if not sources:
        return "No sources returned."

    lines = []

    for source in sources[:5]:
        filename = source.get("filename", "unknown")
        chunk_id = source.get("chunk_id", "unknown")
        score = source.get("score")

        if isinstance(score, float):
            lines.append(f"- `{filename}` chunk `{chunk_id}` score `{score:.3f}`")
        else:
            lines.append(f"- `{filename}` chunk `{chunk_id}`")

    return "\n".join(lines)


def split_discord_message(text: str, max_length: int = 1900) -> list[str]:
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")
    print("Available guilds:")

    for guild in bot.guilds:
        print(f"- {guild.name}: {guild.id}")


@bot.command(name="ask")
async def ask(ctx: commands.Context, *, question: str | None = None):
    if not question:
        await ctx.reply(
            "Please ask a question. Example: `!ask What is Project Moonstone?`"
        )
        return

    async with ctx.typing():
        try:
            data = await ask_rag_api(question)
        except httpx.HTTPStatusError as exc:
            await ctx.reply(
                f"RAG API returned an error: `{exc.response.status_code}`"
            )
            return
        except httpx.RequestError as exc:
            await ctx.reply(
                f"Could not reach RAG API: `{exc}`"
            )
            return
        except Exception as exc:
            await ctx.reply(
                f"Unexpected bot error: `{type(exc).__name__}: {exc}`"
            )
            return

    answer = data.get("answer", "No answer returned.")
    sources = data.get("sources", [])

    message = f"""**Question**
{question}

**Answer**
{answer}

**Sources**
{format_sources(sources)}
"""

    for part in split_discord_message(message):
        await ctx.reply(part, mention_author=False)


bot.run(DISCORD_TOKEN)