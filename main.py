import discord
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import timedelta
from itertools import chain
from random import choice
import re

client = discord.Client()

token = "!"

state = defaultdict(dict)

stats_re = re.compile("!stats", re.IGNORECASE)

def find_distance(x):
    distance_re = re.compile("(\d+(?:\.\d+)?).{0,2}(mil|km)", re.IGNORECASE)
    total = None
    for (d, unit) in distance_re.findall(x):
        try:    
            d = float(d)
            match unit:
                case "mil":
                    d = d * 10
                case "km":
                    d = d
            total = 0 if total is None else total
            total += d
        except:
            pass
    return total


def plot_pushups(pushups_users_dates):
    total_per_day = defaultdict(int)
    for data in pushups_users_dates.values():
        for datetime, number in data.items():
            total_per_day[datetime] += number

    user_per_day = defaultdict(lambda: defaultdict(int))
    for user, data in pushups_users_dates.items():
        for d in total_per_day.keys():
            user_per_day[user][d] = 0
        for datetime, number in data.items():
            user_per_day[user][datetime] += number

    total = sum(total_per_day.values())

    fix, (ax, bx) = plt.subplots(2, 1)
    for user, data in user_per_day.items():
        label = user.name
        xy = sorted(data.items())
        x = list(map(lambda x:x[0], xy))
        y = list(map(lambda x:x[1], xy))
        ax.plot(x, y, label=label, marker='o')
    ax.legend()
    ax.set(xticklabels=[])
    ax.set(title="km per day per person")
    ax.set(xlabel=None)
    ax.set_ylim(ymin=0)

    xy = sorted(total_per_day.items())
    x = list(map(lambda x:x[0], xy))
    y = list(map(lambda x:x[1], xy))
    bx.plot(x, y, label="total", marker='o')
    bx.legend()
    bx.set(xticklabels=[])
    bx.set(title="Total distance traveled per day")
    ax.set(xlabel=None)
    bx.set_ylim(ymin=0)

    fix.tight_layout()
    fix.set_figwidth(10)
    fix.set_figwidth(10)
    filename = "distance.png"
    fix.savefig(filename)
    with open(filename, "rb") as f:
        return (discord.File(f, filename=filename), total)


async def note_distance(state, message):
    """Modifies the global state"""
    if distance := find_distance(message.content):
        emoji = choice(list(emoji for emoji in message.guild.emojis if emoji.name == "lesslie") or ["👌", "🔫", "🚩"])
        at = message.created_at.date()
        state[message.author][at] = distance
        await message.add_reaction(emoji)
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

    channel_name = message.channel.name.lower()
    if "workout" not in channel_name and "💪" not in channel_name: return

    _, state = await note_distance(state, message)
    if stats_re.search(message.content):
        await send_current_stats(state, message.channel)

with open("discord-token.txt", "r") as f:
    client.run(f.read().strip())
