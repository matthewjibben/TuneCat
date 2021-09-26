import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
import os
import youtube_dl
import asyncio
import itertools
import random
bot = commands.Bot(command_prefix='-')


class VoiceError(Exception):
    pass


# VoiceStates store useful server-specific information like the song queue, if it is set to loop, etc.
# Using a single VoiceState for each server allows the bot to work in multiple servers
class VoiceState:
    def __init__(self, bot, ctx):
        self.current_song = None
        self.voice = None
        self.ctx = ctx
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    @property
    def player(self):
        return self.current_song.player

    def skip(self):
        if self.ctx.voice_client.is_playing():
            pass # todo actually implement skip

    def toggle_next(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    # main async task
    # play the next song in the queue until there are no more songs to play
    async def audio_player_task(self):
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn -bufsize 64k'}

        ydl_opts = {
            'format': 'bestaudio/best',
            'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
        }



        while True:
            print("audio p[layer task==============================")
            self.play_next_song.clear()
            self.current_song = await self.songs.get()
            # self.current_song.player.start()
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.current_song, download=False)
                URL = info['formats'][0]['url']
                title = info['title']
            await self.ctx.send('Now playing: ' + str(title)) # todo make this a discord.embed
            self.ctx.voice_client.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), after=self.toggle_next)
            await self.play_next_song.wait()




# class Song:
#     def __init__(self, url):
#         self.url = url
#         self.name = "name"
#
#     def create_embed(self):
#         embed = (discord.Embed(title='Now playing', description='```css\n{0.source.title}\n```'.format(self),
#                                color=discord.Color.blurple())
#                  .add_field(name='Duration', value=self.source.duration)
#                  .add_field(name='Requested by', value=self.requester.mention)
#                  .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
#                  .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
#                  .set_thumbnail(url=self.source.thumbnail)
#                  .set_author(name=self.requester.name, icon_url=self.requester.avatar_url))
#         return embed





@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

class MusicPlayer(commands.Cog):
    # use self.voice_states to enable usage in multiple servers
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        print("voice state get: id:{}, {}".format(ctx.guild.id, state))
        print(self.voice_states)
        # update the VoiceState's current ctx
        state.ctx = ctx
        return state



    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))


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

    @commands.command(aliases=['s'])
    async def stop(self, ctx):
        ctx.voice_client.stop()

    @commands.command(aliases=[])
    async def pause(self, ctx):
        ctx.voice_client.pause()

    @commands.command(aliases=['unpause'])
    async def resume(self, ctx):
        ctx.voice_client.resume()


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
        # todo -play another song should add to queue
        # todo -skip
        # todo if alone in a call, leave
        # todo loop, repeat
        if len(args)==0: # and ctx.voice_client.is_paused:
            return ctx.voice_client.resume()


        state = self.get_voice_state(ctx)

        if not ctx.voice_client:
            await self.join(ctx)

        await ctx.voice_state.songs.put(args[0])
        await ctx.send('Enqueued {}'.format(str(args[0])))

        if not ctx.voice_client.is_playing:
            state.toggle_next()

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
