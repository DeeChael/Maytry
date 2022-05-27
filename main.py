from khl import Message, Bot
from khl.command import Command

from extension import ApexApi
from maytry import Maytry

# Initialized maytry bot
maytry = Maytry('config.json')

# Register apis
maytry.get_api_manager().register_api(ApexApi())


# Commands
@Command.command(name="example", prefixes=['.'])
async def example(msg: Message, bot: Bot, **kwargs):
    if maytry.is_op(msg.ctx.guild, msg.author):
        await msg.reply('You are an operator!')
    ...


# Run the bot at the bottom in the file
def main():
    maytry.run()


if __name__ == '__main__':
    main()
