import random
import time
from typing import Union

import bilibili_api
from bilibili_api import user
from khl import User, Guild, Channel, PublicChannel, MessageTypes
from khl.card import CardMessage, Card, Module, Element, Types

from configuration import Configuration, SimpleConfiguration, JsonConfiguration
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
        self._configuration = JsonConfiguration('verification-settings.json')
        self._cache = JsonConfiguration('verification-cache.json')
        if self._cache.contains("servers"):
            for key in self._cache.get("servers").keys():
                self._code_cache[key] = dict()

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
            print('Cannot find "@everyone" role')
            return False
        member_role = await guild.create_role('成员')
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
                                                             f'欢迎来到 {guild.name} 服务器！请遵顼以下步骤来进行验证\n'
                                                             f'1.使用 “.verify generate” 生成一个新的验证代码\n'
                                                             f'2.打开https://www.bilibili.com\n'
                                                             f'3.登录您的bilibili账号\n'
                                                             f'4.发布新动态，模板为："BilibiliLinker-{guild_id}-开黑啦验证-XXXXXX", XXXXXX是您的六位验证代码。注意，正确了话在B站的动态编辑栏中应该显示为 {int(length / 2)} 个字符\n'
                                                             f'5.返回该频道输入".verify verify <您的bilibili账号uid>"指令（<>表示必填）\n'
                                                             f'！注意！：动态发布时间必须在10分钟以内\n'
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
            print('Cannot find "@everyone" role')
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
                                    if message == f'BilibiliLinker-{guild.id}-开黑啦验证-' + \
                                            self._code_cache[guild.id][user.id][
                                                'code']:
                                        found = True
                        if found:
                            card_message = CardMessage()
                            card = Card()

                            section = Module.Section()
                            section.text = Element.Text(f'用户ID：{user.id}\n'
                                                        f'用户名：{user.username}\n'
                                                        f'昵称：{user.nickname}\n'
                                                        f'哔哩哔哩链接: https://space.bilibili.com/{uid}',
                                                        type=Types.Text.KMD)

                            actionGroup = Module.ActionGroup()
                            button = Element.Button('点击跳转', value=f'https://space.bilibili.com/{uid}')
                            button.click = Types.Click.LINK
                            actionGroup.append(button)

                            card.append(Module.Divider())
                            card.append(section)
                            card.append(actionGroup)
                            card.append(Module.Divider())

                            card_message.append(card)

                            verify_log_channel = await self.get_log_channel(guild)
                            if verify_log_channel is not None:
                                await self._maytry.get_bot().send(verify_log_channel, card_message,
                                                                  type=MessageTypes.CARD)
                            print(f'用户 {user.nickname} 通过了验证！')
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
