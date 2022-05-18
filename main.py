import discord
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import timedelta

client = discord.Client()


def maybe_int(x):
    try:
        return int(x)
    except:
        return None

def accumulate(it):
    s = 0
    for i in it:
        s += i
        yield s

def plot_pushups(pushups_users_dates):
    fix, (ax, bx) = plt.subplots(2, 1)
    for user, data in pushups_users_dates.items():
        ax.plot(
            list(data.keys()), list(data.values()), label=user.nick or user.name
        )
        bx.plot(
            list(data.keys()), list(accumulate(data.values())), label=user.nick or user.name
        )
    ax.legend()
    bx.legend()
    fix.tight_layout()
    filename = "pushups.png"
    fix.savefig(filename)
    with open(filename, "rb") as f:
        return discord.File(f, filename=filename)

state = defaultdict(dict)

def note_pushups(message):
    """Modifies the global state"""
    global state
    for pushups in list(
        filter(lambda x: type(x) == type(1), map(maybe_int, message.content.split()))
    ):
        if message.author == client.user:
            continue

        date = message.created_at.date()
        for x in range(5, 10):
            state[message.author][date + timedelta(days=x)] = pushups + x**2
        return True
    return False


@client.event
async def on_message(message):
    """Modifies the global state"""
    global state
    if message.author == client.user:
        return

    if message.content.startswith("refresh"):
        async with message.channel.typing():
            await message.channel.send('Re-reading all history!')
            state = {}
            async for message in message.channel.history(limit=200):
                note_pushups(message)
    else:
        if note_pushups(message):
            await message.channel.send(file=plot_pushups(state))

with open("discord-token.txt", "r") as f:
    client.run(f.read().strip())
