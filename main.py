import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
import os
import youtube_dl
import asyncio

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)





bot = commands.Bot(command_prefix='-')
# client = discord.Client()


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

class MusicPlayer(commands.Cog):
    # use self.voice_states to enable usage in multiple servers
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    # def get_voice_state(self, server):
    #     state = self.voice_states.get(server.id)
    #     if state is None:
    #         state = VoiceState(self.bot)
    #         self.voice_states[server.id] = state
    #
    #     return state






    @commands.command(aliases=['j'])
    async def join(self, ctx):
        await ctx.send('joining...')

        channel = ctx.message.author.voice.channel
        return await channel.connect()


    @commands.command(aliases=['leave', 'l', 'q'])
    async def quit(self, ctx):
        # print(bot.voice_clients)
        if len(bot.voice_clients)>0:
            await ctx.voice_client.disconnect()


    # @commands.command(aliases=[])
    # async def summon(self, ctx):
    #     # summons bot to current users channel
    #     summoned_channel = ctx.message.author.voice_channel
    #     if summoned_channel is None:
    #         await ctx.send('You are not in a voice channel')
    #         return False

    @commands.command(aliases=['p'])
    async def play(self, ctx, *args):
        # todo cannot play music while currently in a vc
        # todo player occasionally cuts out
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn -bufsize 64k'}
        vc = await self.join(ctx)

        ydl_opts = {'format': 'bestaudio'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(args[0], download=False)
            URL = info['formats'][0]['url']
        vc.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))

        return







# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return
#
#     if message.content.startswith('-hello'):
#         await message.channel.send('Hello!')
#
#
#     if message.content.startswith(("-join", "-j")):
#         await message.channel.send('joining...')
#
#         channel = message.author.voice.channel
#         await channel.connect()
#
#         pass
#
#
#     if message.content.startswith(("-quit", "-leave", "-l", "-q")):
#         print(client.voice_clients)
#         if len(client.voice_clients)>0:
#             await client.voice_clients[0].disconnect()
#
#         pass





# client.run(os.getenv('TOKEN'))
bot.add_cog(MusicPlayer(bot))
bot.run(os.getenv('TOKEN'))
