import json
import urllib.request, urllib.error
from dataclasses import dataclass, asdict
from datetime import datetime
import os

NHL_GAMES_IN_SEASON = 82
CURRENT_SEASON = 20232024
CACHE_DIR = "data_cache/"

def _load_data_from_nhl_api_url(url):
    request = urllib.request.Request(url)
    request.add_header("User-Agent", "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0")
    with urllib.request.urlopen(request) as u:
        return json.loads(u.read().decode())


@dataclass
class TeamRecord:
    id: int
    abbrev: str
    name: str
    wins: int
    losses: int
    ot_losses: int
    games_played: int
    points: int
    goals_for: int
    goals_against: int
    last_updated: datetime

    def asdict(self):
        return asdict(self)

@dataclass
class PlayerGameStats:
    player_id: int
    game_id: int
    date: datetime
    goals: int
    assists: int
    points: int

    def asdict(self):
        return asdict(self)


@dataclass
class PlayerStats:
    player_id: int
    games_played: int
    goals: int
    assists: int
    points: int
    games_remaining: int
    team_id: int

    def asdict(self):
        return asdict(self)


def load_team_abbrev_to_id():
    url = f"https://api.nhle.com/stats/rest/en/team/"
    data = _load_data_from_nhl_api_url(url)
    team_abbrev_to_id = {}
    for team in data["data"]:
        team_abbrev_to_id[team["triCode"]] = team["id"]
    return team_abbrev_to_id


def load_standings():
    current_date = datetime.strftime(datetime.now(), "%Y-%m-%d")
    url = f"https://api-web.nhle.com/v1/standings/{current_date}"
    return _load_data_from_nhl_api_url(url)

def player_to_team(player_id):
    url = f"https://api-web.nhle.com/v1/player/{player_id}/landing/"
    data = _load_data_from_nhl_api_url(url)
    return data["currentTeamId"]

def player_stats_for_season(player_id, season, team_records, player_logs_for_season=None):
    team_id = player_to_team(player_id)
    games_remaining = NHL_GAMES_IN_SEASON - team_records[team_id].games_played
    if player_logs_for_season is None:
        player_logs_for_season = load_player_logs_for_regular_season(player_id=player_id,
                                                                     season=season)
    current_stats = PlayerStats(
        player_id=player_id,
        games_played=len(player_logs_for_season),
        goals=sum(pl.goals for pl in player_logs_for_season),
        assists=sum(pl.assists for pl in player_logs_for_season),
        points=sum(pl.points for pl in player_logs_for_season),
        games_remaining=games_remaining,
        team_id=team_id
    )

    return current_stats



def load_team_records():
    """
    Loads current records for each team.
    :return: Dict team id -> team record
    """
    standings = load_standings()
    team_abbrev_to_id = load_team_abbrev_to_id()
    team_records = {}
    for team in standings["standings"]:
        team_record = TeamRecord(id=team_abbrev_to_id[team["teamAbbrev"]["default"]],
                                 abbrev=team["teamAbbrev"]["default"],
                                 name=team["teamName"]["default"],
                                 last_updated=datetime.strptime(team["date"],
                                                                "%Y-%m-%d"),
                                 wins=team["wins"],
                                 losses=team["losses"],
                                 ot_losses=team["otLosses"],
                                 games_played=team["gamesPlayed"],
                                 points=team["points"],
                                 goals_for=team["goalFor"],
                                 goals_against=team["goalAgainst"])
        team_records[team_record.id] = team_record
    return team_records

def load_player_logs_for_regular_season(player_id, season):
    url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season}/2"

    cache_file = f"player_logs_{player_id}_{season}"
    if season == CURRENT_SEASON:
        cache_file += f"_{datetime.strftime(datetime.now(), '%Y-%m-%d')}"
    cache_file += ".json"

    raw_log = _load_from_cache(cache_file)
    if raw_log is None:
        raw_log = _load_data_from_nhl_api_url(url)
        _save_to_cache(raw_log, cache_file)

    games = []
    for game_log in raw_log.get("gameLog", []):
        games.append(PlayerGameStats(player_id=player_id,
                                     game_id=game_log["gameId"],
                                     date=datetime.strptime(game_log["gameDate"], "%Y-%m-%d"),
                                     goals=game_log["goals"],
                                     assists=game_log["assists"],
                                     points=game_log["points"]))
    return games

def _load_from_cache(file_name):
    if os.path.isfile(CACHE_DIR + file_name):
        with open(CACHE_DIR + file_name) as f:
            return json.load(f)

    return None

def _save_to_cache(data, file_name):
    with open(CACHE_DIR + file_name, "w") as f:
        json.dump(data, f)

if __name__ == '__main__':
    team_records = load_team_records()
    print("team_records", team_records)
    mcdavid_logs = load_player_logs_for_regular_season(8478402, 20212022)
    print("mcdavid_logs", mcdavid_logs)
    import distributions
    dist = distributions.calculate_distribution_for_player(distributions.ScoreType.GOALS, mcdavid_logs)
    print("dist",dist)
    mcdavid_stats = player_stats_for_season(8477500, 20222023, team_records)
    print("mcdavid_stats", mcdavid_stats)
    mcdavid_team_id = player_to_team(8478402)
    print("mcdavid team id", mcdavid_team_id)
    print("mcdavid team name", team_records[mcdavid_team_id].name)
