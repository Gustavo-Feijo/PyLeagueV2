import os
from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    DateTime,
    Enum,
    Integer,
    String,
    SmallInteger,
    ForeignKey,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker
from sqlalchemy.sql import func
from sqlalchemy import and_

# Load the dotenv and create a logger
load_dotenv("./credentials.env")

# Create the SQL Alchemy ORM.
engine = create_engine(os.getenv("CONNECTION_STRING"), echo=False, pool_size=20)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
Base = declarative_base()


# Class model for rating related data.
class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    tier = Column(
        Enum(
            "IRON",
            "BRONZE",
            "SILVER",
            "GOLD",
            "PLATINUM",
            "EMERALD",
            "DIAMOND",
            "MASTER",
            "GRANDMASTER",
            "CHALLENGER",
        )
    )
    rank = Column(Enum("IV", "III", "II", "I"))
    summonerId = Column(String(63))
    leaguePoints = Column(SmallInteger)
    wins = Column(SmallInteger)
    losses = Column(SmallInteger)
    region = Column(String(4))
    fetchTime = Column(DateTime, default=func.now())


# Class model for player info related data.
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    puuid = Column(String(78), nullable=False, unique=True)
    summonerId = Column(String(63))
    gameName = Column(String(50))
    tagLine = Column(String(5))
    summonerLevel = Column(SmallInteger)
    profileIconId = Column(SmallInteger)
    lastMatchFetch = Column(DateTime, default="2024-05-1 00:00:01")
    region = Column(String(4))
    stats = relationship("Stats", back_populates="player")


# Class model for match related data.
class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    gameVersion = Column(String(15))
    matchId = Column(String(20))
    matchStart = Column(DateTime)
    matchDuration = Column(Integer)
    matchWinner = Column(Boolean)
    matchSurrender = Column(Boolean)
    matchRemake = Column(Boolean)
    stats = relationship("Stats", back_populates="match")


# Class model for stats related data.
class Stats(Base):
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    playerId = Column(Integer, ForeignKey("players.id"))
    matchId = Column(Integer, ForeignKey("matches.id"))
    championId = Column(SmallInteger)
    kills = Column(SmallInteger)
    deaths = Column(SmallInteger)
    assists = Column(SmallInteger)
    goldEarned = Column(Integer)
    goldSpent = Column(Integer)
    totalDamage = Column(Integer)
    totalCs = Column(Integer)
    spell1 = Column(Integer)
    spell2 = Column(Integer)
    item0 = Column(SmallInteger)
    item1 = Column(SmallInteger)
    item2 = Column(SmallInteger)
    item3 = Column(SmallInteger)
    item4 = Column(SmallInteger)
    item5 = Column(SmallInteger)
    item6 = Column(SmallInteger)
    defense = Column(SmallInteger)
    flex = Column(SmallInteger)
    offense = Column(SmallInteger)
    runeTree = Column(SmallInteger)
    main0 = Column(SmallInteger)
    main1 = Column(SmallInteger)
    main2 = Column(SmallInteger)
    main3 = Column(SmallInteger)
    subTree = Column(SmallInteger)
    sub1 = Column(SmallInteger)
    sub2 = Column(SmallInteger)
    spell1 = Column(SmallInteger)
    spell2 = Column(SmallInteger)
    visionScore = Column(SmallInteger)
    controlWardsPlaced = Column(SmallInteger)
    wardsPlaced = Column(SmallInteger)
    wardsKilled = Column(SmallInteger)
    teamPosition = Column(
        Enum("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY", "Invalid", "")
    )
    team = Column(Boolean)
    player = relationship("Player", back_populates="stats")
    match = relationship("Match", back_populates="stats")


Base.metadata.create_all(engine)


def insert_data_list(data, model):
    """Generic function for inserting lists of data into the database.

    Args:
        data (List[Dict]): List of dictionaries to be inserted into the passed model.
        model (Class): Database model from the ORM.

    Raises:
        Exception: Raises an exception showing in which model the error occurred.
    """
    session = Session()
    try:
        session.bulk_insert_mappings(model, data)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Error inserting data on model: {model}, error: {e}")
    finally:
        session.close()


def insert_player_rating_list(data_list):
    """Wrapper for inserting a list of ratings into the database.

    Args:
        data_list (List[Dict]): List of dictonaries containing the treated rating data.
    """
    insert_data_list(data_list, Rating)


def insert_match(data):
    """Function to insert a single match info into the database.

    Args:
        data (Dict): Dictionary containing the data to insert into the database.

    Raises:
        Exception: Exception showing where the error happened.
    """
    session = Session()
    try:
        session.add(Match(**data))
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Error occurred on match insertion: {e}")
    finally:
        session.close()


def insert_player_list(data_list):
    """Wrapper for inserting a list of players into the database.

    Args:
        data_list (List[Dict]): List of dictonaries containing the treated player data.
    """
    insert_data_list(data_list, Player)


def insert_stats_list(data_list):
    """
    Function to get the player id and match id as integers from the database.
    Wrapper for inserting data into the database.

    Args:
        data_list (List[Dict]): List of dictonaries containing the treated stats data.
    """
    for stat in data_list:
        stat["playerId"] = get_player_id(stat["playerId"])
        stat["matchId"] = get_match_id(stat["matchId"])
    insert_data_list(data_list, Stats)


def safe_query(func):
    """Decorator for safe queries. Assure that the queries will log an error."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            raise Exception(f"An error occurred in {func.__name__}: {e}")

    return wrapper


@safe_query
def get_next_to_fetch(regions):
    """Function to get the next player to fetch the data from.

    Args:
        regions (List[String]): List of regions that the player to be fetched can be.

    Returns:
        Dict OR None: Returns a dict containing the player puuid and lastMatchFetch if the data was found. Otherwise, returns None.
    """
    with Session() as session:
        player = (
            session.query(Player)
            .order_by(Player.lastMatchFetch)
            .filter(Player.region.in_(regions))
            .first()
        )
        return (
            {"puuid": player.puuid, "lastFetch": player.lastMatchFetch}
            if player
            else None
        )


@safe_query
def get_player_id(puuid):
    """Function to return a player id based on it's puuid.
    Assumes the player is already registered since this function is only called after player insertion.

    Args:
        puuid (String): Unique identifier for the player.

    Returns:
        Number: Player id on the Player's table.
    """
    with Session() as session:
        player = session.query(Player).filter(Player.puuid == puuid).first()
        return player.id


@safe_query
def get_match_id(match_id):
    """Function to return a match id based on it's match id.
    Assumes the match is already registered since this function is only called after match insertion.

    Args:
        puuid (String): Unique identifier for the match.

    Returns:
        Number: Match id on the Matches table.
    """
    with Session() as session:
        match = session.query(Match).filter(Match.matchId == match_id).first()
        return match.id


@safe_query
def update_last_fetch(puuid):
    """Function to update the last fetch date from a given player to set it as the current time.
    Assures that the same player will not be fetched unless there is no other player whose data need to be fetched first.

    Args:
        puuid (String): Unique identifier for the player that will be updated.
    """
    with Session() as session:
        player = session.query(Player).filter(Player.puuid == puuid).first()
        player.lastMatchFetch = func.now()
        session.commit()


@safe_query
def update_player_if_exists(player, matchDate):
    """Function to verify if a player is on the database.

    Args:
        puuid (dict): Dictionary containing the player's data

    Returns:
        dict: Returns a dictionary containing the player information if the player is on the database.
    """
    with Session() as session:
        player_exists = (
            session.query(Player).filter(Player.puuid == player["puuid"]).first()
        )
        if not player_exists:
            return None

        if player_exists.lastMatchFetch > matchDate:
            # Update the player's information
            player_exists.summonerId = player["summonerId"]
            player_exists.gameName = player["gameName"]
            player_exists.tagLine = player["tagLine"]
            player_exists.summonerLevel = player["summonerLevel"]
            player_exists.profileIconId = player["profileIconId"]
            player_exists.lastMatchFetch = matchDate
            player_exists.region = player["region"]
            session.commit()
        return True


@safe_query
def match_on_db(match_id):
    """Function to verify if a match is on the database.

    Args:
        match_id (String): Unique identifier for the match.

    Returns:
        bool: Returns True if the match is on the database, else False.
    """
    with Session() as session:
        match_exists = session.query(Match).filter(Match.matchId == match_id).first()
        return True if match_exists else False


@safe_query
def get_player_from_region_count(region):
    """Function to get the count of players on from a given region.

    Args:
        region (String): Region to get the count.

    Returns:
        Number: Count of players on the given region.
    """
    with Session() as session:
        player_count = session.query(Player).filter(Player.region == region).count()
        return player_count


@safe_query
def main_region_is_started(region_list):
    """Function to check if the main region is started.

    Args:
        region_list (List[String]): List of regions associated with the main region. Gets the count of all players that are from any of the regions.

    Returns:
        bool: Returns True if any record of a player of the passed regions is found, False otherwise.
    """
    with Session() as session:
        region_count = (
            session.query(Player).filter(Player.region.in_(region_list)).count()
        )
        return True if region_count > 0 else False


def insert_starting_point(player, region):
    """Function to insert a empty starting point for the main region fetching.

    Args:
        player (dict): Dictionary with simple player data.
        region (string): Region where the player will be inserted.
    """
    new_player = {
        "puuid": player["puuid"],
        "profileIconId": player["profileIconId"],
        "region": region,
        "summonerId": player["id"],
    }
    insert_player_list([new_player])


@safe_query
def rating_up_to_date(rating):
    with Session() as session:
        last_rating = (
            session.query(Rating)
            .filter(Rating.summonerId == rating["summonerId"])
            .order_by(Rating.fetchTime)
            .first()
        )
        if last_rating:
            if (
                last_rating.leaguePoints == rating["leaguePoints"]
                and last_rating.wins == rating["wins"]
                and last_rating.losses == rating["losses"]
            ):
                return True
        return False
