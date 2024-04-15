import discord
import requests
import ghostGrabber
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    for ghostFile in message.attachments:

        if ghostFile.size < 5000000:
            fileUrl = str(ghostFile)
            r = requests.get(fileUrl)

            if ghostFile.filename[-4:] == '.gci':

                f = open('inputFile', 'wb')
                f.write(r.content)
                f.close()

                if(message.content):
                    ghostGrabber.changeRegion('inputFile', message.content[0].upper())

                newName, output = ghostGrabber.grabGhost('inputFile')
                os.rename('inputFile',newName)

                await message.channel.send(content=output, file=discord.File(newName))
                os.remove(newName)

client.run(os.environ["GGBETA_API_KEY"])
