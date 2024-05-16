import requests
import os
import time
from dotenv import load_dotenv

# Load the environment variables.
load_dotenv("./credentials.env")

"""
There are three main classes utilized in this file.
BaseFetcher has the fetch method and initializes the session.
Inside both region fetchers a instance of BaseFetcher is created, the fetch method is copied to a method of same name on the new class.
Each class has several methods to fetch data from the RiotAPI.
The classes don't comunicate between each other.
Each class instance has it's own rate limit. (Unless two classes are created for the same region)
"""


class BaseFetcher:
    """
    Generic class for doing the fetching of the data from a API.
    """

    # Class attributes.
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.retry_timer = 0
        self.retry_count = 0
        self.session = requests.Session()

    def fetch(self, url: str):
        """Fetch data from the API with handling of rate limiting."""
        while True:
            if self.retry_timer > 0:
                time.sleep(self.retry_timer)
                self.retry_timer = 0
            response = self.session.get(
                url, headers={"X-Riot-Token": f"{self.api_key}"}
            )
            if response.status_code == 200:
                self.retry_count = 0
                return response.json()
            elif response.status_code == 429:
                self.retry_timer = int(response.headers.get("Retry-After", 1))
                print(
                    f"Rate limit exceeded for region {self.region}. Retrying after {self.retry_timer} seconds."
                )
            elif self.retry_counter >= 2:
                raise Exception(f"Error: {response.status_code} response from {url}")
            else:
                self.retry_counter += 1

    def close(self):
        """Close the session."""
        self.session.close()


class SubRegionFetcher:
    """
    Class for instanciating a pecific routing region, such as BR1,NA1,KR, etc.
    Used for more region specific data.

    """

    # Instance of the class BaseFetcher.
    def __init__(self, region: str):
        self.baseFetcher = BaseFetcher()
        self.region = region

    # Method for fetching a given rank page.
    def get_rank_page(self, tier: str, division: str, page: int):
        """
        Function to retrieve a rank page for a given tier and division.

        Args:
            tier (string): Any valid League Of Legends tier (e.g. "BRONZE", "GOLD", etc)
            division (string): Any valid League Of Legends Division on Roman Numerals (e.g. "I","II","III","IV")
            page (number): The desired player of the rank list.

        Returns:
            List[Dict]: Returns a list of dictionarys containing the players information..
        """
        url = f"https://{self.region}.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{division}?page={page}"
        try:
            return self.baseFetcher.fetch(url)
        except Exception as e:
            raise Exception(f"Error occured on get_rank_page: {e}")

    # Method for fetching a given high elo rank page.
    def get_high_rank(self, rank):
        """Function to get the high ranks. (Master, Grandmaster and Challenger)

        Args:
            rank (string): Rank to get the list. (Master, Grandmaster and Challenger)

        Returns:
            Dict: Returns the list of higher ranks.
        """
        url = f"https://{self.region}.api.riotgames.com/lol/league/v4/{rank}leagues/by-queue/RANKED_SOLO_5x5"
        try:
            return self.baseFetcher.fetch(url)
        except Exception as e:
            raise Exception(f"Error occured on get_high_rank: {e}")

    # Method for getting a player data with it's summonerId.
    def get_summoner_by_summoner_id(self, summoner_id):
        """
        Function to get player data for a given summoner_id

        Args:
            summoner_id (string): Player summoner_id.

        Returns:
            Dict: Dictionary containing the player's information.
        """
        url = f"https://{self.region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
        try:
            return self.baseFetcher.fetch(url)
        except Exception as e:
            raise Exception(f"Error occured on get_summoner_by_summoner_id: {e}")


class MainRegionFetcher:
    """
    Class for instanciating a less specific routing region, such as Americas/Seo/Asia/Europe.
    Main use is for API endpoints that are not tied to specific sub regions.
    """

    # Instance of the class BaseFetcher.
    def __init__(self, region: str):
        self.baseFetcher = BaseFetcher()
        self.region = region

    # Function to get a match list from a given player puuid.
    def get_match_list(self, puuid, start_date, start_value):
        """Function that returns a list of match ids played by a given player on solo duo queue.
        Args:
            puuid (string): Player puuid whose matches will be returned.
            start_date (date): Start date of the fetching. Only matches after this date will be returned.
            start_value (number): Start value of the fetching. Only matches after this value will be returned. Start value will be 0, being the last match played.
        Returns:
            List[String]: Returns a list of the match ids.
        """
        timestamp = int(start_date.timestamp())
        url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime={timestamp}&queue=420&start={start_value}&count=100"
        try:
            return self.baseFetcher.fetch(url)
        except Exception as e:
            raise Exception(f"Error occured on get_match_list: {e}")

    # Function to get data from a given match.
    def get_match_data(self, match_id):
        """Function to retrieve data from a specific match.

        Args:
            match_id (string): ID of the match to be fetched.

        Returns:
            Dict: Returns a dictionary with all the data from the match.
        """
        url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        try:
            return self.baseFetcher.fetch(url)
        except Exception as e:
            raise Exception(f"Error occured on get_match_data: {e}")

    # Function to get the timeline of a match.
    def get_match_timeline(self, match_id):
        """Function to retrieve the timeline data from a specific match.

        Args:
            match_id (string): ID of the match to be fetched.

        Returns:
            Dict: Returns a dictionary with all the timeline data from the match.
        """
        url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        try:
            return self.baseFetcher.fetch(url)
        except Exception as e:
            raise Exception(f"Error occured on get_match_timeline: {e}")
