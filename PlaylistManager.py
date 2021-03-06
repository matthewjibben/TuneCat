import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
import os
import yt_dlp
import asyncio
import itertools
import random
import requests
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sclib.asyncio import SoundcloudAPI, Track
from json import loads
from requests import get
import sys




spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=os.environ['SPOTIFY_CLIENT_ID'],
                                                           client_secret=os.environ['SPOTIFY_CLIENT_SECRET']))

ydl = yt_dlp.YoutubeDL({'dump_single_json': True,
                            'extract_flat' : True})



#
# The purpose of this file is to create playlists filled with audio sources
# each audio source will be a valid url
# the playlists will be created whenever a new url is used with -play command
# spotify playlists and tracks will use the artist id and track name to attempt to find a source on soundcloud/youtube
# playlists can be added together

class SourceError(Exception):
    pass


class HiddenPrints:
    # a tiny class to prevent some nasty functions from printing to stdout
    # use "with HiddenPrints():"
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


# def ytdl_make_url(ytdl_dict):
#     # convert youtube_dl video dictionaries into valid urls
#     # _yt_re = re.compile(r"https?://(.*\.)*youtube\.com/(.*)")
#     # _yt_share_re = re.compile(r"https?://(.*\.)*youtu\.be/(.*)")
#     print("DOING YTDL MAKE ====================")
#     print(ytdl_dict)
#     return f"https://www.youtube.com/watch?v={ytdl_dict['url']}"




soundcloud_guest_client_id = os.environ['SOUNDCLOUD_CLIENT_ID']

with HiddenPrints():
    soundcloud_api = SoundcloudAPI()
    soundcloud_api.client_id = os.environ['SOUNDCLOUD_CLIENT_ID']


def soundcloud_search(query, cid):
    global soundcloud_api
    url = "https://api-v2.soundcloud.com/search?q={query}&client_id={client_id}&limit={limit}&offset={offset}".format(query=query, client_id=cid, limit=10, offset=0)

    while url:
        response = get(url)
        if response.status_code != 200:
            return
        try:
            doc = loads(response.text)
        except:
            return
        for entity in doc['collection']:
            if entity['kind'] == 'track':
                track = Track(obj=entity, client=soundcloud_api)
                yield track

        url = doc.get('next_href')





class Song:
    def __init__(self, url=""):
        self.url = url
        self.title = ""
        self.artist = ""
        self.length = 0 # song length in ms
        self.ytdl_dict = {}


    def __str__(self):
        if not self.title and not self.artist:
            return self.url
        else:
            if not self.artist:
                return self.title
            return self.title + " - " + self.artist

    # use the length of the song and find a video with similar length +/- 1.5 seconds
    # use several different metrics to find the correct track source on youtube/spotify
    # metrics: title similarity, track duration, total play count
    # follow https://github.com/robinfriedli/botify/issues/137
    async def get_url(self):
        if self.url:
            return self.url

        global soundcloud_api # todo maybe check if current credentials are still working

        # search for a song url given a query: usually a song name plus artist name
        query = f"{self.title} - {self.artist}"
        result = soundcloud_search(query, soundcloud_api.client_id)
        close_results = []
        for s in result:
            # print(f"found on soundcloud: {s.title} - {s.artist} - {s.permalink_url} duration: {s.duration} PLAYS: {s.playback_count}")

            # try to get the exact track as quickly as possible
            if s.artist.lower() == self.artist.lower() and s.title.lower() == self.title.lower():
                self.url = s.permalink_url
                return self.url
            else:
                # if we cant find an exact match, attempt to get the best result using the length, title similarity, and view count of the track
                if abs(s.duration - self.length) <= 1500:
                    close_results.append(s)

        # choose the result with the highest number of views
        if len(close_results)>0:
            best_result = max(close_results, key=lambda track: track.playback_count)
            self.url = best_result.permalink_url
            return self.url


        # if a result isnt found on soundcloud, instead search youtube and find the best result there
        yt_search = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
        close_results = []
        # get results where the duration is within 1.5 seconds
        for i, video in enumerate(yt_search):
            if abs((video['duration']*1000)-self.length) <= 1500:
                close_results.append(video)
        # choose the result with the highest number of views
        if len(close_results) > 0:
            best_result = max(close_results, key=lambda track: track['view_count'])
            self.url = best_result['url']
            return self.url






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
        self._soundcloud_re = re.compile(r"https?://(.*\.)*soundcloud.com/(.*)")
        self._soundcloud_set_re = re.compile(r"https?://(.*\.)*soundcloud.com/(.*)/sets/(.*)")
        self._yt_re = re.compile(r"https?://(.*\.)*youtube\.com/(.*)")
        self._yt_share_re = re.compile(r"https?://(.*\.)*youtu\.be/(.*)")




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
            temp.length = song['duration_ms']
            await super().put(temp)

        elif self._spotify_album_re.match(link):
            album = spotify.album(link)
            for song in album['tracks']['items']:
                temp = Song()
                temp.artist = song['artists'][0]['name']
                temp.title = song['name']
                temp.length = song['duration_ms']
                await super().put(temp)

        elif self._spotify_artist_re.match(link):
            artist = spotify.artist_top_tracks(link)
            for song in artist['tracks']:
                temp = Song()
                temp.artist = song['artists'][0]['name']
                temp.title = song['name']
                temp.length = song['duration_ms']
                await super().put(temp)

        elif self._spotify_playlist_re.match(link):
            playlist = spotify.playlist(link)
            for song in playlist['tracks']['items']:
                temp = Song()
                temp.artist = song['track']['artists'][0]['name']
                temp.title = song['track']['name']
                temp.length = song['track']['duration_ms']
                # search_key = song['track']['name'] + "-" + song['track']['artists'][0]['name']
                # print(i, search_key)
                # video_info = ydl.extract_info(f"ytsearch:{search_key}", download=False)['entries'][0]
                # video = Song(ytdl_make_url(video_info))
                # print()
                await super().put(temp)

        else:
            raise SourceError("Invalid link given")

        return

    async def add_soundcloud_songs(self, link):
        if self._soundcloud_set_re.match(link):
            global soundcloud_api
            playlist = await soundcloud_api.resolve(link)
            async for track in playlist:
                print(track.permalink_url)
                await super().put(Song(track.permalink_url))
        else:
            await super().put(Song(link))
        return


    async def add_youtube_songs(self, link):
        with ydl:
            yt_metadata = ydl.extract_info(link, download=False)

        # todo there might be a better way to do this using re to check if its a playlist/mix
        try:
            if yt_metadata['_type'] == 'playlist':
                for track in yt_metadata['entries']:
                    await super().put(Song(track['url']))
            pass
        except:
            await super().put(Song(link))
        return


    async def put_song(self, song):
        await super().put(song)


    async def put(self, item):
        # todo convert item to song
        try:
            # check if a valid url
            requests.get(item)
        except:
            # if not a valid url, search youtube
            video_info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            video = Song(video_info['url'])
            await super().put(video)
        else:
            # if it is a valid url, find an audio source and add to queue
            # verify audio source
            if self._spotify_re.match(item):
                await self.add_spotify_songs(item)
            elif self._soundcloud_re.match(item):
                await self.add_soundcloud_songs(item)
            elif self._yt_re.match(item) or self._yt_share_re.match(item):
                await self.add_youtube_songs(item)
            else:
                raise SourceError("Invalid link given")






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

