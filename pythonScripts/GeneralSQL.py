import sqlite3
import os
import sys

sys.path.append(os.path.join(".", "pythonScripts"))  # so Python can find the module
from GameInfo import *
from Helpers import *

def connect():
    conn = None
    try:
        conn = sqlite3.connect(os.path.join(".", "data", "game_data.db"))
    except:
        conn = sqlite3.connect(os.path.join("\\192.168.1.223", "database", "data", "game_data.db"))
        
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def update_game(conn, game): #adds game to games table, or update if game already exists
    c = conn.cursor()
    c.execute("""
        SELECT g.id
        FROM games g
        LEFT JOIN game_alt_names a ON a.game_id = g.id
        WHERE g.name = ? COLLATE NOCASE
           OR a.alt_name = ? COLLATE NOCASE
        LIMIT 1
    """, (game.name, game.name))

    row = c.fetchone()

    if row:
        game_id = row[0]

        c.execute("""
            UPDATE games
            SET subtype = ?,
                debut = ?,
                last_play = ?,
                last_rr_play = ?
            WHERE id = ?
        """, (game.subtype, game.debut, game.last_play, game.last_rr_play, game_id))

    else:
        c.execute("""
            INSERT INTO games (name, subtype, debut, last_play, last_rr_play)
            VALUES (?, ?, ?, ?, ?)
        """, (game.name, game.subtype, game.debut, game.last_play, game.last_rr_play))
        
game_cache = {}
def add_track(conn, Track):
    c = conn.cursor()

    if Track.game in game_cache:
        game_id = game_cache[Track.game]
    else:
        game_id = get_id_from_game_name(conn, Track.game)
        game_cache[Track.game] = game_id

    # add track if needed
    c.execute("""
        INSERT OR IGNORE INTO tracks (game_id, name, sub_track)
        VALUES (?, ?, ?)
    """, (game_id, Track.name, Track.sub_track))

    # find the track id
    c.execute("""
        SELECT id
        FROM tracks
        WHERE game_id = ? AND name = ?
    """, (game_id, Track.name))
    track_id = c.fetchone()[0]
    
    if(Track.play is not None): #if we have a play to add,
        
        # add play no matter what
        c.execute("""
            INSERT INTO plays (track_id, mode, episode, track_num)
            VALUES (?, ?, ?, ?)
        """, (track_id, Track.play.mode, Track.play.episode, Track.play.track_num))
        
        #update game to match the play if needed (update last_play and last_rr_play (only if rr play))
        
        if(Track.play.mode == 1): #regular round play
            c.execute("""
                UPDATE games
                SET last_play = CASE WHEN last_play IS NULL OR last_play < ? THEN ? ELSE last_play END,
                    last_rr_play = CASE WHEN last_rr_play IS NULL OR last_rr_play < ? THEN ? ELSE last_rr_play END
                WHERE id = ?
            """, (Track.play.episode, Track.play.episode, Track.play.episode, Track.play.episode, game_id))
        else:
            c.execute("""
                UPDATE games
                SET last_play = CASE WHEN last_play IS NULL OR last_play < ? THEN ? ELSE last_play END
                WHERE id = ?
            """, (Track.play.episode, Track.play.episode, game_id))

def main():
    # pass
    conn = connect()
# 
    update_game(conn, Game("MediEvil (2019)", expansion_game_id=None))
    
#     add_game(conn, Game("Pokemon Gold and Silver", Type.REGULAR | Type.GRADUATED, 587, 2, 16, None))
#     add_game(conn, Game("Pokemon Red and Blue", Type.REGULAR | Type.GRADUATED, 587, 5, 7, None))
# 
#     add_track(conn, Track("arknights", "Broken Sun", False, Play(723, Play_Mode.FINAL_CHASE)))
#     add_track(conn, Track("Pokemon Gold and Silver", "Route 29", False, Play(432, Play_Mode.REGULAR)))
#     add_track(conn, Track("Pokemon Red and Blue", "Route 29", False, Play(100, Play_Mode.REGULAR)))
#     add_track(conn, Track("Pokemon Red and Blue", "Route 29", False, Play(105, Play_Mode.FINAL_CHASE)))
# 
#     hail_mary(conn)
# 
    conn.commit()
    conn.close()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root
    main()