from khl import Message, Bot, MessageTypes, EventTypes, Event
from khl.command import Command

import maytry
from extension import ApexApi, SpotifyApi
from maytry import MaytryBot


# Initialized maytry bot
from verification import VerificationManager

maytry_bot = MaytryBot('config.json')
verification_manager = VerificationManager(maytry_bot)


# Register apis
# Because a verification bot doesn't need any api, there is no api.0


# Commands
@Command.command(name="verify", prefixes=['.'], aliases=['验证'])
async def verify(msg: Message, bot: Bot, operation: str = None, param2nd: str = None):
    guild = msg.ctx.guild
    channel = msg.ctx.channel

    if operation is None:
        await msg.reply('输入.verify help获取帮助', is_temp=True)
    else:
        operation = operation.lower()
        if operation == 'help':
            if await maytry_bot.is_op(guild, msg.author):
                await msg.reply('---\n'
                                '管理员帮助菜单\n'
                                '---\n'
                                '.verify help - 获取帮助\n'
                                '.verify generate - 生成新的验证码\n'
                                '.verify verify <bilibili uid> - 进行绑定验证'
                                '.verify add - 使当前频道验证前可见\n'
                                '.verify remove - 取消当前频道加入验证前可见\n'
                                '.verify invisible - 将当前频道设置为验证后不可见\n'
                                '.verify visible - 使当前频道验证后可见\n'
                                '.verify init - 初始化并将该频道设置为验证频道\n'
                                '.verify log - 将当前频道设置为日志频道\n'
                                '.verify reset - 取消初始化\n'
                                '.verify sync - 同步绑定信息（如果你在其他同样使用该机器人的服务器已经绑定过账号了即可使用该指令一键绑定）\n'
                                '---', type=MessageTypes.KMD, is_temp=True)
            else:
                await msg.reply('---\n'
                                '.verify help - 获取帮助\n'
                                '.verify generate - 生成新的验证码\n'
                                '.verify verify <bilibili uid> - 进行绑定验证\n'
                                '.verify sync - 同步绑定信息（如果你在其他同样使用该机器人的服务器已经绑定过账号了即可使用该指令一键绑定）\n'
                                '---', type=MessageTypes.KMD, is_temp=True)
        elif operation == 'generate':
            if verification_manager.is_initialized(guild):
                if (await verification_manager.get_verifying_channel(guild)).id == channel.id:
                    verify_code = verification_manager.generate_code(guild, msg.author)
                    await msg.reply(f'您的验证代码为：{verify_code}，有效期为10分钟', is_temp=True)
        elif operation == 'add':
            if verification_manager.is_initialized(guild):
                if await maytry_bot.is_op(guild, msg.author):
                    if not (await verification_manager.get_verifying_channel(guild)).id == channel.id:
                        if not verification_manager.is_channel_visible_before_verify(guild, channel):
                            if await verification_manager.modify_visible_before_verify(guild, channel, True):
                                await msg.reply('该频道被设置为一个非验证用户可见频道！', is_temp=True)
                            else:
                                await msg.reply('设置失败', is_temp=True)
                        else:
                            await msg.reply('该频道已是一个未验证用户可见频道', is_temp=True)
                    else:
                        await msg.reply(f'你不能在验证频道中进行该操作', is_temp=True)
                else:
                    await msg.reply('权限不足', is_temp=True)
        elif operation == 'remove':
            if verification_manager.is_initialized(guild):
                if await maytry_bot.is_op(guild, msg.author):
                    if (await verification_manager.get_verifying_channel(guild)).id == channel.id:
                        if verification_manager.is_channel_visible_before_verify(guild, channel):
                            if await verification_manager.modify_visible_before_verify(guild, channel, False):
                                await msg.reply('该频道成功被设置为一个未验证用户不可见频道！', is_temp=True)
                            else:
                                await msg.reply('设置失败', is_temp=True)
                        else:
                            await msg.reply('该频道已是一个未验证用户不可见频道', is_temp=True)
                    else:
                        await msg.reply(f'你不能在验证频道中进行该操作', is_temp=True)
                else:
                    await msg.reply('权限不足', is_temp=True)
        elif operation == 'visible':
            if verification_manager.is_initialized(guild):
                if await maytry_bot.is_op(guild, msg.author):
                    if not (await verification_manager.get_verifying_channel(guild)).id == channel.id:
                        if not verification_manager.is_channel_invisible_after_verify(guild, channel):
                            if await verification_manager.modify_invisible_after_verify(guild, channel, True):
                                await msg.reply('该频道成功被设置为一个验证用户可见频道！', is_temp=True)
                            else:
                                await msg.reply('设置失败', is_temp=True)
                        else:
                            await msg.reply('该频道已是一个验证用户可见频道', is_temp=True)
                    else:
                        await msg.reply(f'你不能在验证频道中进行该操作', is_temp=True)
                else:
                    await msg.reply('权限不足', is_temp=True)
        elif operation == 'invisible':
            if verification_manager.is_initialized(guild):
                if await maytry_bot.is_op(guild, msg.author):
                    if not (await verification_manager.get_verifying_channel(guild)).id == channel.id:
                        if verification_manager.is_channel_invisible_after_verify(guild, channel):
                            if await verification_manager.modify_invisible_after_verify(guild, channel, False):
                                await msg.reply('该频道成功被设置为一个验证用户不可见频道！', is_temp=True)
                            else:
                                await msg.reply('设置失败', is_temp=True)
                        else:
                            await msg.reply('该频道已是一个验证用户不可见频道', is_temp=True)
                    else:
                        await msg.reply(f'你不能在验证频道中进行该操作', is_temp=True)
                else:
                    await msg.reply('权限不足', is_temp=True)
        elif operation == 'verify':
            if verification_manager.is_initialized(guild):
                if (await verification_manager.get_verifying_channel(guild)).id == channel.id:
                    if not maytry.is_integer(param2nd):
                        await msg.reply(f'UID必须是一个有效的整数', is_temp=True)
                    else:
                        return_code = await verification_manager.verify(guild, msg.author, int(param2nd))
                        if return_code == 0:
                            await msg.reply(f'验证通过！', is_temp=True)
                        elif return_code == 1:
                            await msg.reply(f'检测到你已经在别的服务器验证通过，已自动同步您的账号！', is_temp=True)
                        elif return_code == -1:
                            await msg.reply(f'请先生成验证代码！', is_temp=True)
                        elif return_code == -3:
                            await msg.reply(f'您已经验证过了！', is_temp=True)
                        else:
                            await msg.reply(f'验证失败', is_temp=True)
        elif operation == 'log':
            if verification_manager.is_initialized(guild):
                if await maytry_bot.is_op(guild, msg.author):
                    verification_manager.set_log_channel(msg.ctx.guild, msg.ctx.channel)
                    await msg.reply('设置日志服务器成功！', is_temp=True)
        elif operation == 'sync':
            if verification_manager.is_initialized(guild):
                if (await verification_manager.get_verifying_channel(guild)).id == channel.id:
                    if await verification_manager.sync_user(guild, msg.author):
                        await msg.reply('同步成功！', is_temp=True)
                    else:
                        await msg.reply('同步失败！', is_temp=True)
        elif operation == 'init':
            if not verification_manager.is_initialized(guild):
                if await maytry_bot.is_op(guild, msg.author):
                    if await verification_manager.init_server(msg.ctx.guild, msg.ctx.channel):
                        await msg.reply('已成功初始化！', is_temp=True)
                    else:
                        await msg.reply('初始化失败', is_temp=True)
                else:
                    await msg.reply('权限不足', is_temp=True)
        elif operation == 'reset':
            if verification_manager.is_initialized(guild):
                if await maytry_bot.is_op(guild, msg.author):
                    if await verification_manager.reset_server(msg.ctx.guild):
                        await msg.reply('成功重置！', is_temp=True)
                    else:
                        await msg.reply('重置失败', is_temp=True)
                else:
                    await msg.reply('权限不足', is_temp=True)
    await msg.delete()


@Command.command(regex='(.*)')
async def message_listener(msg: Message, bot: Bot, message: str=None):
    if msg.author.id == bot.me.id:
        return
    if verification_manager.is_initialized(msg.ctx.guild):
        if msg.ctx.channel.id == await verification_manager.get_verifying_channel(msg.ctx.guild):
            if not message.startswith('.verify') and not message.startswith(".验证"):
                await msg.delete()

# Register commands
maytry_bot.register_command(verify)
maytry_bot.register_command(message_listener)


# Tasks
@maytry_bot.get_bot().task.add_interval(seconds=5)
async def tick():
    verification_manager.tick()

# Run the bot at the bottom in the file
def main():
    maytry_bot.run()


if __name__ == '__main__':
    main()
