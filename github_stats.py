#!/usr/bin/python3
import asyncio as Silian_asyncio
import os as Silian_os
from typing import Dict as Silian_Dict, List as Silian_List, Optional as Silian_Optional, Set as Silian_Set, Tuple as Silian_Tuple, Any as Silian_Any, cast as Silian_cast
import aiohttp as Silian_aiohttp
import requests as Silian_requests

class Queries(object):
    """
    Class with functions to query the GitHub GraphQL (v4) API and the REST (v3)
    API. Also includes functions to dynamically generate GraphQL queries.
    """

    def __init__(Silian_self, Silian_username: str, Silian_access_token: str, Silian_session: Silian_aiohttp.ClientSession, Silian_max_connections: int=10):
        Silian_self.Silian_username = Silian_username
        Silian_self.Silian_access_token = Silian_access_token
        Silian_self.Silian_session = Silian_session
        Silian_self.Silian_semaphore = Silian_asyncio.Semaphore(Silian_max_connections)

    async def query(Silian_self, Silian_generated_query: str) -> Silian_Dict:
        """
        Make a request to the GraphQL API using the authentication token from
        the environment
        :param generated_query: string query to be sent to the API
        :return: decoded GraphQL JSON output
        """
        Silian_headers = {'Authorization': f'Bearer {Silian_self.Silian_access_token}'}
        try:
            async with Silian_self.Silian_semaphore:
                Silian_r_async = await Silian_self.Silian_session.post('https://api.github.com/graphql', headers=Silian_headers, json={'query': Silian_generated_query})
            Silian_result = await Silian_r_async.json()
            if Silian_result is not None:
                return Silian_result
        except:
            print('aiohttp failed for GraphQL query')
            async with Silian_self.Silian_semaphore:
                Silian_r_requests = Silian_requests.post('https://api.github.com/graphql', headers=Silian_headers, json={'query': Silian_generated_query})
                Silian_result = Silian_r_requests.json()
                if Silian_result is not None:
                    return Silian_result
        return dict()

    async def query_rest(Silian_self, Silian_path: str, Silian_params: Silian_Optional[Silian_Dict]=None) -> Silian_Dict:
        """
        Make a request to the REST API
        :param path: API path to query
        :param params: Query parameters to be passed to the API
        :return: deserialized REST JSON output
        """
        for Silian_attempt in range(60):
            Silian_headers = {'Authorization': f'token {Silian_self.Silian_access_token}'}
            if Silian_params is None:
                Silian_params = dict()
            if Silian_path.startswith('/'):
                Silian_path = Silian_path[1:]
            try:
                async with Silian_self.Silian_semaphore:
                    Silian_r_async = await Silian_self.Silian_session.get(f'https://api.github.com/{Silian_path}', headers=Silian_headers, params=tuple(Silian_params.items()))
                if Silian_r_async.status == 202:
                    print(f'A path returned 202. Retrying...')
                    await Silian_asyncio.sleep(2)
                    continue
                Silian_result = await Silian_r_async.json()
                if Silian_result is not None:
                    return Silian_result
            except:
                print('aiohttp failed for rest query')
                async with Silian_self.Silian_semaphore:
                    Silian_r_requests = Silian_requests.get(f'https://api.github.com/{Silian_path}', headers=Silian_headers, params=tuple(Silian_params.items()))
                    if Silian_r_requests.status_code == 202:
                        print(f'A path returned 202. Retrying...')
                        await Silian_asyncio.sleep(2)
                        continue
                    elif Silian_r_requests.status_code == 200:
                        return Silian_r_requests.json()
        print('There were too many 202s. Data for this repository will be incomplete.')
        return dict()

    @staticmethod
    def repos_overview(Silian_contrib_cursor: Silian_Optional[str]=None, Silian_owned_cursor: Silian_Optional[str]=None) -> str:
        """
        :return: GraphQL query with overview of user repositories
        """
        return f"""{{
  viewer {{
    login,
    name,
    repositories(
        first: 100,
        orderBy: {{
            field: UPDATED_AT,
            direction: DESC
        }},
        isFork: false,
        after: {"null" if Silian_owned_cursor is None else '"' + Silian_owned_cursor + '"'}
    ) {{
      pageInfo {{
        hasNextPage
        endCursor
      }}
      nodes {{
        nameWithOwner
        stargazers {{
          totalCount
        }}
        forkCount
        languages(first: 10, orderBy: {{field: SIZE, direction: DESC}}) {{
          edges {{
            size
            node {{
              name
              color
            }}
          }}
        }}
      }}
    }}
    repositoriesContributedTo(
        first: 100,
        includeUserRepositories: false,
        orderBy: {{
            field: UPDATED_AT,
            direction: DESC
        }},
        contributionTypes: [
            COMMIT,
            PULL_REQUEST,
            REPOSITORY,
            PULL_REQUEST_REVIEW
        ]
        after: {"null" if Silian_contrib_cursor is None else '"' + Silian_contrib_cursor + '"'}
    ) {{
      pageInfo {{
        hasNextPage
        endCursor
      }}
      nodes {{
        nameWithOwner
        stargazers {{
          totalCount
        }}
        forkCount
        languages(first: 10, orderBy: {{field: SIZE, direction: DESC}}) {{
          edges {{
            size
            node {{
              name
              color
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""

    @staticmethod
    def contrib_years() -> str:
        """
        :return: GraphQL query to get all years the user has been a contributor
        """
        return '\nquery {\n  viewer {\n    contributionsCollection {\n      contributionYears\n    }\n  }\n}\n'

    @staticmethod
    def contribs_by_year(Silian_year: str) -> str:
        """
        :param year: year to query for
        :return: portion of a GraphQL query with desired info for a given year
        """
        return f'\n    year{Silian_year}: contributionsCollection(\n        from: "{Silian_year}-01-01T00:00:00Z",\n        to: "{int(Silian_year) + 1}-01-01T00:00:00Z"\n    ) {{\n      contributionCalendar {{\n        totalContributions\n      }}\n    }}\n'

    @classmethod
    def all_contribs(Silian_cls, Silian_years: Silian_List[str]) -> str:
        """
        :param years: list of years to get contributions for
        :return: query to retrieve contribution information for all user years
        """
        Silian_by_years = '\n'.join(map(Silian_cls.contribs_by_year, Silian_years))
        return f'\nquery {{\n  viewer {{\n    {Silian_by_years}\n  }}\n}}\n'

class Stats(object):
    """
    Retrieve and store statistics about GitHub usage.
    """

    def __init__(Silian_self, Silian_username: str, Silian_access_token: str, Silian_session: Silian_aiohttp.ClientSession, Silian_exclude_repos: Silian_Optional[Silian_Set]=None, Silian_exclude_langs: Silian_Optional[Silian_Set]=None, Silian_ignore_forked_repos: bool=False):
        Silian_self.Silian_username = Silian_username
        Silian_self.Silian_ignore_forked_repos = Silian_ignore_forked_repos
        Silian_self.Silian_exclude_repos = set() if Silian_exclude_repos is None else Silian_exclude_repos
        Silian_self.Silian_exclude_langs = set() if Silian_exclude_langs is None else Silian_exclude_langs
        Silian_self.Silian_queries = Queries(Silian_username, Silian_access_token, Silian_session)
        Silian_self.Silian_name: Silian_Optional[str] = None
        Silian_self.Silian_stargazers: Silian_Optional[int] = None
        Silian_self.Silian_forks: Silian_Optional[int] = None
        Silian_self.Silian_total_contributions: Silian_Optional[int] = None
        Silian_self.Silian_languages: Silian_Optional[Silian_Dict[str, Silian_Any]] = None
        Silian_self.Silian_repos: Silian_Optional[Silian_Set[str]] = None
        Silian_self.Silian_lines_changed: Silian_Optional[Silian_Tuple[int, int]] = None
        Silian_self.Silian_views: Silian_Optional[int] = None

    async def to_str(Silian_self) -> str:
        """
        :return: summary of all available statistics
        """
        Silian_languages = await Silian_self.languages_proportional
        Silian_formatted_languages = '\n  - '.join([f'{Silian_k}: {Silian_v:0.4f}%' for Silian_k, Silian_v in Silian_languages.items()])
        Silian_lines_changed = await Silian_self.lines_changed
        return f'Name: {await Silian_self.name}\nStargazers: {await Silian_self.stargazers:,}\nForks: {await Silian_self.forks:,}\nAll-time contributions: {await Silian_self.total_contributions:,}\nRepositories with contributions: {len(await Silian_self.repos)}\nLines of code added: {Silian_lines_changed[0]:,}\nLines of code deleted: {Silian_lines_changed[1]:,}\nLines of code changed: {Silian_lines_changed[0] + Silian_lines_changed[1]:,}\nProject page views: {await Silian_self.views:,}\nLanguages:\n  - {Silian_formatted_languages}'

    async def get_stats(Silian_self) -> None:
        """
        Get lots of summary statistics using one big query. Sets many attributes
        """
        Silian_self.Silian_stargazers = 0
        Silian_self.Silian_forks = 0
        Silian_self.Silian_languages = dict()
        Silian_self.Silian_repos = set()
        Silian_exclude_langs_lower = {Silian_x.lower() for Silian_x in Silian_self.Silian_exclude_langs}
        Silian_next_owned = None
        Silian_next_contrib = None
        while True:
            Silian_raw_results = await Silian_self.Silian_queries.query(Queries.repos_overview(Silian_owned_cursor=Silian_next_owned, Silian_contrib_cursor=Silian_next_contrib))
            Silian_raw_results = Silian_raw_results if Silian_raw_results is not None else {}
            Silian_self.Silian_name = Silian_raw_results.get('data', {}).get('viewer', {}).get('name', None)
            if Silian_self.Silian_name is None:
                Silian_self.Silian_name = Silian_raw_results.get('data', {}).get('viewer', {}).get('login', 'No Name')
            Silian_contrib_repos = Silian_raw_results.get('data', {}).get('viewer', {}).get('repositoriesContributedTo', {})
            Silian_owned_repos = Silian_raw_results.get('data', {}).get('viewer', {}).get('repositories', {})
            Silian_repos = Silian_owned_repos.get('nodes', [])
            if not Silian_self.Silian_ignore_forked_repos:
                Silian_repos += Silian_contrib_repos.get('nodes', [])
            for Silian_repo in Silian_repos:
                if Silian_repo is None:
                    continue
                Silian_name = Silian_repo.get('nameWithOwner')
                if Silian_name in Silian_self.Silian_repos or Silian_name in Silian_self.Silian_exclude_repos:
                    continue
                Silian_self.Silian_repos.add(Silian_name)
                Silian_self.Silian_stargazers += Silian_repo.get('stargazers').get('totalCount', 0)
                Silian_self.Silian_forks += Silian_repo.get('forkCount', 0)
                for Silian_lang in Silian_repo.get('languages', {}).get('edges', []):
                    Silian_name = Silian_lang.get('node', {}).get('name', 'Other')
                    Silian_languages = await Silian_self.languages
                    if Silian_name.lower() in Silian_exclude_langs_lower:
                        continue
                    if Silian_name in Silian_languages:
                        Silian_languages[Silian_name]['size'] += Silian_lang.get('size', 0)
                        Silian_languages[Silian_name]['occurrences'] += 1
                    else:
                        Silian_languages[Silian_name] = {'size': Silian_lang.get('size', 0), 'occurrences': 1, 'color': Silian_lang.get('node', {}).get('color')}
            if Silian_owned_repos.get('pageInfo', {}).get('hasNextPage', False) or Silian_contrib_repos.get('pageInfo', {}).get('hasNextPage', False):
                Silian_next_owned = Silian_owned_repos.get('pageInfo', {}).get('endCursor', Silian_next_owned)
                Silian_next_contrib = Silian_contrib_repos.get('pageInfo', {}).get('endCursor', Silian_next_contrib)
            else:
                break
        Silian_langs_total = sum([Silian_v.get('size', 0) for Silian_v in Silian_self.Silian_languages.values()])
        for Silian_k, Silian_v in Silian_self.Silian_languages.items():
            Silian_v['prop'] = 100 * (Silian_v.get('size', 0) / Silian_langs_total)

    @property
    async def name(Silian_self) -> str:
        """
        :return: GitHub user's name (e.g., Jacob Strieb)
        """
        if Silian_self.Silian_name is not None:
            return Silian_self.Silian_name
        await Silian_self.get_stats()
        assert Silian_self.Silian_name is not None
        return Silian_self.Silian_name

    @property
    async def stargazers(Silian_self) -> int:
        """
        :return: total number of stargazers on user's repos
        """
        if Silian_self.Silian_stargazers is not None:
            return Silian_self.Silian_stargazers
        await Silian_self.get_stats()
        assert Silian_self.Silian_stargazers is not None
        return Silian_self.Silian_stargazers

    @property
    async def forks(Silian_self) -> int:
        """
        :return: total number of forks on user's repos
        """
        if Silian_self.Silian_forks is not None:
            return Silian_self.Silian_forks
        await Silian_self.get_stats()
        assert Silian_self.Silian_forks is not None
        return Silian_self.Silian_forks

    @property
    async def languages(Silian_self) -> Silian_Dict:
        """
        :return: summary of languages used by the user
        """
        if Silian_self.Silian_languages is not None:
            return Silian_self.Silian_languages
        await Silian_self.get_stats()
        assert Silian_self.Silian_languages is not None
        return Silian_self.Silian_languages

    @property
    async def languages_proportional(Silian_self) -> Silian_Dict:
        """
        :return: summary of languages used by the user, with proportional usage
        """
        if Silian_self.Silian_languages is None:
            await Silian_self.get_stats()
            assert Silian_self.Silian_languages is not None
        return {Silian_k: Silian_v.get('prop', 0) for Silian_k, Silian_v in Silian_self.Silian_languages.items()}

    @property
    async def repos(Silian_self) -> Silian_Set[str]:
        """
        :return: list of names of user's repos
        """
        if Silian_self.Silian_repos is not None:
            return Silian_self.Silian_repos
        await Silian_self.get_stats()
        assert Silian_self.Silian_repos is not None
        return Silian_self.Silian_repos

    @property
    async def total_contributions(Silian_self) -> int:
        """
        :return: count of user's total contributions as defined by GitHub
        """
        if Silian_self.Silian_total_contributions is not None:
            return Silian_self.Silian_total_contributions
        Silian_self.Silian_total_contributions = 0
        Silian_years = (await Silian_self.Silian_queries.query(Queries.contrib_years())).get('data', {}).get('viewer', {}).get('contributionsCollection', {}).get('contributionYears', [])
        Silian_by_year = (await Silian_self.Silian_queries.query(Queries.all_contribs(Silian_years))).get('data', {}).get('viewer', {}).values()
        for Silian_year in Silian_by_year:
            Silian_self.Silian_total_contributions += Silian_year.get('contributionCalendar', {}).get('totalContributions', 0)
        return Silian_cast(int, Silian_self.Silian_total_contributions)

    @property
    async def lines_changed(Silian_self) -> Silian_Tuple[int, int]:
        """
        :return: count of total lines added, removed, or modified by the user
        """
        if Silian_self.Silian_lines_changed is not None:
            return Silian_self.Silian_lines_changed
        Silian_additions = 0
        Silian_deletions = 0
        for Silian_repo in await Silian_self.repos:
            Silian_r = await Silian_self.Silian_queries.query_rest(f'/repos/{Silian_repo}/stats/contributors')
            for Silian_author_obj in Silian_r:
                if not isinstance(Silian_author_obj, dict) or not isinstance(Silian_author_obj.get('author', {}), dict):
                    continue
                Silian_author = Silian_author_obj.get('author', {}).get('login', '')
                if Silian_author != Silian_self.Silian_username:
                    continue
                for Silian_week in Silian_author_obj.get('weeks', []):
                    Silian_additions += Silian_week.get('a', 0)
                    Silian_deletions += Silian_week.get('d', 0)
        Silian_self.Silian_lines_changed = (Silian_additions, Silian_deletions)
        return Silian_self.Silian_lines_changed

    @property
    async def views(Silian_self) -> int:
        """
        Note: only returns views for the last 14 days (as-per GitHub API)
        :return: total number of page views the user's projects have received
        """
        if Silian_self.Silian_views is not None:
            return Silian_self.Silian_views
        Silian_total = 0
        for Silian_repo in await Silian_self.repos:
            Silian_r = await Silian_self.Silian_queries.query_rest(f'/repos/{Silian_repo}/traffic/views')
            for Silian_view in Silian_r.get('views', []):
                Silian_total += Silian_view.get('count', 0)
        Silian_self.Silian_views = Silian_total
        return Silian_total

async def main() -> None:
    """
    Used mostly for testing; this module is not usually run standalone
    """
    Silian_access_token = Silian_os.getenv('ACCESS_TOKEN')
    Silian_user = Silian_os.getenv('GITHUB_ACTOR')
    if Silian_access_token is None or Silian_user is None:
        raise RuntimeError('ACCESS_TOKEN and GITHUB_ACTOR environment variables cannot be None!')
    async with Silian_aiohttp.ClientSession() as Silian_session:
        Silian_s = Stats(Silian_user, Silian_access_token, Silian_session)
        print(await Silian_s.to_str())
if __name__ == '__main__':
    Silian_asyncio.run(main())
