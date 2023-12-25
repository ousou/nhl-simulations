import random
from collections import Counter
from distributions import ScoreType


def player_score_simulation(player_ids, player_stats,
                            player_distribution_lists,
                            score_type: ScoreType,
                            player_game_played_prob):
    assert set(player_ids) == set(player_stats.keys())
    assert set(player_ids) == set(player_distribution_lists.keys())
    total_score_for_player = Counter()
    for player_id in player_ids:
        total_score_for_player[player_id] = _simulate_season_score_for_player(
            player_distribution_list=player_distribution_lists[player_id],
            player_current_score=player_stats[player_id].asdict()[score_type.value],
            player_games_left=player_stats[player_id].games_remaining,
            player_game_played_prob=player_game_played_prob[player_id]
        )
    return total_score_for_player


def convert_counter_to_list_distribution(counter_distribution):
    cd_list = []
    for score, amount in counter_distribution.items():
        for _ in range(amount):
            cd_list.append(score)
    assert len(cd_list) == sum(counter_distribution.values())
    return cd_list

def _simulate_one_game(player_distribution_list):
    return random.choice(player_distribution_list)

def _simulate_season_score_for_player(player_distribution_list, player_current_score,
                                      player_games_left, player_game_played_prob):
    player_total_score = player_current_score
    for _ in range(player_games_left):
        if random.random() < player_game_played_prob:
            player_total_score += _simulate_one_game(player_distribution_list)
    return player_total_score

def simulate_rocket_richard(simulations=10000):
    score_type = ScoreType.GOALS
    import data_loader
    player_ids = data_loader.load_player_ids("nhl_player_ids_top_50_goal_scorers_20231225.csv")
    print("player_ids", player_ids)
    import load_stats
    team_records = load_stats.load_team_records()

    player_game_logs_this_season = {}

    player_game_logs_last_season = {}

    for player_id in player_ids:
        print(f"Loading game logs for player_id {player_id}")
        this_season = load_stats.load_player_logs_for_regular_season(player_id, 20232024)
        player_game_logs_this_season[player_id] = this_season
        prev_season = load_stats.load_player_logs_for_regular_season(player_id, 20222023)
        player_game_logs_last_season[player_id] = prev_season


    player_stats = {}
    for player_id in player_ids:
        print(f"Loading data for player_id {player_id}")
        player_stats[player_id] = load_stats.player_stats_for_season(player_id=player_id,
                                                                     season=20232024,
                                                                     team_records=team_records,
                                                                     player_logs_for_season=player_game_logs_this_season[player_id])


    import distributions
    player_distribution_list = {
        player_id: convert_counter_to_list_distribution(
            distributions.calculate_distribution_for_player(score_type=score_type,
                                                            player_game_stats=player_game_logs_this_season[player_id] + player_game_logs_last_season[player_id])
        )

        for player_id in player_ids
    }

    winners = Counter()

    player_game_played_prob = {player_id: 1. for player_id in player_ids}
    # Matthews is injured a bit more often
    player_game_played_prob[8479318] = 0.92

    print(f"Running {simulations} simulations")
    for _ in range(simulations):
        result = player_score_simulation(player_ids=player_ids,
                                         player_stats=player_stats,
                                         player_distribution_lists=player_distribution_list,
                                         score_type=score_type,
                                         player_game_played_prob=player_game_played_prob)
        top_results = list(result.most_common(10))
        tied_players = [top_results[0][0]]
        highest_score = top_results[0][1]
        for _, (player, score) in enumerate(top_results[1:]):
            if score == highest_score:
                tied_players.append(player)
        tied_players = [player_ids[p] for p in tied_players]
        if len(tied_players) > 1:
            tied_str = "-".join(tied_players)
            winner = "tie-" + tied_str
        else:
            winner = tied_players[0]
        winners[winner] += 1
    return winners

if __name__ == '__main__':
    winners = simulate_rocket_richard(simulations=10000)
    print("Top winners", winners.most_common(1000))

