# TuneCat
Small discord bot used for playing music in discord calls. This can be used to create playlists and play music from Youtube, Spotify, and Soundcloud. This can be used to play music in multiple servers at the same time, but must be self-hosted.

# Setting up your environment
You will need a text file named ```.env``` in the same directory to store your tokens. 
You will need to get tokens for your discord bot at https://discord.com/developers/applications and your spotify app at https://developer.spotify.com/dashboard/applications. 
To get a guest soundcloud token, you will need to get a browser's client_id. This can usually be done by pressing f12 and going to the networking tab, then opening a track on soundcloud.

Your ```.env``` file should include these 4 lines
```
DISCORD_BOT_TOKEN=<YOUR TOKEN HERE>
SPOTIFY_CLIENT_ID=<YOUR TOKEN HERE>
SPOTIFY_CLIENT_SECRET=<YOUR TOKEN HERE>
SOUNDCLOUD_CLIENT_ID=<YOUR TOKEN HERE>
```

# Commands
* ```-play, -p``` 
Loads your input and adds it to the queue. If there is no playing track, then it will start playing. Can also search youtube if given a query

* ```-skip, -s```
Skips to the next track in the queue

* ```-join, -j```
Joins the current user's voice channel, if they are in one

* ```-quit, -leave, -q```
Leaves the current voice channel and clears the queue

* ```-stop```
Stops playback and clears the queue

* ```-pause```
Pauses playback

* ```-resume```
Resumes playback

* ```-loop on, -l on```
Loops the queue

* ```-loop off, -l off```
Stops looping the queue

* ```-shuffle```
shuffles the queue

* ```-print, -display```
displays the currently queued tracks