import sqlite3
import os
import sys
import re
from collections import defaultdict
import math
from statistics import mean

sys.path.append(os.path.join(".", "pythonScripts"))  # so Python can find the module
from GameInfo import *
from GeneralSQL import *
from Helpers import *
from GetTracks import *
import GameSearch

def merge_tracks(conn, track_id_remove, track_id_keep):
    # edit all track_ids in plays that mach track_id_from and make them track_id_to, and then delete the track with id of track_id_from
    c = conn.cursor()
    c.execute("""
        SELECT id, name FROM tracks
        WHERE id = ? OR id = ?
    """, (track_id_remove, track_id_keep))
    rows = c.fetchall()
    print(rows)
    try:
        c.execute("""
            SELECT MAX(sub_track)
            FROM tracks 
            WHERE id=? OR id=?
        """, (track_id_remove, track_id_keep))
        sub_track = c.fetchone()[0]

        name_to   = rows[0][1] if rows[0][0] == track_id_remove else rows[1][1]
        name_from = rows[1][1] if rows[0][0] == track_id_remove else rows[0][1]
        i = input(f"Double check: Replace \"{name_to}\" with \"{name_from}\"? {'It is a sub track. ' if sub_track else ''}(Y/n): ")
        if(i.lower().rstrip() == "y"):
            c.execute("""
                UPDATE plays
                SET track_id = ?
                WHERE track_id = ?
            """, (track_id_keep, track_id_remove))

            c.execute("""
                DELETE FROM tracks
                WHERE id = ?
            """, (track_id_remove, ))

            c.execute("""
                UPDATE tracks
                SET sub_track = ?
                WHERE id = ?
            """, (sub_track, track_id_keep))

            conn.commit()
            
            print("Processed")
            return
        else:
            print("Canceled.")
    except Exception as e:
        print("ID missing, already deleted?")



def get_sub_tracks(conn, game_name):
    c = conn.cursor()
    
    game_id, game_name = get_id_and_formatted_game_name(conn, game_name)
        
    c.execute("""
        SELECT name
        FROM tracks
        WHERE game_id = ? AND sub_track = 1
    """, (game_id, )) #get track names
    
    sub_track_names = sorted([x[0] for x in c.fetchall()])
    
    print("sub tracks for", game_name, sub_track_names)
    
def get_episode(conn, episode, mode=Play_Mode.REGULAR):
    c = conn.cursor()

    c.execute("""
        SELECT p.track_num, t.name, g.name
        FROM plays p
        JOIN tracks t ON p.track_id = t.id
        JOIN games g ON t.game_id = g.id
        WHERE p.episode = ? AND p.mode = ?
    """, (episode, mode.value))
    
    tracks = c.fetchall()
    
    print(f"Episode {episode}, in {mode}")
    print("=" * len(f"Episode {episode}, in {mode}"))
    L = [""]
    if(mode == Play_Mode.FINAL_CHASE and (1 in [l[0] for l in tracks][1:])):
        L = ["\n(Chaser)\n\n", "\n(Players)\n\n"]
    elif(mode == Play_Mode.SPECIAL_EPISODE):
        L = ["\nTeam Skunny VS Team Bubsy\n\n", "\nTeam Banjo VS Team Plok\n\n", "\nTeam Banjo VS Team Skunny\n\n", "\nTeam Plok VS Team Bubsy\n\n", "\nTeam Bubsy VS Team Banjo\n\n", "\nTeam Plok VS Team Skunny\n\n"]

    for id, song, game in tracks:
        if id == 1:
            print(L.pop(), end = '')
        prev_id = id
        print(f"{id}\t{game} - {song}")
        
    return tracks
    
def hail_mary_game(conn, game_id):
    c = conn.cursor()

    c.execute(""" 
        SELECT expansion_game_id
        FROM games
        WHERE id = ?
    """, (game_id, ))
    expansion_id = c.fetchone()[0]
    if(expansion_id): #swap to base game id if looking at expansion
        game_id = expansion_id

    c.execute("""
        SELECT name, effective_last_play, has_played, place
        FROM hail_mary
        WHERE id = ?
    """, (game_id,))
    game_name, last_play, has_played, place = c.fetchone()
    
    msg = f"**{game_name}**\n"
    if(has_played == 1):
        if place > 50:
            msg += f"Last Played: Episode **#{last_play}**. It is {place - 50} games from entering Hail Mary."
        else:
            msg += f"Last Played: Episode **#{last_play}**. It is in Hail Mary."
    else:
        if place > 50:
            msg += f"Added to the ChaseVGM on episode **#{last_play}**. It is {place - 50} games from entering Hail Mary."
        else:
            msg += f"Added to the ChaseVGM on episode **#{last_play}**. It is in Hail Mary."
    return msg

def hail_mary(conn, count=50):
    c = conn.cursor()

    c.execute("""
        SELECT name, effective_last_play, has_played
        FROM hail_mary
        ORDER BY effective_last_play
        LIMIT ?;
    """, (count, ))

    results = c.fetchall()  # list of tuples: (name, last_rr_play, has_played)
    results.sort(key=lambda x: x[1])
    
    msg = ""
    msg += (f"Hail Mary Games (Last Played)/[Unplayed]\n\n")
    for game, last_play, has_played in results:
        last_play_formatting = f"({last_play})" if has_played else f"[{last_play}]"
        msg += f"{last_play_formatting} {game}\n"
    return msg

def dead_games(conn, count=50):
    c = conn.cursor()

    c.execute("""
        SELECT name, effective_last_play, has_played
        FROM dead_games
        ORDER BY effective_last_play
        LIMIT ?;
    """, (count, ))

    results = c.fetchall()  # list of tuples: (name, last_rr_play, has_played)
    results.sort(key=lambda x: x[1])
    
    msg = ""
    msg += (f"Dead Games (Most Recent Play)/<Added to Chase>\n\n")
    for game, last_play, has_played in results:
        last_play_formatting = f"({last_play})" if has_played else f"[{last_play}]"
        msg += f"{last_play_formatting} {game}\n"
    return msg

def points(conn, player):
    c = conn.cursor()

    try:
        ID = str(player.id)
    except:
        ID = player

    c.execute("""
        SELECT name, points, regular_subs, micro_subs, chaser
        FROM players
        WHERE discord_id = ?
    """, (ID, ))
    row = c.fetchone()

    if not row:
        return f"Cannot find **{player}**. Please send this over to Mia (the scoreboard name and discord name) if you think this is an error."

    name, points, regular_subs, micro_subs, chaser = row

    msg = f"**{name}**\nThis "
    if chaser == True:
        msg += f"Chaser has {regular_subs} submission" + ("s" if (regular_subs != 1 and regular_subs) else "")
    else:
        subCost = (int(regular_subs)+1) * 100
        msg += f"player has **{points}** total points, and needs {subCost} for their next submission.\nThey currently have {regular_subs} submission" + ("s" if (regular_subs != 1 and regular_subs) else "")

    return(msg + (f" and {micro_subs} micro submission" if micro_subs else "") + ("s" if (micro_subs != '1') and (micro_subs) else "") + ".")

def submissions(conn, player):
    c = conn.cursor()

    try:
        ID = str(player.id)
    except:
        ID = player

    c.execute("""
        SELECT id, name, regular_subs, micro_subs, chaser
        FROM players
        WHERE discord_id = ?
    """, (ID, ))
    row = c.fetchone()

    if not row:
        return f"Cannot find **{player}**. Please send this over to Mia (the scoreboard name and discord name) if you think this is an error."

    player_id, name, regular_subs, micro_subs, chaser = row
    submissions = (regular_subs if regular_subs is not None else 0) + (micro_subs if micro_subs is not None else 0)

    c.execute("""
        SELECT name, subtype
        FROM base_game_debuts
        WHERE submitter_id = ?
        ORDER BY debut IS NULL, debut
    """, (player_id, ))
    sub_list = c.fetchall()

    msg = f"**{name}**\nThis "
    if chaser == True:
        msg += f"Chaser "
    else:
        msg += f"player "

    if(submissions == 0):
        msg += f"has no submissions :("
        return msg

    msg += f"has the following {submissions} submission" + ("s" if (submissions != 1 and submissions) else "") + ":\n```\n"
    for i, sub in enumerate(sub_list):
        sub_name, sub_type = sub
        if(submissions >= 10):
            msg += f"({(i+1):02d}) {sub_name}\n"
        else:
            msg += f"({i+1}) {sub_name}\n"

    return(msg + '```')

def hail_mary_submissions(conn, player):
    c = conn.cursor()

    try:
        ID = str(player.id)
    except:
        ID = player

    c.execute("""
        SELECT id, name, regular_subs, micro_subs, chaser
        FROM players
        WHERE discord_id = ?
    """, (ID, ))
    row = c.fetchone()

    if not row:
        return f"Cannot find **{player}**. Please send this over to Mia (the scoreboard name and discord name) if you think this is an error."

    player_id, name, regular_subs, micro_subs, chaser = row
    submissions = (regular_subs if regular_subs is not None else 0) + (micro_subs if micro_subs is not None else 0)

    msg = f"**{name}**\nThis "
    if chaser == True:
        msg += f"Chaser"
    else:
        msg += f"player"

    if(submissions == 0):
        msg += f" has no submissions :("
        return msg
    

    c.execute("""
        SELECT name, has_played, place
        FROM hail_mary
        WHERE submitter_id = ?
        ORDER BY place DESC
    """, (player_id, ))
    sub_list = c.fetchall()

    msg_end = ""

    average_distance = []

    for game_name, has_played, place in sub_list:
        average_distance.append(0 if place <= 50 else (place - 50))
        last_play_format = ('(' if has_played else '[') + ("HM" if place <= 50 else str(place - 50)) + (')' if has_played else ']')
        if(place <= 50):
            msg_end += "-" * max([len(l[0]) + 6 for l in sub_list]) + "\n"
        msg_end += (f"{last_play_format:>5} {game_name}\n")

    average_distance = int(mean(average_distance))
    msg += "'s submission" + ("s" if submissions > 1 else "") + f" are on average **{average_distance}** from entering hail mary.\n```\n"
    msg += msg_end + "```"

    return(msg)

def game_streaks(conn):
    c = conn.cursor()
    def game_from_track_id(track_id):
        c.execute("""
        SELECT t.game_id
        FROM tracks t
        WHERE id = ?
        """, (track_id, ))
        return c.fetchone()[0]

    c.execute("""
        SELECT track_id, episode, track_num, mode
        FROM plays
        WHERE mode = 2 OR mode = 3
    """)
    rows = c.fetchall()
    streak = [game_from_track_id(rows[0][0]), 1]


    current_episode = rows[0][1] #first episode
    for track_id, episode, track_num, mode in rows:
        if episode != current_episode: #episode ended, restart streak
           current_episode = episode
           streak = [game_from_track_id(track_id), 1]
        else:
            game_id = game_from_track_id(track_id)
            if game_id == streak[0]: #game is the same, streak continues
                streak[1] += 1
            else: #streak dies
                if(streak[1] > 2):
                    game_name = get_game_name_from_id(conn, streak[0])
                    print(f"{game_name} played {streak[1]} times in a row on episode {current_episode}")
                streak = [game_from_track_id(track_id), 1]
    
def boost_data(conn, game_id, game_name):
    c = conn.cursor()

    c.execute("""
        SELECT double_noosts, noosts, neutrals, boosts, double_boosts, score, easy, graduated 
        FROM boosts
        WHERE game_id = ?
    """, (game_id, ))

    fetched_data = c.fetchone()

    double_noosts = (fetched_data[0])
    noosts        = (fetched_data[1])
    neutrals      = (fetched_data[2])
    boosts        = (fetched_data[3])
    double_boosts = (fetched_data[4])

    score       = fetched_data[5]
    easy        = fetched_data[6]
    graduate    = fetched_data[7]

    gradCheck = "*not* " if graduate == 0 else ""
    easyCheck = " It is considered an easy game." if easy == 1 else ""
    
    msg = f"""**{game_name}**
This game has a total boost score of **{score}**. It has {gradCheck}graduated.{easyCheck}
```
Double Boosts (+2): {double_boosts}
Boosts        (+1): {boosts}
Neutrals      (+0): {neutrals}
Noosts        (-1): {noosts}
Double Noosts (-2): {double_noosts}
```"""
    return msg

def very_hard(conn):
    c = conn.cursor()
    c.execute("""
        SELECT game_id, score 
        FROM boosts 
        WHERE score <= -2 
        ORDER BY score
    """)
    vh_game_ids = c.fetchall()
    msg = ""
    
    for game_id, score in vh_game_ids:
        game_name = get_game_name_from_id(conn, game_id)
        msg += f"({score}) {game_name}\n"

    return msg

def main():
    conn = connect()

    # merge_tracks(conn, track_id_remove=12128, track_id_keep=12614)

    # which_games_are_missing(conn)

    # game_name = "arknights"
    # get_sub_tracks(conn, game_name)
    # get_tracks(conn, game_name)

    # get_episode(conn, 652, Play_Mode.REGULAR)

    # print(hail_mary(conn))
    # print(submissions(conn, 120137608016691200))
    # get_track_plays(conn, "eschatos")
    # game_streaks(conn)
    # print(boost_data(conn, 378, "Ghost Trick"))
    print(very_hard(conn))

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root
    main()