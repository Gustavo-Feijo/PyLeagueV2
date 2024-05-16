import datetime
from database import rating_up_to_date


# Get rating information from a rating page.
def get_rating_list(rating_response, region, high_rank=False):
    """Function to get the list of ratings for a given league page.

    Args:
        rating_response (Dict OR List[Dict]): Dictionary with the entries of the league as value of key "entries" if it's high rank, else a list of dictionaries with the data.
        region (string): Region that the rating is associated.
        high_rank (bool, optional): Variable to verify if the list is from high rating or not. Defaults to False.

    Returns:
        List[Dict]: Returns the list of dictionaries with the treated data.
    """
    try:
        rating_list = []
        for rating in rating_response["entries"] if high_rank else rating_response:
            new_rating = {
                "tier": rating_response["tier"] if high_rank else rating["tier"],
                "rank": rating["rank"],
                "wins": rating["wins"],
                "losses": rating["losses"],
                "leaguePoints": rating["leaguePoints"],
                "summonerId": rating["summonerId"],
                "region": region,
            }
            if not rating_up_to_date(new_rating):
                rating_list.append(new_rating)

        return rating_list
    except Exception as e:
        raise Exception(f"Error on the treatment of data for rating list: {e}")


# Get very simple match info and let it structured to insert directly into the database.
def get_match_info(data):
    """
    Function to get simplified information from a match.

    Args:
        data (dict): Receives a dict containing the data of a given match.

    Returns:
        dict: Filtered dictionary with useful information from the match.
    """
    try:
        if data["info"]["endOfGameResult"] != "Abort_Unexpected":
            match_info = {
                "gameVersion": data["info"]["gameVersion"],
                "matchId": data["metadata"]["matchId"],
                "matchStart": datetime.datetime.fromtimestamp(
                    data["info"]["gameCreation"] / 1000
                ),
                "matchDuration": data["info"]["gameDuration"],
                "matchWinner": not data["info"]["teams"][0]["win"],
                "matchSurrender": data["info"]["participants"][0][
                    "gameEndedInSurrender"
                ],
                "matchRemake": data["info"]["participants"][0][
                    "gameEndedInEarlySurrender"
                ],
            }
            return match_info
        else:
            return None
    except Exception as e:
        match_id = data["metadata"]["matchId"]
        raise Exception(f"Error on the treatment of data for match {match_id}: {e}")


# Get very simple player info and structure it to insert into the database..
def get_player_info(data):
    """
    Function to get simple player information and structure it.

    Args:
        data (dict): Receives a dict containing the data of a given match.

    Returns:
        List[Dict]: Returns a list of dictionaries, each containing the information about a player that was on a given match.
    """
    try:
        player_array = []
        # Loop through each participant and fetch it's data.
        for participant in data["info"]["participants"]:
            player_info = {
                "puuid": participant["puuid"],
                "summonerId": participant["summonerId"],
                "gameName": participant["riotIdGameName"],
                "tagLine": participant["riotIdTagline"],
                "profileIconId": participant["profileIcon"],
                "summonerLevel": participant["summonerLevel"],
                "region": data["info"]["platformId"],
            }
            player_array.append(player_info)
        return player_array
    except Exception as e:
        raise Exception(f"Error on the treatment of data for player information: {e}")


# Get informations from each player of a game and return it as a array.
def get_player_stats(data):
    """
    Function to get the stats for each player of a game.

    Args:
        data (dict): Receives a dict containing the data of a given match.

    Returns:
        List[Dict]: Returns a list of dictionaries with the stats of each player.
    """
    try:
        player_array = []
        # Loop through each participant and fetch it's data.
        for participant in data["info"]["participants"]:
            player_stats = {
                # Imutable global ID, unique for each account.
                "playerId": participant["puuid"],
                # ID of a given match. Should appear 10 times, one for each player.
                "matchId": data["metadata"]["matchId"],
                "championId": participant[
                    "championId"
                ],  # ID of the champion played by the player.
                # KDA information.
                "kills": participant["kills"],
                "deaths": participant["deaths"],
                "assists": participant["assists"],
                # Gold stats.
                "goldEarned": participant["goldEarned"],
                "goldSpent": participant["goldSpent"],
                # Damage stats.
                "totalDamage": participant["totalDamageDealtToChampions"],
                # Items.
                "item0": participant["item0"],
                "item1": participant["item1"],
                "item2": participant["item2"],
                "item3": participant["item3"],
                "item4": participant["item4"],
                "item5": participant["item5"],
                "item6": participant["item6"],
                # Runes.
                "defense": participant["perks"]["statPerks"]["defense"],
                "flex": participant["perks"]["statPerks"]["flex"],
                "offense": participant["perks"]["statPerks"]["offense"],
                "runeTree": participant["perks"]["styles"][0]["style"],
                "main0": participant["perks"]["styles"][0]["selections"][0]["perk"],
                "main1": participant["perks"]["styles"][0]["selections"][1]["perk"],
                "main2": participant["perks"]["styles"][0]["selections"][2]["perk"],
                "main3": participant["perks"]["styles"][0]["selections"][3]["perk"],
                "subTree": participant["perks"]["styles"][1]["style"],
                "sub1": participant["perks"]["styles"][1]["selections"][0]["perk"],
                "sub2": participant["perks"]["styles"][1]["selections"][1]["perk"],
                # Spells:
                "spell1": participant["summoner1Id"],
                "spell2": participant["summoner2Id"],
                # Farm and vision stats.
                "neutralMinionsKilled": participant["neutralMinionsKilled"],
                "totalMinionsKilled": participant["totalMinionsKilled"],
                "totalCs": int(
                    participant["totalMinionsKilled"]
                )  # Calculation between the total minions and neutral minions killed.
                + int(participant["neutralMinionsKilled"]),
                "csPerMin": (
                    int(participant["totalMinionsKilled"])
                    + int(participant["neutralMinionsKilled"])
                )
                / (int(data["info"]["gameDuration"]) / 60),
                # Vision stats.
                "visionScore": participant["visionScore"],
                "controlWardsPlaced": participant["challenges"]["controlWardsPlaced"],
                "wardsPlaced": participant["wardsPlaced"],
                "wardsKilled": participant["wardsKilled"],
                # Game informations.
                "teamPosition": participant["teamPosition"],
                # Player team, if it equals 200, return true, otherwise 0. Blue team is stored as 0 and red as 1 on the Database.
                "team": participant["teamId"] == 200,
            }
            player_array.append(player_stats)
        return player_array
    except Exception as e:
        raise Exception(f"Error on the treatment of data for player stats list: {e}")
