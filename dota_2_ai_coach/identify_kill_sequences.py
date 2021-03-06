import pandas as pd
from datetime import datetime
import hana_connector


def get_kill_sequences(matchID):
    """
    Finds kill sequences where numerous heros got killed within 
    a time frame of 18 seconds
    Args:
        match_id: id of a match in database
    Returns:
        Pandas dataframe with scenes starts, end times
    """
    hana = hana_connector.HanaConnector()
    connection = hana.connect()
    print("asdasd")
    combat_log_only_kills = pd.read_sql("""
    SELECT
        *
    FROM
        "DOTA2_TI8"."combatlog"
    WHERE
        "match_id" = {matchID}
        AND
        "type" = 'DOTA_COMBATLOG_DEATH'
        AND
        "isTargetHero" = TRUE
    ORDER BY
        "tick"
        ASC
    """.format(matchID=matchID), connection)

    hana.close()

    combat_log_only_kills["adj_tick"] = combat_log_only_kills["tick"] - \
        (combat_log_only_kills["tick"] - combat_log_only_kills["game_tick"])
    combat_log_only_kills["adj_tick_prior"] = combat_log_only_kills["adj_tick"].shift(
        1)
    combat_log_only_kills["tick_delta"] = combat_log_only_kills["adj_tick"] - \
        combat_log_only_kills["adj_tick_prior"]

    curr_tuple = []
    number_kills = 0
    kill_sequences = []

    for index, kill in combat_log_only_kills.iterrows():
        # curr_kill_xy = [kill['locationX_target'], kill['locationY_target']]
        if number_kills == 0:
            curr_tuple.append(kill['adj_tick'])
            number_kills = number_kills + 1
        elif kill['tick_delta'] <= 540:
            number_kills = number_kills + 1
        elif kill['tick_delta'] > 540:
            if number_kills > 2:
                curr_tuple.append(kill['adj_tick_prior'])
                kill_sequences.append(curr_tuple)
                number_kills = 1
                curr_tuple = [kill['adj_tick']]
            else:
                curr_tuple = [kill['adj_tick']]
                number_kills = 1

    kill_sequences_sec = pd.DataFrame()
    start_times = []
    end_times = []
    for start, end in kill_sequences:
        start_times.append(start / 30 - 15)  # add 3 as buffer
        end_times.append(end / 30 + 5)  # add 3 as buffer
    
    kill_sequences_sec['tick_start'] = start_times
    kill_sequences_sec['datetime_start'] = kill_sequences_sec['timestamp_start'].apply(
        lambda x: datetime.utcfromtimestamp(x).isoformat())
    kill_sequences_sec['tick_end'] = end_times
    kill_sequences_sec['datetime_end'] = kill_sequences_sec['timestamp_end'].apply(
        lambda x: datetime.utcfromtimestamp(x).isoformat())
    kill_sequences_sec['type'] = "KILL_SEQUENCE"

    return kill_sequences_sec



# print(identify_kill_sequences(4074440208))
