from enum import Enum
from collections import Counter
from typing import List
from load_stats import PlayerGameStats

class ScoreType(Enum):
    POINTS = "points"
    GOALS = "goals"
    ASSISTS = "assists"

def calculate_distribution_for_player(score_type: ScoreType,
                                      player_game_stats: List[PlayerGameStats]):
    distribution = Counter()
    score_type_str = score_type.value
    for game_stat in player_game_stats:
        val = game_stat.asdict()[score_type_str]
        distribution[val] += 1
    return distribution
