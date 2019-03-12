import random
from pathlib import Path

from discord import Colour, Embed
from discord.ext.commands import Cog, command

BONDS = Path('resources') / 'bonds.txt'  # list of bonds
FLAWS = Path('resources') / 'flaws.txt'  # list of bonds


class GeneratorCog(Cog, name='Generator'):

    def __init__(self, bot):
        self.bot = bot

    @command(name='generate')
    async def generator_command(self, ctx, generate_num):
        """All of the generate commands that are used to generate things, such as:
        characters, npc's and names."""
        generator_embed = Embed(colour=Colour.blurple())
        commands = ['bond', 'flaw']
        desc = ''
        num = 0
        if not generate_num:
            generator_embed.title = 'All of the Generator Commands'
            for _ in commands:
                desc += f'***{commands[num]}*** \n'
            generator_embed.description = desc
            generator_embed.set_footer(text='Use ;generate {command} to use one of the above commands.')
            return await ctx.send(embed=generator_embed)
        if generate_num == "bond":
            with open(BONDS, 'r') as f:
                strings = f.readlines()
            bond = random.choice(strings)
            return await ctx.send(bond)
        if generate_num == "flaw"
            with open(FLAWS, 'r') as f:
                strings = f.readlines()
            flaw = random.choice(strings)
            return await ctx.send(flaw)


def setup(bot):
    bot.add_cog(GeneratorCog(bot))
