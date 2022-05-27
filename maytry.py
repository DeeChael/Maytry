import asyncio
import json
from abc import ABC
from typing import Union, IO

from khl import Bot, Guild, User
from khl.command import Command


class Api(ABC):
    _name: str

    def __init__(self, name: str):
        self._name = name

    def get_name(self) -> str:
        return self._name

    def request(self, api_token: str, **kwargs) -> dict:
        """
        response template:
        {
            "code": 0,  # 0 means success
            "message": "Message returned",
            "data": {
                "type": 0,  # the type of the content: 0 - json object, 1 - json array, 2 - str, 3 - number, 4 - bool, 5 - null
                "content": { # this is a json object
                    ...  # Made by yourself!
                }
            }
        }

        :param api_token: The token which is needed by the api
        :param kwargs: all you need
        :return: response
        """
        pass


class Febtry(ABC):

    def get_api_token(self, api_id: Union[str, Api]) -> str:
        pass


class ApiManager:

    _febtry: Febtry
    _registered: dict[str, Api] = dict()

    def __init__(self, febtry: Febtry):
        self._febtry = febtry
        ...

    def register_api(self, api: Api):
        if api is not None and api.get_name() not in self._registered:
            self._registered[api.get_name()] = api

    def request(self, api: Union[str, Api], **kwargs) -> dict:
        if isinstance(api, Api):
            api = api.get_name()
        if api in self._registered:
            return self._registered[api].request(api_token=self._febtry.get_api_token(api), **kwargs)


class Maytry(Febtry):
    _config: dict = dict()
    _bot: Bot
    _api_manager: ApiManager

    def __init__(self, config_file: Union[IO, str]):
        if isinstance(config_file, str):
            config_file = open(config_file, 'r')
        self._config = json.loads(config_file.read())
        if 'khl_token' in self._config:
            _bot = Bot(token=self._config['khl_token'])
        self._api_manager = ApiManager(self)
        config_file.close()

    def run(self):
        self._bot.run()

    def get_api_token(self, api_id: Union[str, Api]) -> str:
        if isinstance(api_id, Api):
            api_id = api_id.get_name()
        if 'api_tokens' in self._config:
            if api_id in self._config['api_tokens']:
                return self._config['api_tokens'][api_id]
        return ''

    def get_api_manager(self):
        return self._api_manager

    def get_bot(self) -> Bot:
        return self._bot

    def register_command(self, command: Command):
        self._bot.command.add(command)

    def is_op(self, guild: Guild, user: User) -> bool:
        return asyncio.get_event_loop().run_until_complete(self._is_op(guild, user))

    async def _is_op(self, guild: Guild, user: User) -> bool:
        if guild.master_id == user.id:
            return True
        roles = user.roles
        if len(roles) == 0:
            return False
        else:
            guild_roles = await guild.fetch_roles()
            guild_role_ids = dict()
            for guild_role in guild_roles:
                guild_role_ids[str(guild_role.id)] = guild_role
            for role in roles:
                if str(role) in guild_role_ids:
                    guild_role = guild_role_ids[str(role)]
                    if guild_role.permissions & (1 << 0) == (1 << 0):
                        return True
            return False



