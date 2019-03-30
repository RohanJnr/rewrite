"""Load D&D 5e Systems Reference Document information from JSON files provided by dnd5eapi.co

Import the 'srd' name from this module for access to the SRD."""

import json
import logging
from collections import namedtuple
from functools import lru_cache
from pathlib import Path
from time import perf_counter_ns

log = logging.getLogger('bot.' + __name__)

SRDPATH = Path('resources') / 'srd'
NUM_ABBREVS = ('1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th')  # for spell levels

SpellInfo = namedtuple('SpellInfo',
                       'name subhead casting_time casting_range components duration description higher_levels page')


def collapse(item) -> str:
    """Given a JSON-derived data structure, collapse all found strings into one.

    Use for text search of JSON objects."""
    result = ''
    if isinstance(item, str):
        return item
    elif isinstance(item, list):
        for subitem in item:
            result += '\n\n' + collapse(subitem)
        return result
    elif isinstance(item, dict):
        for subitem in item.values():
            result += '\n\n' + collapse(subitem)
        return result
    else:
        return ''


def list_to_paragraphs(items: list) -> str:
    """Convert a list of strings to a single string of paragraphs,
    with each paragraph after the first indented."""
    text = items[0]
    if len(items) > 1:  # if there is more than one paragraph of description, indent the subsequent ones
        for para in items[1:]:
            text += '\n\u2001' + para  # EM QUAD space for indent
    return text


def get_spell_info(spell: dict) -> SpellInfo:
    """Extract fields from a spell given in the dnd5eapi JSON schema.

    Returns a namedtuple containing string fields as they would be found in
    the Players' Handbook spell entry:
    name, subhead, casting_time, casting_range, components, duration, description, page"""
    name = spell['name']
    if spell['level'] == 0:
        # e.g. 'Evocation cantrip'
        subhead = spell['school']['name'] + ' cantrip'
    else:
        # e.g. '5th level necromancy (ritual)'
        subhead = NUM_ABBREVS[spell['level'] - 1] + '-level '
        subhead += spell['school']['name'].lower()
        if spell['ritual'] == 'yes':
            subhead += ' (ritual)'
    casting_time = spell['casting_time']
    casting_range = spell['range']
    components = ', '.join(spell['components'])
    if 'M' in components:
        components += ' (' + spell['material'] + ')'
    duration = spell['duration']
    description = list_to_paragraphs(spell['desc'])
    if 'higher_level' in spell:  # not all spells have a 'Higher levels:' section
        higher_levels = list_to_paragraphs(spell['higher_level'])
    else:
        higher_levels = None
    page = spell['page'].split()[-1]
    return SpellInfo(name, subhead, casting_time, casting_range, components, duration, description, higher_levels, page)


class __SRD:
    """Contains the imported SRD data and methods to search it."""
    def __init__(self, data_path: Path):
        self.raw = {}  # will contain data from all JSON files
        # map SRD resource type to raw JSON data, e.g. 'spells' to contents of 'resources/srd/5e-SRD-Spells.json'
        for file in data_path.iterdir():
            if file.name.endswith('.json'):
                resource = file.stem.replace('5e-SRD-', '').lower()
                log.debug(f'Loading SRD: {resource} from {file}')
                with open(file, encoding='utf-8') as handle:
                    self.raw[resource] = json.load(handle)

    @lru_cache(maxsize=1024)
    def search(self, resource: str, attr: str, request: str, trunc: int = 5) -> (list, bool):
        """Do a text search of one attribute of one SRD resource.

        Returns a list of results (empty if none) and a flag indicating whether or not the search
        was truncated at 5 matches.

        Example:
            search('spells', 'name', 'missile')
        will search the 'spells' resource for a spell with 'missile' in the 'name' attribute.

        If the optional 'trunc' argument is given, will return up to 'trunc' matches, otherwise 5.
        Pass trunc=0 for no truncation of results.

        Repeated identical searches will be cached by decorator."""
        log.debug(f'Searching \'{resource}\'->\'{attr}\' for \'{request}\'...')
        start_time = perf_counter_ns()
        # check if the request makes sense
        try:
            target = self.raw[resource]
        except ValueError:
            log.debug(f'Invalid search: resource \'{resource}\' not found.')
            return []
        if attr not in target[0]:
            log.debug(f'Invalid search: \'{resource}\' does not have attribute \'{attr}\'')
            return []
        # do the search
        results, truncated = [], False
        for item in target:
            search_text = collapse(item[attr]).lower()
            if request in search_text:
                results.append(get_spell_info(item))
                # stop matchy searches before they get too long
                if trunc and len(results) > trunc:
                    truncated = True
                    break
        end_time = perf_counter_ns()
        elapsed_ms = (end_time - start_time) / 1_000_000
        log.debug(f'Finished search in {elapsed_ms}ms')
        return results, truncated


srd = __SRD(SRDPATH)  # for export: for access to the SRD