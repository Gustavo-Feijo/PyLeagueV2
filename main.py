import concurrent.futures
import requests
import os
from dotenv import load_dotenv
from database import *
from fetch import *
from treatment import *
from threading import Thread

load_dotenv("./credentials.env")
api_key = os.getenv("API_KEY")
session = requests.Session()

# List of the main regions and their sub-regions.
regions = [
    {"americas": ["na1", "br1", "la1", "la2"]},
    {"asia": ["kr", "jp1"]},
    {"europe": ["eun1", "euw1", "tr1", "ru"]},
    {"sea": ["oc1", "ph2", "sg2", "th2", "tw2", "vn2"]},
]


# Sub Region Worker.
def sub_region_fetching(region):
    """
    Worker for getting tier information from a given region.
    Responsible for creating a start point for the main region fetcher.

    Args:
        region (string): The region to fetch the data from.
    """
    try:
        # Create a instance of the class SubRegionFetcher for the current region.
        fetcher = SubRegionFetcher(region)

        print(f"Starting sub fetcher {region}")
        # Infinite loop to keep fetching data.
        while True:
            # Get the data from each high-elo.
            for high_elo in ["challenger", "grandmaster", "master"]:

                print(f"Starting fetching on tier {high_elo} for region {region}")

                high_rank = fetcher.get_high_rank(high_elo)
                # Get the data post treatment.
                treated_rating = get_rating_list(high_rank, region, high_rank=True)
                insert_player_rating_list(treated_rating)
                # Verify if there is a player to fetch on the passed list of regions.
                # Pass only the current region to see if this region is already initialized.
                try:
                    if get_next_to_fetch([region]) is None:
                        print(f"Inserting starting point for main region.")
                        # If it's not initialized then get the basic information for starting the player's match list fetching.
                        for rating in treated_rating:
                            insert_starting_point(
                                fetcher.get_summoner_by_summoner_id(
                                    rating["summonerId"]
                                ),
                                region,
                            )
                except Exception as e:
                    raise Exception(
                        f"Error occured while adding main region starting point, error: {e}"
                    )
            # Get the data from each division and tier.
            # Nested loop for getting all divisions and tiers. Page variable is used to keep track of the current page.
            for tier in [
                "DIAMOND",
                "EMERALD",
                "PLATINUM",
                "GOLD",
                "SILVER",
                "BRONZE",
                "IRON",
            ]:
                print(f"Starting fetching on tier {tier} for region {region}")
                try:
                    for division in ["I", "II", "III", "IV"]:
                        page = 1
                        while True:
                            data = fetcher.get_rank_page(
                                tier=tier, division=division, page=page
                            )
                            # Verify if the division wasn't fully fetched.
                            # If it was, then go to the next iteration.
                            if len(data) > 0:
                                treated_rating = get_rating_list(data, region)
                                insert_player_rating_list(treated_rating)
                                page += 1
                            else:
                                break
                except Exception as e:
                    raise Exception(
                        f"Error occurred while fetching player rating list: {e}"
                    )
            print(
                f"Rating fetching finished for region {region}. Sleeping for 30 minutes."
            )
            time.sleep(1800)
    except Exception as e:
        print(e)


def main_region_fetching(region_list: dict):
    """
    Worker responsible for fetching match history, match data and player information.
    Initializes the sub-regions.

    Args:
        region_list (dict): Dictionary containing the main region as key and it's associated sub-regions as value.{main_region:[sub_regions]}
    """
    # Get the first and only key, which represents the current main region.
    cur_region = next(iter(region_list.keys()))
    try:
        # Create a simple manager worker function to be run with threads.
        def manager():
            """
            Function to run a executor on the sub regions without blocking the main region thread.
            """
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(region_list[cur_region])
            ) as executor:
                list(
                    executor.map(
                        sub_region_fetching, region_list[cur_region], chunksize=1
                    )
                )

        # Start the manager function.
        manager = Thread(target=manager)
        manager.start()

        # Wait for the sub region fetcher to insert any record into the players table.
        # Eventually the sub region fetcher will insert a puuid from it's top challenger.
        while get_next_to_fetch(region_list[cur_region]) is None:
            print(f"Awaiting start point for {cur_region}")
            time.sleep(15)

        print(f"Starting main fetcher {cur_region}")

        # Instanciate the fetcher.
        main_fetcher = MainRegionFetcher(cur_region)

        # Infinite loop for keeping the fetcher running.
        while True:
            print("Starting fetching for the next player...")
            # Get the next player from this region scope.
            next_player = get_next_to_fetch(region_list[cur_region])
            # Initialize the match list as a empty list and it's starting point.
            match_list = []
            list_size = 0
            # Infinite loop for getting all possible matches.
            while True:
                # Get a list of at maximum 100 matches.
                matches = main_fetcher.get_match_list(
                    next_player["puuid"], next_player["lastFetch"], list_size
                )
                # Extend the current match list.
                match_list.extend(matches)
                # Verify if the size of the match list is equal to 100, meaning it's not the end of the list.
                if matches is not None and len(matches) == 100:
                    list_size += 100
                else:
                    break

            # Loop through each match.
            for match in match_list:
                # Verify if the match was already in the database, meaning that it was already treated.
                if match_on_db(match):
                    continue
                # Get the match data from the API.
                match_data = main_fetcher.get_match_data(match)
                # Get the match, player and stats data.
                m_info = get_match_info(match_data)
                if m_info is None:
                    continue
                p_info = get_player_info(match_data)
                p_stats = get_player_stats(match_data)

                # Verify if a player was already on the database before inserting it into the database, so no duplicates can be added.
                new_p_info = []
                for player in p_info:
                    player_exists = update_player_if_exists(
                        player, m_info["matchStart"]
                    )
                    if player_exists == True:
                        continue
                    new_p_info.append(player)
                # Insert all the data in the database.
                insert_player_list(new_p_info)
                insert_match(m_info)
                insert_stats_list(p_stats)
            # Set the current time as the last time the player data was fetched.
            update_last_fetch(next_player["puuid"])
    except Exception as e:
        print(f"Error on main region {cur_region}: {e}")


# Thread pool executor to create the threads for the main regions.
with concurrent.futures.ThreadPoolExecutor(max_workers=len(regions)) as executor:
    executor.map(main_region_fetching, regions)
