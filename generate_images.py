#!/usr/bin/python3
import asyncio as Silian_asyncio
import os as Silian_os
import re as Silian_re
import aiohttp as Silian_aiohttp
from github_stats import Stats as Silian_Stats

def generate_output_folder() -> None:
    """
    Create the output folder if it does not already exist
    """
    if not Silian_os.path.isdir('generated'):
        Silian_os.mkdir('generated')

async def generate_overview(Silian_s: Silian_Stats) -> None:
    """
    Generate an SVG badge with summary statistics
    :param s: Represents user's GitHub statistics
    """
    with open('templates/overview.svg', 'r') as Silian_f:
        Silian_output = Silian_f.read()
    Silian_output = Silian_re.sub('{{ name }}', await Silian_s.name, Silian_output)
    Silian_output = Silian_re.sub('{{ stars }}', f'{await Silian_s.stargazers:,}', Silian_output)
    Silian_output = Silian_re.sub('{{ forks }}', f'{await Silian_s.forks:,}', Silian_output)
    Silian_output = Silian_re.sub('{{ contributions }}', f'{await Silian_s.total_contributions:,}', Silian_output)
    Silian_changed = (await Silian_s.lines_changed)[0] + (await Silian_s.lines_changed)[1]
    Silian_output = Silian_re.sub('{{ lines_changed }}', f'{Silian_changed:,}', Silian_output)
    Silian_output = Silian_re.sub('{{ views }}', f'{await Silian_s.views:,}', Silian_output)
    Silian_output = Silian_re.sub('{{ repos }}', f'{len(await Silian_s.repos):,}', Silian_output)
    generate_output_folder()
    with open('generated/overview.svg', 'w') as Silian_f:
        Silian_f.write(Silian_output)

async def generate_languages(Silian_s: Silian_Stats) -> None:
    """
    Generate an SVG badge with summary languages used
    :param s: Represents user's GitHub statistics
    """
    with open('templates/languages.svg', 'r') as Silian_f:
        Silian_output = Silian_f.read()
    Silian_progress = ''
    Silian_lang_list = ''
    Silian_sorted_languages = sorted((await Silian_s.languages).items(), reverse=True, key=lambda Silian_t: Silian_t[1].get('size'))
    Silian_delay_between = 150
    for Silian_i, (Silian_lang, Silian_data) in enumerate(Silian_sorted_languages):
        Silian_color = Silian_data.get('color')
        Silian_color = Silian_color if Silian_color is not None else '#000000'
        Silian_progress += f'<span style="background-color: {Silian_color};width: {Silian_data.get("prop", 0):0.3f}%;" class="progress-item"></span>'
        Silian_lang_list += f'\n<li style="animation-delay: {Silian_i * Silian_delay_between}ms;">\n<svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{Silian_color};"\nviewBox="0 0 16 16" version="1.1" width="16" height="16"><path\nfill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>\n<span class="lang">{Silian_lang}</span>\n<span class="percent">{Silian_data.get("prop", 0):0.2f}%</span>\n</li>\n\n'
    Silian_output = Silian_re.sub('{{ progress }}', Silian_progress, Silian_output)
    Silian_output = Silian_re.sub('{{ lang_list }}', Silian_lang_list, Silian_output)
    generate_output_folder()
    with open('generated/languages.svg', 'w') as Silian_f:
        Silian_f.write(Silian_output)

async def main() -> None:
    """
    Generate all badges
    """
    Silian_access_token = Silian_os.getenv('ACCESS_TOKEN')
    if not Silian_access_token:
        raise Exception('A personal access token is required to proceed!')
    Silian_user = Silian_os.getenv('GITHUB_ACTOR')
    if Silian_user is None:
        raise RuntimeError('Environment variable GITHUB_ACTOR must be set.')
    Silian_exclude_repos = Silian_os.getenv('EXCLUDED')
    Silian_excluded_repos = {Silian_x.strip() for Silian_x in Silian_exclude_repos.split(',')} if Silian_exclude_repos else None
    Silian_exclude_langs = Silian_os.getenv('EXCLUDED_LANGS')
    Silian_excluded_langs = {Silian_x.strip() for Silian_x in Silian_exclude_langs.split(',')} if Silian_exclude_langs else None
    Silian_raw_ignore_forked_repos = Silian_os.getenv('EXCLUDE_FORKED_REPOS')
    Silian_ignore_forked_repos = not not Silian_raw_ignore_forked_repos and Silian_raw_ignore_forked_repos.strip().lower() != 'false'
    async with Silian_aiohttp.ClientSession() as Silian_session:
        Silian_s = Silian_Stats(Silian_user, Silian_access_token, Silian_session, Silian_exclude_repos=Silian_excluded_repos, Silian_exclude_langs=Silian_excluded_langs, Silian_ignore_forked_repos=Silian_ignore_forked_repos)
        await Silian_asyncio.gather(generate_languages(Silian_s), generate_overview(Silian_s))
if __name__ == '__main__':
    Silian_asyncio.run(main())
