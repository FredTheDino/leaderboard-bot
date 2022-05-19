import discord
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import timedelta
from itertools import chain

client = discord.Client()

token = "!"

state = defaultdict(dict)


def parse_pushup(x):
    try:
        if x[0] == token:
            return int(x[1:])
    except:
        pass


def plot_pushups(pushups_users_dates):
    user_per_day = defaultdict(lambda: defaultdict(int))
    for user, data in pushups_users_dates.items():
        for datetime, number in data.items():
            user_per_day[user][datetime.date()] += number

    total_per_day = defaultdict(int)
    for data in pushups_users_dates.values():
        for datetime, number in data.items():
            total_per_day[datetime.date()] += number

    total = sum(total_per_day.values())

    fix, (ax, bx) = plt.subplots(2, 1)
    for user, data in user_per_day.items():
        label = user.name
        ax.plot(list(data.keys()), list(data.values()), label=label)
    ax.legend()

    bx.plot(list(total_per_day.keys()), list(total_per_day.values()), label="total")
    bx.legend()

    fix.tight_layout()
    filename = "pushups.png"
    fix.savefig(filename)
    with open(filename, "rb") as f:
        return (discord.File(f, filename=filename), total)


async def note_pushups(state, message):
    """Modifies the global state"""
    if pushups := parse_pushup(message.content):
        await message.add_reaction("👌")
        at = message.created_at
        state[message.author][at] = pushups
        return (True, state)
    return (False, state)


async def send_current_stats(state, channel):
    (file, total) = plot_pushups(state)
    await channel.send(file=file)
    await channel.send(f"Total: {total}")

@client.event
async def on_ready():
    print("CONNECTED")

@client.event
async def on_message(message):
    """Modifies the global state"""
    global state
    if message.author.bot:
        return

    if "challenge" not in message.channel.name.lower():
        return

    if message.content[0] != token:
        return

    command = message.content[1:]

    if command == "recount":
        async with message.channel.typing():
            state = defaultdict(dict)
            async for message in message.channel.history(limit=200):
                _, state = await note_pushups(state, message)

            await send_current_stats(state, message.channel)
    elif command == "stats":
        await send_current_stats(state, message.channel)
    else:
        contained_pushup, state = await note_pushups(state, message)


with open("discord-token.txt", "r") as f:
    client.run(f.read().strip())
