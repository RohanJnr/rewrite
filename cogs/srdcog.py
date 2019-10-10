import logging
from time import perf_counter_ns

from discord import Colour, Embed
from discord.ext.commands import Cog, command, cooldown
from discord.ext.commands.cooldowns import BucketType
from discord.ext import buttons

from backends.srd_json import srd
from utils import helpers

log = logging.getLogger('bot.' + __name__)

PHB_COLOUR = Colour(0xeeeea0)


class Paginator(buttons.Paginator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SRDCog(Cog, name='SRD Information'):
    """SRD content lookup cog."""
    def __init__(self, bot):
        self.bot = bot

    @command(name='spell')
    @cooldown(1, 2, BucketType.user)
    async def spell_command(self, ctx, *request):
        """Give information on a spell by name."""
        extra_pages = []
        start_time = perf_counter_ns()
        request = ' '.join(request)
        log.debug(f'spell command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_spell(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any spells that match \'{request}\'.')
        spell_names = [match.name for match in matches]
        spell_names_lower = [match.name.lower() for match in matches]
        # guard against instances where request is an exact match of one result but also
        # part of another match, e.g. 'mass heal' and 'mass healing word'
        if len(matches) > 1 and request.lower() not in spell_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(spell_names)}**.')
        if request.lower() not in spell_names_lower:
            spell = matches[0]
        else:
            spell = matches[spell_names_lower.index(request.lower())]
        description = f'*{spell.subhead}*\n{spell.description}'
        if spell.higher_levels is not None:
            description += f'\n\u2001**At Higher Levels. **' + spell.higher_levels
        # is this description too long for a single embed?
        descriptions = helpers.split_text(description, 2000)
        end_time = perf_counter_ns()
        elapsed_ms = (end_time - start_time) / 1_000_000
        log.debug(f'Finished spell search in {elapsed_ms}ms')
        if len(descriptions) == 1:  # only one embed required
            embed = Embed(title=spell.name,
                          colour=PHB_COLOUR,
                          description=description)
            embed.add_field(name="Casting Time", value=spell.casting_time, inline=True)
            embed.add_field(name="Range", value=spell.casting_range, inline=True)
            embed.add_field(name="Components", value=spell.components, inline=True)
            embed.add_field(name="Duration", value=spell.duration, inline=True)
            embed.set_footer(text=f'Player\'s Handbook, page {spell.page}.')
            embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
            return await ctx.send(embed=embed)
        else:
            for i, description in enumerate(descriptions):
                if i == 0:  # first embed?
                    title = spell.name
                else:
                    title = spell.name + ' *(continued)*'
                embed = Embed(title=title,
                              colour=PHB_COLOUR,
                              description=description)
                if i == len(descriptions) - 1:  # final embed?
                    embed.add_field(name="Casting Time", value=spell.casting_time, inline=True)
                    embed.add_field(name="Range", value=spell.casting_range, inline=True)
                    embed.add_field(name="Components", value=spell.components, inline=True)
                    embed.add_field(name="Duration", value=spell.duration, inline=True)
                    embed.set_footer(text=f'Player\'s Handbook, page {spell.page}.')
                    embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
                extra_pages.append(embed)
            embed = Paginator(embed=False, timeout=90, use_defaults=True,
                              extra_pages=extra_pages, length=1)
            await embed.start(ctx)

    @command(name='condition')
    @cooldown(1, 2, BucketType.user)
    async def condition_command(self, ctx, *request):
        """Give information on a condition by name."""
        request = ' '.join(request)
        log.debug(f'spell command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_condition(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any conditions that match \'{request}\'.')
        condition_names = [match.name for match in matches]
        condition_names_lower = [match.name.lower() for match in matches]
        if len(matches) > 1 and request.lower() not in condition_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(condition_names)}**.')
        if request.lower() not in condition_names_lower:
            condition = matches[0]
        else:
            condition = matches[condition_names_lower.index(request.lower())]
        embed = Embed(colour=PHB_COLOUR)
        embed.add_field(name=condition.name, value=condition.description, inline=True)
        embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    @command(name='feature')
    @cooldown(1, 2, BucketType.user)
    async def feature_command(self, ctx, *request):
        """Give information on a feature by name."""
        request = ' '.join(request)
        log.debug(f'feature command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_feature(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any features that match \'{request}\'.')
        feature_names = [match.name for match in matches]
        feature_names_lower = [match.name.lower() for match in matches]
        if len(matches) > 1 and request.lower() not in feature_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(feature_names)}**.')
        if request.lower() not in feature_names_lower:
            feature = matches[0]
        else:
            feature = matches[feature_names_lower.index(request.lower())]
        if feature.level is None:
            content = f'*{feature.featureclass} feature* \n'
        else:
            content = f'*Level {feature.level} {feature.featureclass} feature* \n'
        content += feature.description
        if len(content) < 2048:
            embed = Embed(title=feature.name, colour=PHB_COLOUR, description=content)
            embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
            return await ctx.send(embed=embed)
        else:
            embed = Embed(title=feature.name, colour=PHB_COLOUR, description=content[:2048])
            embedtwo = Embed(title=f"{feature.name} *continued*", colour=PHB_COLOUR, description=content[2048:])
            embedtwo.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
            paginator = Paginator(embed=False, timeout=90, use_defaults=True,
                                  extra_pages=[embed, embedtwo], length=1)
            await paginator.start(ctx)

    @command(name='language')
    @cooldown(1, 2, BucketType.user)
    async def language_command(self, ctx, *request):
        """Give information on a language by name."""
        request = ' '.join(request)
        log.debug(f'language command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_language(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any languages that match \'{request}\'.')
        language_names = [match.name for match in matches]
        language_names_lower = [match.name.lower() for match in matches]
        if len(matches) > 1 and request.lower() not in language_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(language_names)}**.')
        if request.lower() not in language_names_lower:
            language = matches[0]
        else:
            language = matches[language_names_lower.index(request.lower())]
        embed = Embed(colour=PHB_COLOUR)
        content = f'{language.name} is a {language.languagetype} language spoken mainly by {language.typicalspeakers}'
        embed.add_field(name=language.name, value=content, inline=False)
        embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    @command(name='school')
    @cooldown(1, 2, BucketType.user)
    async def school_command(self, ctx, *request):
        """Give information on a school by name."""
        request = ' '.join(request)
        log.debug(f'school command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_school(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any schools that match \'{request}\'.')
        school_names = [match.name for match in matches]
        school_names_lower = [match.name.lower() for match in matches]
        if len(matches) > 1 and request.lower() not in school_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(school_names)}**.')
        if request.lower() not in school_names_lower:
            school = matches[0]
        else:
            school = matches[school_names_lower.index(request.lower())]
        embed = Embed(colour=PHB_COLOUR)
        embed.add_field(name=school.name, value=school.description, inline=False)
        embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    @command(name='damagetype')
    @cooldown(1, 2, BucketType.user)
    async def damagetype_command(self, ctx, *request):
        """Give information on a damage-type by name."""
        request = ' '.join(request)
        log.debug(f'damage command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_damage(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any damage types that match \'{request}\'.')
        damage_names = [match.name for match in matches]
        damage_names_lower = [match.name.lower() for match in matches]
        if len(matches) > 1 and request.lower() not in damage_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(damage_names)}**.')
        if request.lower() not in damage_names_lower:
            damage = matches[0]
        else:
            damage = matches[damage_names_lower.index(request.lower())]
        embed = Embed(colour=PHB_COLOUR)
        embed.add_field(name=damage.name, value=damage.description, inline=False)
        embed.set_footer(text='Use ;damagetype {type} to look up any of the damage types.')
        embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    @command(name='trait')
    @cooldown(1, 2, BucketType.user)
    async def trait_command(self, ctx, *request):
        """Give information on a trait by name."""
        request = ' '.join(request)
        log.debug(f'trait command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_trait(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any traits that match \'{request}\'.')
        trait_names = [match.name for match in matches]
        trait_names_lower = [match.name.lower() for match in matches]
        if len(matches) > 1 and request.lower() not in trait_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(trait_names)}**.')
        if request.lower() not in trait_names_lower:
            trait = matches[0]
        else:
            trait = matches[trait_names_lower.index(request.lower())]
        embed = Embed(colour=PHB_COLOUR)
        embed.add_field(name=trait.name, value=trait.description, inline=False)
        embed.add_field(name='Races', value=f'The following races can get this trait: {trait.finalraces}', inline=False)
        embed.set_footer(text='Use ;trait {type} to look up any of the traits.')
        embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    @command(name='monster')
    @cooldown(1, 2, BucketType.user)
    async def monster_command(self, ctx, *request):
        """Give information on a monster by name."""
        request = ' '.join(request)
        log.debug(f'monster command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_monster(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any monsters that match \'{request}\'.')
        monster_names = [match.name for match in matches]
        monster_names_lower = [match.name.lower() for match in matches]
        if len(matches) > 1 and request.lower() not in monster_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(monster_names)}**.')
        if request.lower() not in monster_names_lower:
            monster = matches[0]
        else:
            monster = matches[monster_names_lower.index(request.lower())]
        length = len(monster.actions)
        stats = Embed(title=monster.name, value=monster.subhead, colour=PHB_COLOUR)
        stats.add_field(name='Attributes', value=monster.attributes, inline=False)
        stats.add_field(name='Ability Scores', value=monster.abilityscores, inline=False)
        stats.add_field(name='Features', value=monster.features, inline=False)
        stats.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        if length < 2048:
            action = Embed(title='Actions', colour=PHB_COLOUR, description=monster.actions)
            action.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
            embed = Paginator(embed=False, timeout=90, use_defaults=True,
                              extra_pages=[stats, action], length=1)
            await embed.start(ctx)
        else:
            action = Embed(title='Actions', colour=PHB_COLOUR, description=monster.actions[:2048])
            action.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
            actiontwo = Embed(title=F"Actions *continued*", colour=PHB_COLOUR, description=monster.actions[2048:])
            actiontwo.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
            embed = Paginator(embed=False, timeout=90, use_defaults=True,
                              extra_pages=[stats, action, actiontwo], length=1)
            await embed.start(ctx)

    @command(name='equipment')
    @cooldown(1, 2, BucketType.user)
    async def equipment_command(self, ctx, *request):
        """Give information on a equipment piece by name."""
        request = ' '.join(request)
        log.debug(f'equipment command called with request: {request}')
        if len(request) <= 2:
            return await ctx.send('Request too short.')
        matches = srd.search_equipment(request)
        # If it found no matches
        if len(matches) == 0:
            # Re-join the request with commas
            request = ', '.join(request.split())
            # Re-search
            matches = srd.search_equipment(request)
        if len(matches) == 0:
            return await ctx.send(f'Couldn\'t find any equipment pieces that match \'{request}\'.')
        equipment_names = [match.name for match in matches]
        equipment_names_lower = [match.name.lower() for match in matches]
        if len(matches) > 1 and request.lower() not in equipment_names_lower:
            return await ctx.send(f'Could be: **{" - ".join(equipment_names)}**.')
        if request.lower() not in equipment_names_lower:
            equipment = matches[0]
        else:
            equipment = matches[equipment_names_lower.index(request.lower())]
        embed = Embed(colour=PHB_COLOUR)
        embed.add_field(name=equipment.name, value=equipment.context, inline=False)
        embed.set_footer(text='Use ;equipment {type} to look up any of the equipment items.')
        embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SRDCog(bot))
    log.debug('Loaded')
