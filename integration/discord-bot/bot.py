import os
import textwrap

import discord
import httpx
from discord import app_commands
from discord.ext import commands


DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
RAG_API_URL = os.getenv("RAG_API_URL", "http://rag-api:8080")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")


intents = discord.Intents.default()

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
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        chunks.append(text[:max_length])
        text = text[max_length:]

    return chunks


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")

    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} slash command(s) to guild {GUILD_ID}.")
    else:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global slash command(s).")


if GUILD_ID:
    guild_object = discord.Object(id=int(GUILD_ID))
else:
    guild_object = None


@bot.tree.command(
    name="ai",
    description="Ask the local RAG knowledge base.",
    guild=guild_object,
)
@app_commands.describe(
    question="The question to ask your local RAG system."
)
async def rag(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)

    try:
        data = await ask_rag_api(question)
    except httpx.HTTPStatusError as exc:
        await interaction.followup.send(
            f"RAG API returned an error: `{exc.response.status_code}`"
        )
        return
    except httpx.RequestError as exc:
        await interaction.followup.send(
            f"Could not reach RAG API: `{exc}`"
        )
        return
    except Exception as exc:
        await interaction.followup.send(
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
        await interaction.followup.send(part)


bot.run(DISCORD_TOKEN)