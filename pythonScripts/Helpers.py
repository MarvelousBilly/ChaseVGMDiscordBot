import os
from pathvalidate import sanitize_filepath

def cleanFilename(filename):
    filename = filename.replace(":", "-")
    filename = filename.replace("/","-")
    filename = filename.replace("\u2019", "'") #curly brace
    filename = filename.replace("\u03bb", "A") #lambda
    filename = filename.replace("\u0394", "A") #delta
    filename = filename.replace("\u00b2", "2") #superscript 2
    return sanitize_filepath(filename)

def get_id_from_game_name(conn, game_name):
    c = conn.cursor()
    
    c.execute("""
        SELECT g.id
        FROM games g
        LEFT JOIN game_alt_names a ON a.game_id = g.id
        WHERE g.name = ? COLLATE NOCASE OR a.alt_name = ? COLLATE NOCASE
        LIMIT 1
    """, (game_name, game_name))

    row = c.fetchone()
    if not row:
        raise ValueError(f"Game not found: {game_name}")

    return row[0]

def get_base_id_from_game_name(conn, game_name):
    c = conn.cursor()
    
    c.execute("""
        SELECT COALESCE(g.expansion_game_id, g.id)
        FROM games g
        LEFT JOIN game_alt_names a ON a.game_id = g.id
        WHERE g.name = ? COLLATE NOCASE
           OR a.alt_name = ? COLLATE NOCASE
        LIMIT 1
    """, (game_name, game_name))

    row = c.fetchone()
    if not row:
        raise ValueError(f"Game not found: {game_name}")

    return row[0]


def get_game_name_from_id(conn, game_id):
    c = conn.cursor()
    c.execute("""
        SELECT name
        FROM games
        WHERE id = ?
    """, (game_id, )) 
    
    return c.fetchone()[0]


def get_base_id_and_formatted_game_name(conn, game_name):
    game_id = get_base_id_from_game_name(conn, game_name)
    game_name = get_game_name_from_id(conn, game_id) #get game name properly formatted
    return game_id, game_name

def get_id_and_formatted_game_name(conn, game_name):
    game_id = get_id_from_game_name(conn, game_name)
    game_name = get_game_name_from_id(conn, game_id) #get game name properly formatted
    return game_id, game_name
    
def which_games_are_missing_arts(conn):
    c = conn.cursor()
    c.execute("""SELECT name FROM games WHERE expansion_game_id IS NULL""")
    games = [l[0] for l in c.fetchall()]
    for game_name in games:
        filepath = os.path.join(".", "data", "boxarts", cleanFilename(game_name) + ".png")
        if not os.path.exists(filepath):
            print(f'{cleanFilename(game_name)}')

