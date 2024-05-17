# PYLEAGUE V2

Improvement of my first project of fetching data from the Riot API.

## Improvements

- Added support for fetching data from all the regions, improaving drastically the amount of data fetched.
- Use of multiple threads to improve perfomance of fetching, with a thread for each region running in parallel.
- Use of SQL Alchemy ORM to improve code quality.
- Use of classes for better readability and separation of concerns.

## Usage

A .env file containing the API KEY and database connection ur.
The only requirements to start the project are:

1. The connection to the Database is required and a valid api key needs to be provided.
2. Installl therequirements from requirements.txt

## Structure

The structure of the code currently is composed of several utilities.

The fetching is done by three classes, one being the base fetching class, with rate limiting functionality and the pure fetching, it's instanciated inside other two classes.
The sub region and main region fetchers are classes that instanciate the base fetching class and use it to fetch data from the urls that are constructed by it's methods.
A UML diagram containing the structure of the classes is on the project directory. The region attribute on the main and sub region are not used as attributes, but instead are passed to the BaseFetching class constructor.
A Flowchart of the code is also on the project directory, but the Flowchart is not very precise, yet to be redone.

The basic control flow goes like:
Start 4 threads for the main regions, pass the sub regions inside a dictionary.
Inside each thread create threads for each sub region passed in the dictionary.
Now the code flow splits in two parts, sub regions and main regions.

The main region is focused on getting player information and match data, while the sub region is focused on getting rating information.
The main region needs a starting point for the match fetching, verifying if there is a starting point every 15 seconds.
The sub region starts by fetching the high elo ratings and inserting then into the database. During the high elo rating fetching it verifies if there is any player from the region on the player table.

If there isn't any player from the regions related to a main region, then the main region doesn't have a starting point. In that case, the sub region gets the player puuid and insert into the player table to act as a starting point for the main region.

After inserting the main region starting point, the sub region goes on into fetching all high elo pages, then fetchs all other rating pages from the remaining tiers and divisions, then, after getting all rating information, goes into sleep for 30 minutes, after that reinitiates the process.
Ps: Before each insertion of rating verifies that the rating has changed, if not, doesn't insert it.

The main region find it's starting point after the sub regions efforts, then proceeds to get data from each player based on the last time the data was fetched.
Get the player puuid from the database, then get the previous match list and it's data, treating it and inserting into the database while avoiding duplicates.
The main region is supposed to keep going indefinitely.

### TODO:

Multiple adjustments could be done to the code to improve it, some as follows:

- Add a stop condition to the code, in order to avoid leaving at the database writing and then not fetch the remaining data of a match.
- Add additional modules for different tasks, such as data analysis with Pandas, graph generation, etc.
- Implement Match V5 timeline.
- Improve treatment of errors.
- Implement asyncio and aiohttp. Currently use is reliable on the requests slow speed to not hit the 1s rate limit, but also it being fast enough to hit the 2 minutes rate limit. This can lead to perfomance issues if a better API key is provided. The best approach is to use asyncio with rate limits to not hit the rate limit, but also be able to handle higher number of requests per second.
- Improve database structure, specially on the stats table, with items, runes and spells being not treated in the best way possible. Migrating to postgres to use arrays or using mysql JSON could improve the structure.
- Improve some logic, like main region fetching being responsible for fetching match data from all regions, add a mechanism to make it get data from all regions in a more consistent way.
