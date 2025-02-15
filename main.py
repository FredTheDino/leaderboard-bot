import discord
from collections import defaultdict, Counter
from datetime import timedelta
from random import choice
import matplotlib.pyplot as plt
import re
from difflib import get_close_matches
from typing import (Tuple, List)
import pickle

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

state = defaultdict(dict)

stats_re = re.compile("!stats", re.IGNORECASE)

def sumit(x):
    return sum(x.values())

def unit_dist(amount, suffix):
    # km is default unit
    if suffix == "m":
        amount = amount / 1000
    elif suffix == "km":
        amount = amount
    elif suffix == "mil":
        amount = amount * 10
    return amount

def unit_count(amount, suffix):
    amount = int(amount)
    if suffix == "dussin":
        amount = amount * 12
    elif suffix == "st":
        amount = amount
    elif suffix == "":
        amount = amount
    return amount

def unit_time(amount, suffix):
    # Minutes is the unit of time
    if get_close_matches(suffix, ["s", "sekunder", "sec"], cutoff=0.6):
        amount = amount / 60
    elif get_close_matches(suffix, ["m", "min", "minuter"], cutoff=0.6):
        amount = amount
    elif get_close_matches(suffix, ["h", "time", "hour"], cutoff=0.6):
        amount = amount * 60
    return amount

# '<,'>s/ *\"\([^\"]*\)\": .*, unit_\(.*\), \(\d*\).*/\1: \2 x \3
# körning: dist x 0
# löpning: dist x 100
# promenad: dist x 50
# cyklade: dist x 30
# armhävning: count x 2
# situp: count x 2
# squat: count x 2
# burpee: count x 4
# dans: time x 2
# plankan: time x 10
# klättring: time x 4
# stretching: time x 2
# meditera: time x 1
activities = {
    # "löpning": (["spring", "löpning", "jogga"], unit_dist, 100),
    # "köra": (["köra", "körabil", "bil"], unit_dist, 0),
    # "promenad": (["promenad", "gick", "promenerade"], unit_dist, 50),
    # "cyklade": (["cyklade", "mountain", "bike"], unit_dist, 30),
    "armhävning": (["armhävning", "pushup"], unit_count, 1),
    # "situp": (["situp", "mage"], unit_count, 2),
    # "squat": (["squat"], unit_count, 2),
    # "burpee": (["burpee"], unit_count, 4),
    # "dans": (["lindihop", "dansa", "folkdans"], unit_time, 2),
    # "plankan": (["planka", "planking"], unit_time, 10),
    # "klättring": (["bouldering", "topprep", "klättrade"], unit_time, 4),
    # "stretching": (["stretching", "stretch", "stretchande"], unit_time, 2),
    # "meditera": (["meditera"], unit_time, 1),
}

def find_likely_activity(activity, known):
    aliases = [x for (aliases, _, _) in known.values() for x in aliases]
    best = get_close_matches(activity.lower(), aliases, n=1, cutoff=0.6)
    best = (best or [None])[0]
    for (k, (alises, _, _)) in known.items():
        if best in alises: return k

def parse_message(x):
    global activities
    distance_re = re.compile(r"(\w+)\W{0,2}(-?\d+)(\W{1,2}(\w+))?", re.IGNORECASE)
    total = []
    for (kind, amount, unit, _) in distance_re.findall(x):
        try:    
            amount = float(amount)
        except:
            continue
        likely = find_likely_activity(kind, activities)
        if likely is None: continue
        (_, unit_parse, _) = activities[likely]
        total.append((likely, unit_parse(amount, unit)))
    return total

async def note_distance(state, message):
    """Modifies the global state"""
    new_stats = parse_message(message.content)
    if new_stats:
        emoji = choice(list(emoji for emoji in message.guild.emojis if "lesslie" in emoji.name) + ["👌", "💪", "🏋️", "🦾", "🏅", "⭐", "🚀", "🚩"])
        at = message.created_at
        state[message.author.name][at] = new_stats
        await message.add_reaction(emoji)
        with open('state.pickle', 'wb') as f:
            pickle.dump(state, f)
        return (True, state)
    return (False, state)

def score(known_activites, entries: List[Tuple[str, float]]):
    return Counter({ name: known_activites[name][2] * count for (name, count) in entries })

def summarize(user_data):
    global activities
    all_days = set()
    for data in user_data.values():
        for datetime, entries in data.items():
            all_days.add(datetime.date())

    raw_user_per_day = dict()
    for user, data in user_data.items():
        if user not in raw_user_per_day:
            raw_user_per_day[user] = dict()
            for d in all_days:
                raw_user_per_day[user][d] = Counter()
        for datetime, entries in data.items():
            raw_user_per_day[user][datetime.date()] += score(activities, entries)

    total_per_day = { d: sum(sumit(u[d]) for u in raw_user_per_day.values()) for d in all_days }
    
    total = int(sum(total_per_day.values()))
    user_per_day = { u: { d: sumit(i) for (d, i) in v.items() } for (u, v) in raw_user_per_day.items() }

    fix, (ax, bx) = plt.subplots(2, 1)
    for user, data in user_per_day.items():
        label = user
        xy = sorted(data.items())
        x = list(map(lambda x:x[0], xy))
        y = list(map(lambda x:x[1], xy))
        ax.plot(x, y, label=label, marker='o')
    ax.legend()
    ax.set(xticklabels=[])
    ax.set(title="pushups per day per person")
    ax.set(xlabel=None)
    ax.set_ylim(ymin=0)

    xy = sorted(total_per_day.items())
    x = list(map(lambda x:x[0], xy))
    y = list(map(lambda x:x[1], xy))
    bx.plot(x, y, label="total", marker='o')
    bx.legend()
    bx.set(xticklabels=[])
    bx.set(title="Total pushups per day")
    ax.set(xlabel=None)
    bx.set_ylim(ymin=0)

    fix.tight_layout()
    fix.set_figwidth(10)
    fix.set_figwidth(10)
    filename = "pushups.png"
    fix.savefig(filename)
    with open(filename, "rb") as f:
        return (discord.File(f, filename=filename), total, user_per_day)




async def send_current_stats(state, channel):
    (file, total, user_per_day) = summarize(state)
    await channel.send(file=file)
    best = "\n".join([ f"{u}: {sum(l.values())}" for u, l in user_per_day.items() ])
    await channel.send(f"Total pushups: {total}\n==== LEADERBOARD ===\n{best}")

@client.event
async def on_ready():
    global state
    try:
        with open('state.pickle', 'rb') as f:
            state = defaultdict(dict, **pickle.load(f))
    except:
        pass
    print("LOADED")

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

if __name__ == "__main__":
    with open("discord-token.txt", "r") as f:
        client.run(f.read().strip())
