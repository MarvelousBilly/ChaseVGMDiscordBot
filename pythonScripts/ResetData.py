import sqlite3
import os
import sys
import re
import requests

sys.path.append(os.path.join(".", "pythonScripts"))  # so Python can find the module
from GameInfo import *
from GeneralSQL import *
from Helpers import *


def games_expansions_alternates_subs_comments_images(conn, filepath):
    
    def add_game(name, expansion_game_id=None):
        c = conn.execute("""
            INSERT OR IGNORE INTO games
            (name, subtype, debut, last_play, last_rr_play, submitter_id, expansion_game_id)
            VALUES (?, ?, NULL, NULL, NULL, NULL, ?)
        """, (name, Play_Mode.REGULAR.value, expansion_game_id))  # assuming subtype=1 for regular

        # Fetch the id whether inserted now or already existed
        row = conn.execute("""
            SELECT id
            FROM games
            WHERE name = ?
        """, (name,)
        ).fetchone()

        return row[0]
    
    def add_comment_to_game(game_id, comment):
        conn.execute("""
            UPDATE games
            SET comment = ?
            WHERE id = ?
        """, (comment, game_id))

    def add_alt_name(game_id, alt_name):
        conn.execute("""
            INSERT OR IGNORE INTO game_alt_names (game_id, alt_name)
            VALUES (?, ?)
        """, (game_id, alt_name))
    
    current_game_name = None
    current_base_id = None
    current_expansion_id = None

    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            if not raw_line.strip():
                continue
            
            # Expansion
            if raw_line.startswith("E\t"):
                name = raw_line[2:].strip()
                current_expansion_id = add_game(name, current_base_id)

            # Expansion alt name (A\t\t)
            elif raw_line.startswith("A\t\t"):
                name = raw_line[3:].strip()
                add_alt_name(current_expansion_id, name)

            # Base alt name (A\t)
            elif raw_line.startswith("A\t"):
                name = raw_line[2:].strip()
                add_alt_name(current_base_id, name)
                
            # Sub track (S\t)
            elif raw_line.startswith("S\t"):
                sub_track = raw_line[2:].strip()
                add_track(conn, Track(current_game_name, sub_track, True))
            
            # Sub comment (C\t)
            elif raw_line.startswith("C\t"):
                comment = raw_line[2:].strip()
                add_comment_to_game(current_base_id, comment)
            
            # Image url (I\t)
            elif raw_line.startswith("I\t"):
                image_url = raw_line[2:].strip()
                data = requests.get(image_url).content
                new_image = os.path.join(".", "data", "boxarts", cleanFilename(current_game_name) + ".png")
                f = open(new_image,'wb')
                f.write(data)
                f.close()
                
            # Base game
            else:
                name = raw_line.strip()
                current_game_name = name
                current_base_id = add_game(name)
                current_expansion_id = None

    conn.commit()
    
def sub_tracks(conn):    
    with open(os.path.join(".","data","batches.txt"), "r", encoding='utf-8', errors='replace') as fp:
        for l in fp:
            game = l.split(" - ", 1)[0].strip()
            track = l.split(" - ", 1)[1].strip()            
            add_track(conn, Track(game, track, True, None))
        conn.commit()
        
def all_tracks(conn, filepath = os.path.join(".", "data", "Chase_Episodes_Full.txt")):
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f: 
        
        final_chase_strings = ["(Final Chase)", "<Final Chase>", "<Finals>", "(Players)", "(Chaser)"]
        
        track_num = 0
        
        c = 0
        for l in f:
            c+=1
            if ";" == l[0]: #if the first character is a semicolon, ignore the line but increment track
                track_num += 1
                continue
            
            elif "c:\\users\\aakadarr" in l:
                # Start iterating from the end of the string
                number = ""
                Type = 0
                for char in l[::-1][5:8]:
                    number = char + number
                current_chase = int(number)
                
            else:
                if len(l) > 3:
                    if "*****" in l:
                        track_num = 0
                        mode = Play_Mode.REGULAR
                        
                    elif "(Time Raid)" in l:
                        track_num = 0
                        mode = Play_Mode.TIME_RAID
                        
                    elif l.rstrip() in final_chase_strings:
                        if(l.rstrip() == "(Players)"):
                            Type = 1 #classic format, players then chasers
                        else:
                            track_num = 0
                        mode = Play_Mode.FINAL_CHASE
                        
                    elif "########" in l:
                        track_num = 0
                        mode = Play_Mode.SPECIAL_EPISODE
                        
                        
                    else:
                        track_num += 1

                        try:
                            split_string = l.split(" - ")
                            track = (" - ".join(split_string[1:])).strip()
                            
                            pattern = r'\s{2,}.*'
                            track = re.sub(pattern, '', track)
                            if(track == "'"):
                                track = "\u2800"
                            game_name = split_string[0] if (mode == Play_Mode.REGULAR or current_chase < 361 or mode == Play_Mode.TIME_RAID or Type == 1) else split_string[0][4:] if mode == Play_Mode.FINAL_CHASE else split_string[0][5:] # type: ignore
                                                        
                            if(game_name == "Excitebike"):
                                continue
                            
                            add_track(conn, Track(game_name, track, False, Play(current_chase, mode, track_num))) # type: ignore

                        except Exception as e:
                            print("Bad: '" + l.rstrip() + "' on line " + str(c) + " in chase " + str(current_chase)) # type: ignore
                            print(e)
                            print()
                            conn.rollback()
                            return "Bad: '" + l.rstrip() + "' on line " + str(c) + " in chase " + str(current_chase) + ": " + str(e) # type: ignore
                            
    conn.commit()
    return
    
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root

    conn = connect()
    all_tracks(conn)
    