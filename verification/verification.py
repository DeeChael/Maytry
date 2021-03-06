import random
import time
from typing import Union

import bilibili_api
from bilibili_api import user
from khl import User, Guild, Channel, PublicChannel, MessageTypes
from khl.card import CardMessage, Card, Module, Element, Types

from configuration import Configuration, SimpleConfiguration, JsonConfiguration, YamlConfiguration
from maytry import MaytryBot


class VerificationManager:
    _maytry: MaytryBot
    _verified_users: Configuration
    _configuration: Configuration
    _cache: Configuration

    _code_cache: dict = dict()

    def __init__(self, maytry: MaytryBot):
        self._maytry = maytry
        self._verified_users = SimpleConfiguration('verified.cache')
        self._configuration = YamlConfiguration('verification-settings.yml')
        self._cache = JsonConfiguration('verification-cache.json')
        if self._cache.contains("servers"):
            for key in self._cache.get("servers").keys():
                self._code_cache[key] = dict()

    def is_channel_visible_before_verify(self, guild: Guild, channel: Channel):
        if self.is_initialized(guild):
            return channel.id in self._cache.get(f'servers*{guild.id}*before_visible')
        return False

    async def modify_visible_before_verify(self, guild: Guild, channel: Channel, visible: bool) -> bool:
        everyone_role = ...
        for role in await guild.fetch_roles():
            if role.id == 0:
                everyone_role = role
        if everyone_role is None:
            return False
        if visible:
            if not self.is_channel_visible_before_verify(guild, channel):
                self._cache.get(f'servers*{guild.id}*before_visible').append(channel.id)
                self._cache.save()
                await channel.update_permission(everyone_role, allow=2048)
                return True
        else:
            if self.is_channel_visible_before_verify(guild, channel):
                self._cache.get(f'servers*{guild.id}*before_visible').remove(channel.id)
                self._cache.save()
                await channel.update_permission(everyone_role, deny=2048)
                return True
        return False

    def is_channel_invisible_after_verify(self, guild: Guild, channel: Channel):
        if self.is_initialized(guild):
            return channel.id in self._cache.get(f'servers*{guild.id}*after_invisible')
        return False

    async def modify_invisible_after_verify(self, guild: Guild, channel: Channel, visible: bool) -> bool:
        member_role = await self.get_member_role(guild)
        if visible:
            if self.is_channel_invisible_after_verify(guild, channel):
                await channel.update_permission(member_role, allow=2048)
                self._cache.get(f'servers*{guild.id}*after_invisible').remove(channel.id)
                self._cache.save()
                return True
        else:
            if not self.is_channel_invisible_after_verify(guild, channel):
                self._cache.get(f'servers*{guild.id}*after_invisible').append(channel.id)
                self._cache.save()
                await channel.update_permission(member_role, deny=2048)
                return True
        return False

    async def add_verified_user(self, guild: Guild, user: User, uid: Union[str, int]):
        if not self._verified_users.contains(user.id):
            self._verified_users.set(f'{user.id}', uid)
            self._verified_users.save()
        self._cache.get(f'servers*{guild.id}*verified').append(user.id)
        self._cache.save()
        await guild.grant_role(user, self.get_member_role(guild))
        if user.id in self._code_cache[guild.id]:
            self._code_cache[guild.id].pop(user.id)

    def get_member_role(self, guild: Guild):
        return self._cache.get(f'servers*{guild.id}*member_role')

    async def get_log_channel(self, guild: Guild):
        guild_id = guild.id
        if not self._cache.contains(f'servers*{guild_id}'):
            return None
        channel_in_config = self._cache.get(f'servers*{guild_id}*log_channel')
        for channel in await guild.fetch_channel_list():
            if channel.id == channel_in_config:
                return channel
        return None

    def set_log_channel(self, guild: Guild, channel: Channel):
        self._cache.set(f'servers*{guild.id}*log_channel', channel.id)
        self._cache.save()

    def is_initialized(self, guild: Guild) -> bool:
        return self._cache.contains(f'servers*{guild.id}')

    async def get_verifying_channel(self, guild: Guild) -> PublicChannel:
        for channel in await guild.fetch_channel_list():
            if channel.id == self._cache.get(f'servers*{guild.id}*verifying_channel'):
                return channel

    async def init_server(self, guild: Guild, verifying_channel: Union[Channel, PublicChannel]) -> bool:
        guild_id = guild.id
        if self._cache.contains(f'servers*{guild_id}'):
            return False
        everyone_role = ...
        for role in await guild.fetch_roles():
            if role.id == 0:
                everyone_role = role
        if everyone_role is None:
            return False
        member_role = await guild.create_role('??????')
        everyone_original_permissions = everyone_role.permissions
        everyone_role.permissions = 0
        member_role.permissions = 2048 | 4096 | 32768 | 262144 | 524288 | 4194304 | 8388608
        member_role.color = '#ffffff'
        await guild.update_role(everyone_role)
        time.sleep(0.1)
        await guild.update_role(member_role)
        time.sleep(0.1)
        for channel in await guild.fetch_channel_list():
            for permission in (await channel.fetch_permission()).overwrites:
                if permission.role_id == 0:
                    self._cache.set(f'servers*{guild_id}*everyone_original_permissions*channels*{channel.id}*allow',
                                    permission.allow)
                    self._cache.set(f'servers*{guild_id}*everyone_original_permissions*channels*{channel.id}*deny',
                                    permission.deny)

            await channel.update_permission(everyone_role, deny=2048)
            time.sleep(0.1)
            await channel.update_permission(member_role, allow=2048)
            time.sleep(0.1)
        await verifying_channel.update_permission(everyone_role, allow=2048 | 4096)
        time.sleep(0.1)
        await verifying_channel.update_permission(member_role, deny=2048)
        self._cache.set(f'servers*{guild_id}*verifying_channel', verifying_channel.id)
        self._cache.set(f'servers*{guild_id}*member_role', member_role.id)
        self._cache.set(f'servers*{guild_id}*everyone_original_permissions*guild', everyone_original_permissions)
        self._cache.set(f'servers*{guild_id}*before_visible', list())
        self._cache.set(f'servers*{guild_id}*after_invisible', list())
        self._cache.set(f'servers*{guild_id}*verified', list())
        self._code_cache[guild_id] = dict()
        self._cache.save()
        length = len(f"BilibiliLinker-{guild_id}-XXXXXXXXXX-XXXXXX")
        if length % 2 == 1:
            length += 1
        await self._maytry.get_bot().send(verifying_channel, f'---\n'
                                                             f'(met)all(met)\n'
                                                             f'???????????? {guild.name} ????????????????????????????????????????????????\n'
                                                             f'1.?????? ???.verify generate??? ??????????????????????????????\n'
                                                             f'2.??????https://www.bilibili.com\n'
                                                             f'3.????????????bilibili??????\n'
                                                             f'4.??????????????????????????????"BilibiliLinker-{guild_id}-???????????????-XXXXXX", XXXXXX??????????????????????????????????????????????????????B??????????????????????????????????????? {int(length / 2)} ?????????\n'
                                                             f'5.?????????????????????".verify verify <??????bilibili??????uid>"?????????<>???????????????\n'
                                                             f'??????????????????????????????????????????10????????????\n'
                                                             f'---', type=MessageTypes.KMD)
        return True

    async def reset_server(self, guild: Guild) -> bool:
        guild_id = guild.id
        if not self._cache.contains(f'servers*{guild_id}'):
            return False
        everyone_role = ...
        for role in await guild.fetch_roles():
            if role.id == 0:
                everyone_role = role
        if everyone_role is None:
            return False
        await guild.delete_role(self._cache.get(f'servers*{guild_id}*member_role'))
        for channel in await guild.fetch_channel_list():
            if not self._cache.contains(f'servers*{guild_id}*everyone_original_permissions*channels*{channel.id}'):
                continue
            allow = self._cache.get(f'servers*{guild_id}*everyone_original_permissions*channels*{channel.id}*allow')
            deny = self._cache.get(f'servers*{guild_id}*everyone_original_permissions*channels*{channel.id}*deny')
            await channel.update_permission(everyone_role, allow=allow, deny=deny)
            time.sleep(0.1)
        everyone_role.permissions = self._cache.get(f'servers*{guild_id}*everyone_original_permissions*guild')
        await guild.update_role(everyone_role)
        self._cache.remove(f'servers*{guild_id}')
        self._cache.save()
        return True

    def generate_code(self, guild: Guild, user: User):
        verify_code_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        verify_code_chars_index = len(verify_code_chars)
        verify_code = ''
        for i in range(6):
            verify_code += verify_code_chars[random.randint(0, verify_code_chars_index)]
        new_dict = dict()
        new_dict['code'] = verify_code
        new_dict['timestamp'] = int(time.time())
        self._code_cache[guild.id][user.id] = new_dict
        return verify_code

    async def verify(self, guild: Guild, user: User, uid: int) -> int:
        if user.id in self._code_cache[guild.id]:
            if self._verified_users.contains(user.id):
                await self.sync_user(guild, user)
                return 1
            else:
                if user.id not in self._cache.get(f'servers*{guild.id}*verified'):
                    bili_user = bilibili_api.user.User(uid=int(uid))
                    response = await bili_user.get_dynamics()
                    if 'cards' in response:
                        cards = response['cards']
                        found = False
                        for i in range(max(max(len(cards), 5) - 1, 1)):
                            card = cards[min(i, len(cards) - 1)]['card']
                            if 'item' in card:
                                item = card['item']
                                if time.time() - cards[i]['desc']['timestamp'] < 10 * 60:
                                    message = item['content']
                                    if message == f'BilibiliLinker-{guild.id}-???????????????-' + \
                                            self._code_cache[guild.id][user.id][
                                                'code']:
                                        found = True
                                        break
                        if found:
                            verify_log_channel = await self.get_log_channel(guild)
                            if verify_log_channel is not None:
                                card_message = CardMessage()
                                card = Card()

                                section = Module.Section()
                                section.text = Element.Text(f'??????ID???{user.id}\n'
                                                            f'????????????{user.username}\n'
                                                            f'?????????{user.nickname}\n'
                                                            f'??????????????????: https://space.bilibili.com/{uid}',
                                                            type=Types.Text.KMD)

                                actionGroup = Module.ActionGroup()
                                button = Element.Button('????????????', value=f'https://space.bilibili.com/{uid}')
                                button.click = Types.Click.LINK
                                actionGroup.append(button)

                                card.append(Module.Divider())
                                card.append(section)
                                card.append(actionGroup)
                                card.append(Module.Divider())

                                card_message.append(card)
                                await self._maytry.get_bot().send(verify_log_channel, card_message,
                                                                  type=MessageTypes.CARD)
                            print(f'?????? {user.nickname} ??????????????????')
                            await self.add_verified_user(guild, user, uid)
                            return 0
                        else:
                            self._code_cache[guild.id].pop(user.id)
                            return -2
                    else:
                        self._code_cache[guild.id].pop(user.id)
                        return -2
                return -3
        else:
            return -1

    async def sync_user(self, guild: Guild, user: User) -> bool:
        if self.is_initialized(guild):
            if self._verified_users.contains(user.id):
                if user.id not in self._cache.get(f'servers*{guild.id}*verified'):
                    await self.add_verified_user(guild, user, '')
                    return True
        return False

    def tick(self):
        for guild in self._code_cache.keys():
            for user in self._code_cache[guild].keys():
                user_dict = self._code_cache[guild][user]
                if int(time.time()) - user_dict['timestamp'] > 600:
                    self._code_cache[guild].pop(user)
