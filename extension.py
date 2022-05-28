from enum import Enum
from typing import Union

import requests
import spotipy
import urllib3
from spotipy import SpotifyClientCredentials

from maytry import Api, MaytryBot


class ApexPlatform(Enum):
    ORIGIN = "PC"
    PS4 = "PS4"
    XBOX = "X1"


class ApexType(Enum):
    PLAYER = 'player'
    MAP = 'map'
    CRAFTING = 'crafting'


class ApexApi(Api):
    _maytry: MaytryBot
    _token: str

    def __init__(self, maytry: MaytryBot):
        super().__init__('apex')
        self._maytry = maytry
        self._token = maytry.get_api_token(self)

    def request(self, api_token: str = None, **kwargs) -> dict:
        """
        type: player, map, crafting
        platform: only required when type is player
        player: only required when type is player

        You can find the content format right here: https://apexlegendsapi.com

        ATTENTION: the api has a limit, you can only send 1 request in 2 seconds

        :param api_token: token
        :param kwargs: type is required
        :return:
        """
        if api_token is None: api_token = self._token
        if 'api_token' in kwargs: api_token = kwargs['api_token']
        if 'type' in kwargs:
            type = kwargs['type']
            if isinstance(type, str):
                type = type.lower()
                if type == 'player':
                    if 'platform' in kwargs:
                        platform = kwargs['platform']
                        if isinstance(platform, ApexPlatform):
                            platform = platform.lower()
                            if 'player' in kwargs:
                                player = kwargs['player']
                                if isinstance(player, str):
                                    urllib3.disable_warnings()
                                    headers = {"Content-Type": "application/json"}
                                    request = requests.get(
                                        "https://api.mozambiquehe.re/bridge?version=5&platform="
                                        + platform + "&player=" + player + "&auth=" + api_token,
                                        headers=headers, verify=False, proxies={"http": None, "https": None})
                                    if request.status_code == 200:
                                        return {'code': 0, 'message': 'Success',
                                                'data': {'type': 0, 'content': request.json()}}
                                    else:
                                        return {'code': -4, 'message': request.content}
                                else:
                                    return {'code': -3, 'message': 'Player name should be a str'}
                            return {'code': -2, 'message': 'Type "player" -> "platform" need set "player'}
                        else:
                            return {'code': -2, 'message': 'Platform should be an ApexPlatform object'}
                    else:
                        return {'code': -2, 'message': 'Type "player" need set "platform"'}
                elif type == 'map':
                    urllib3.disable_warnings()
                    headers = {"Content-Type": "application/json"}
                    request = requests.get(
                        "https://api.mozambiquehe.re/maprotation?version=2&auth=" + api_token,
                        headers=headers, verify=False, proxies={"http": None, "https": None})
                    if request.status_code == 200:
                        return {'code': 0, 'message': 'Success', 'data': {'type': 0, 'content': request.json()}}
                    else:
                        return {'code': -4, 'message': request.content}
                elif type == 'crafting':
                    urllib3.disable_warnings()
                    headers = {"Content-Type": "application/json"}
                    request = requests.get(
                        "https://api.mozambiquehe.re/crafting?auth=" + api_token,
                        headers=headers, verify=False,
                        proxies={"http": None, "https": None})
                    if request.status_code == 200:
                        return {'code': 0, 'message': 'Success', 'data': {'type': 0, 'content': request.json()}}
                    else:
                        return {'code': -4, 'message': request.content}
                else:
                    return {'code': -1, 'message': 'Unknown type'}
            else:
                return {'code': -1, 'message': 'Type should be a str'}
        else:
            return {'code': -1, 'message': 'Didn\'t define the type'}


class SpotifyType(Enum):
    SEARCH_SONG = 'search_song'
    SEARCH_ARTIST = 'search_artist'
    SEARCH_ALBUM = 'search_album'


class SpotifyApi(Api):
    """
    In the config file:
    {
        "khl_token": "Your kaiheila bot token",
        "api_tokens": {
            "apex": "Your apex api token",
            "spotify": "client_id|client_secret"
        }
    }
    """
    _maytry: MaytryBot
    _token: str

    def __init__(self, maytry: MaytryBot):
        super().__init__('spotify')
        self._maytry = maytry
        self._token = maytry.get_api_token(self)

    def request(self, **kwargs) -> dict:
        """
        type: search_song, search_artist, search_album
        song: only need when search_song
        artist: only need when search_artist
        album: only need when search_album
        """
        api_token = self._token
        if 'api_token' in kwargs:
            api_token = kwargs['api_token']
        if 'type' in kwargs:
            type = kwargs['type']
            if isinstance(type, SpotifyType):
                type = type.value
            if isinstance(type, str):
                type = type.lower()
                if type == 'search_song':
                    if 'song' in kwargs:
                        song = kwargs['song']
                        if isinstance(type, str):
                            divided_token = api_token.split('|')
                            spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=divided_token[0], client_secret=divided_token[1]))
                            response = spotify.search(q=f'track:{song}')
                            return {'code': 0, 'message': 'Success', 'data': {'type': 0, 'content': response}}
                        else:
                            return {'code': -3, 'message': 'Song should be a str'}
                    else:
                        return {'code': -3, 'message': 'Didn\'t define the song'}
                elif type == 'search_artist':
                    if 'artist' in kwargs:
                        artist = kwargs['artist']
                        if isinstance(type, str):
                            divided_token = api_token.split('|')
                            spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=divided_token[0], client_secret=divided_token[1]))
                            response = spotify.search(q=f'artist:{artist}', type='artist')
                            return {'code': 0, 'message': 'Success', 'data': {'type': 0, 'content': response}}
                        else:
                            return {'code': -3, 'message': 'Artist should be a str'}
                    else:
                        return {'code': -3, 'message': 'Didn\'t define the artist'}
                elif type == 'search_album':
                    if 'album' in kwargs:
                        album = kwargs['album']
                        if isinstance(type, str):
                            divided_token = api_token.split('|')
                            spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=divided_token[0], client_secret=divided_token[1]))
                            response = spotify.search(q=f'album:{album}', type='album')
                            return {'code': 0, 'message': 'Success', 'data': {'type': 0, 'content': response}}
                        else:
                            return {'code': -3, 'message': 'Album should be a str'}
                    else:
                        return {'code': -3, 'message': 'Didn\'t define the album'}
                else:
                    return {'code': -2, 'message': 'Unknown type'}
            else:
                return {'code': -1, 'message': 'Type should be a str'}
        else:
            return {'code': -1, 'message': 'Didn\'t define the type'}