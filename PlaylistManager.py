import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
import os
import youtube_dl
import asyncio
import itertools
import random
import requests
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                                                           client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')))

ydl = youtube_dl.YoutubeDL({'dump_single_json': True,
                            'extract_flat' : True})



#
# The purpose of this file is to create playlists filled with audio sources
# each audio source will be a valid url
# the playlists will be created whenever a new url is used with -play command
# spotify playlists and tracks will use the artist id and track name to attempt to find a source on soundcloud/youtube
# playlists can be added together

class SourceError(Exception):
    pass






def ytdl_make_url(ytdl_dict):
    # convert youtube_dl video dictionaries into valid urls
    return f"https://www.youtube.com/watch?v={ytdl_dict['url']}"



class Song:
    def __init__(self, url=""):
        self.url = url
        self.title = ""
        self.artist = ""
        self.ytdl_dict = {}


    def __str__(self):
        return "url: " + self.url

    # def create_embed(self):
    #     embed = (discord.Embed(title='Now playing', description='```css\n{0.source.title}\n```'.format(self),
    #                            color=discord.Color.blurple())
    #              .add_field(name='Duration', value=self.source.duration)
    #              .add_field(name='Requested by', value=self.requester.mention)
    #              .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
    #              .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
    #              .set_thumbnail(url=self.source.thumbnail)
    #              .set_author(name=self.requester.name, icon_url=self.requester.avatar_url))
    #     return embed


class Playlist(asyncio.Queue):
    def __init__(self):
        super().__init__()
        self._spotify_re = re.compile(r"https?://(.*\.)*spotify.com/(.*)")
        self._spotify_track_re = re.compile(r"https?://(.*\.)*spotify.com/tracks?/(.*)")
        self._spotify_album_re = re.compile(r"https?://(.*\.)*spotify.com/albums?/(.*)")
        self._spotify_artist_re = re.compile(r"https?://(.*\.)*spotify.com/artists?/(.*)")
        self._spotify_playlist_re = re.compile(r"https?://(.*\.)*spotify.com/playlists?/(.*)")


    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

    async def add_spotify_songs(self, link):
        # given a spotify link, add the song/songs
        # todo it is necessary to add all songs as just title and artist, and find each song before playing
        # otherwise, it will take too long to find all the sources and slow down the bot
        if self._spotify_track_re.match(link):
            song = spotify.track(link)
            temp = Song()
            temp.artist = song['artists'][0]['name']
            temp.title = song['name']
            await super().put(temp)

        elif self._spotify_album_re.match(link):
            album = spotify.album(link)
            for song in album['tracks']['items']:
                temp = Song()
                temp.artist = song['artists'][0]['name']
                temp.title = song['name']
                await super().put(temp)

        elif self._spotify_artist_re.match(link):
            artist = spotify.artist_top_tracks(link)
            for song in artist['tracks']:
                temp = Song()
                temp.artist = song['artists'][0]['name']
                temp.title = song['name']
                await super().put(temp)

        elif self._spotify_playlist_re.match(link):
            playlist = spotify.playlist(link)
            for song in playlist['tracks']['items']:
                temp = Song()
                temp.artist = song['track']['artists'][0]['name']
                temp.title = song['track']['name']
                # search_key = song['track']['name'] + "-" + song['track']['artists'][0]['name']
                # print(i, search_key)
                # video_info = ydl.extract_info(f"ytsearch:{search_key}", download=False)['entries'][0]
                # video = Song(ytdl_make_url(video_info))
                # print()
                await super().put(temp)

        else:
            raise SourceError("Invalid link given")

        return


    async def put(self, item):
        # todo convert item to song
        try:
            # check if a valid url
            requests.get(item)
        except:
            # if not a valid url, search youtube
            video_info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            video = Song(ytdl_make_url(video_info))
            await super().put(video)
        else:
            # if it is a valid url, find an audio source and add to queue
            # check if it is a spotify
            if self._spotify_re.match(item):
                print("this is a spotify ==============================")
                await self.add_spotify_songs(item)
            else:
                await super().put(Song(item))





async def main():
    p = Playlist()
    await p.put("asdf1")
    await p.put("asdf2")
    await p.put("asdf3")
    await p.put("asdf4")
    await p.put("asdf5")
    await p.put("asdf6")
    await p.put("asdf7")
    await p.put("asdf8")
    await p.put("https://www.youtube.com/watch?v=yQ0iTDafXuM")


    # p.shuffle()

    for i in p:
        print(i)
    print("done done")

if __name__ == "__main__":
    asyncio.run(main())

