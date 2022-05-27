from enum import Enum

import requests
import urllib3

from maytry import Api


class ApexPlatform(Enum):
    ORIGIN = "PC"
    PS4 = "PS4"
    XBOX = "X1"


class ApexApi(Api):

    def __init__(self):
        super().__init__('apex')

    def request(self, api_token: str, **kwargs) -> dict:
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
                                        return {'code': 0, 'message': 'Success', 'data': {'type': 0, 'content': request.json()}}
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

