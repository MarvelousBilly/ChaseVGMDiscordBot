import sqlite3
import os
import sys
import re
from collections import defaultdict
import math

sys.path.append(os.path.join(".", "pythonScripts"))  # so Python can find the module
from GameInfo import *
from GeneralSQL import *
from Helpers import *
from GetTracks import *

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
        SELECT name, effective_last_play, has_played, row_num
        FROM (
            SELECT id,
                name,
                effective_last_play,
                has_played,
                ROW_NUMBER() OVER (ORDER BY effective_last_play) AS row_num
            FROM hail_mary
        )
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

    return(msg)

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
        ORDER BY debut
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

def main():
    conn = connect()
    
    # which_games_are_missing(conn)

    # game_name = "arknights"
    # get_sub_tracks(conn, game_name)
    # get_tracks(conn, game_name)

    # get_episode(conn, 652, Play_Mode.REGULAR)

    # print(hail_mary(conn))
    print(submissions(conn, 143411810672967680))
    # get_track_plays(conn, "eschatos")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root
    main()