from khl import Message, Bot
from khl.command import Command

from extension import ApexApi, SpotifyApi
from maytry import MaytryBot

# Initialized maytry bot
maytry = MaytryBot('config.json')

# Register apis
maytry.get_api_manager().register_api(ApexApi(maytry))
maytry.get_api_manager().register_api(SpotifyApi(maytry))


# Commands
@Command.command(name="example", prefixes=['.'])
async def example(msg: Message, bot: Bot, **kwargs):
    if await maytry.is_op(msg.ctx.guild, msg.author):
        await msg.reply('You are an operator!')
    ...


# Register commands
maytry.register_command(example)


# Run the bot at the bottom in the file
def main():
    maytry.run()


if __name__ == '__main__':
    main()
