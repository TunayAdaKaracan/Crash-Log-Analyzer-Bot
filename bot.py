import discord
import aiohttp
import yaml

API_URL = "https://api.mclo.gs/1/"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Bot(intents=intents)


def hextofloats(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))  # skip '#'


with open("config.yml", "r", encoding="utf-8") as f:
    settings = yaml.safe_load(f)


@client.event
async def on_message(message: discord.Message):
    if message.attachments and message.attachments[0].filename.endswith(".log") and (len(settings["channels"]) == 0 or (len(settings["channels"]) != 0 and message.channel.id in settings["channels"])):

        log_file: discord.Attachment = message.attachments[0]
        content = await log_file.read()

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL + "log", data={"content": content.decode("utf-8")}) as response:
                id = (await response.json())["id"]
                print(f"New log with id of {id}")
                async with session.post(API_URL + "insights/" + id) as response:
                    jsn = await response.json()
                    clr = hextofloats(settings["embed-color"])
                    embed = discord.Embed(colour=discord.Colour.from_rgb(clr[0], clr[1], clr[2]))
                    embed.title = str(jsn["title"] + f" ({len(jsn['analysis']['problems'])} Problem Found)")
                    embed.description = "`Name`: " + str(jsn["name"])
                    embed.description += "\n`Type`: " + str(jsn["type"])
                    embed.description += "\n`Version`: " + str(jsn["version"])
                    if len(jsn["analysis"]["problems"]) == 0:
                        embed.add_field(name="No Error Found", value="Everything is working fine.")
                    for problem in jsn["analysis"]["problems"]:
                        solution = "`Available Solutions:`\n"
                        for solution_ in problem["solutions"]:
                            solution += "`●` " + solution_["message"] + "\n"
                        solution = solution[:-1]
                        embed.add_field(name=problem["message"], value=solution)
                    await message.channel.send(embed=embed)


@client.event
async def on_ready():
    print("Bot is ready")
    await client.change_presence(activity=discord.Game(name=settings["activity"]))

client.run(settings["bot-token"])
