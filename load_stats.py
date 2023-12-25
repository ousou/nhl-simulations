import json
import urllib.request, urllib.error
from dataclasses import dataclass, asdict
from datetime import datetime

NHL_GAMES_IN_SEASON = 82


def _load_data_from_nhl_api_url(url):
    request = urllib.request.Request(url)
    request.add_header("User-Agent", "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0")
    with urllib.request.urlopen(request) as u:
        return json.loads(u.read().decode())


@dataclass
class TeamRecord:
    id: int
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


def load_standings():
    with urllib.request.urlopen("http://statsapi.web.nhl.com/api/v1/standings") as u:
        return json.loads(u.read().decode())

def player_to_team(player_id):
    url = f"http://statsapi.web.nhl.com/api/v1/people/{player_id}"
    with urllib.request.urlopen(url) as u:
        player_stats = json.loads(u.read().decode())
    return player_stats["people"][0]["currentTeam"]["id"]

def player_stats_for_season(player_id, season, team_records):
    team_id = player_to_team(player_id)
    games_remaining = NHL_GAMES_IN_SEASON - team_records[team_id].games_played
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



def load_team_records(standings):
    """
    Loads current records for each team.
    :param: standings: Dict containing full league standings
    :return: Dict team id -> team record
    """
    team_records = {}
    for division in standings["records"]:
        for team in division["teamRecords"]:
            team_record = TeamRecord(id=team["team"]["id"],
                                     name=team["team"]["name"],
                                     last_updated=datetime.strptime(team["lastUpdated"],
                                                                    "%Y-%m-%dT%H:%M:%SZ"),
                                     wins=team["leagueRecord"]["wins"],
                                     losses=team["leagueRecord"]["losses"],
                                     ot_losses=team["leagueRecord"]["ot"],
                                     games_played=team["gamesPlayed"],
                                     points=team["points"],
                                     goals_for=team["goalsScored"],
                                     goals_against=team["goalsAgainst"])
            team_records[team_record.id] = team_record
    return team_records

def load_player_logs_for_regular_season(player_id, season):
    url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season}/2"
    #url = f"http://statsapi.web.nhl.com/api/v1/people/{player_id}/stats?stats=gameLog&season={season}"
    raw_log = _load_data_from_nhl_api_url(url)
    games = []
    for game_log in raw_log["gameLog"]:
        games.append(PlayerGameStats(player_id=player_id,
                                     game_id=game_log["gameId"],
                                     date=datetime.strptime(game_log["gameDate"], "%Y-%m-%d"),
                                     goals=game_log["goals"],
                                     assists=game_log["assists"],
                                     points=game_log["points"]))
    return games



if __name__ == '__main__':
    #standings = load_standings()
    #team_records = load_team_records(standings)
    mcdavid_logs = load_player_logs_for_regular_season(8478402, 20212022)
    print("mcdavid_logs", mcdavid_logs)
    import distributions
    dist = distributions.calculate_distribution_for_player(distributions.ScoreType.GOALS, mcdavid_logs)
    print("dist",dist)
    #mcdavid_stats = player_stats_for_season(8477500, 20222023, team_records)
    #print("mcdavid_stats", mcdavid_stats)
    #mcdavid_team_id = player_to_team(8478402)
    #print("mcdavid team id", mcdavid_team_id)
    #print("mcdavid team name", team_records[mcdavid_team_id].name)
