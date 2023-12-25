import csv
from typing import Dict


def load_player_ids(csv_file) -> Dict[int, str]:
    player_id_to_name = {}
    with open(csv_file, 'r' ) as f:
        reader = csv.DictReader(f, delimiter=",", quoting=csv.QUOTE_NONE, skipinitialspace=True)
        for line in reader:
            player_id_to_name[int(line["id"])] = line["player_name"]

    return player_id_to_name
