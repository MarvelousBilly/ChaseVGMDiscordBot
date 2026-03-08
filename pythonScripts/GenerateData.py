import sqlite3
import os
import sys
import re
import csv
from collections import defaultdict

sys.path.append(os.path.join(".", "pythonScripts"))  # so Python can find the module
from GameInfo import *
from GeneralSQL import *
from ResetData import *
from Helpers import *

import GoogleSheetsAPI

def debuts(conn): #will work whenever
    def update_sheet():
        debutID = "1BC1Kpx8j8BXBIOIsHxEeDIaThjlrPY3OATRWeV7J24U" #snag this opportunity to update debut data (could crontab it to be every month but whatever this is fine
        debutRange = "Sheet1!A1:C1500"
        debutFilename = os.path.join(".", "data", "sheets", "debuts")
        GoogleSheetsAPI.main(debutID, debutRange, debutFilename)
        return debutFilename + "_values.csv"
    
    c = conn.cursor()

    sub_debut = {}
    
    fields = []
    rows = []
    
    with open(update_sheet(), 'r', encoding='utf-8') as csvfile: #read csv
        csvreader = csv.reader(csvfile)
        fields = next(csvreader)
        for row in csvreader:
            rows.append(row)
                
    for i, row in enumerate(rows): #list of UID, Debut, Name (~1200 lines)
        if((i < len(rows) - 1) and len(row[0]) == 4 and len(rows[i + 1][0]) == 5): #we're looking at a game with an expansion(s), add those instead
            continue
        game_name = row[2].strip()
        try:
            game_id = get_id_from_game_name(conn, game_name)
            sub_debut[game_id] = row[1]
            
            c.execute("""
                SELECT name
                FROM games
                WHERE id = ?
            """, (game_id, ))
            
            game_name = c.fetchone()[0]
        
            update_game(conn, Game(game_name, debut=int(row[1])))
            
        except Exception as e:
            if "int()" not in str(e):
                print(game_name, e)
                
    conn.commit()
                    
def update_game_last_play(conn):
    c = conn.cursor()

    c.execute("""
        SELECT
            t.game_id,
            MAX(p.episode) AS last_play,
            MAX(CASE WHEN p.mode = 1 THEN p.episode ELSE NULL END) AS last_rr_play
        FROM plays p
        JOIN tracks t ON p.track_id = t.id
        GROUP BY t.game_id
    """)

    updates = c.fetchall()  # list of tuples: (game_id, last_play, last_rr_play)

    for game_id, last_play, last_rr_play in updates:
        c.execute("""
            UPDATE games
            SET last_play = ?, last_rr_play = ?
            WHERE id = ?
        """, (last_play, last_rr_play, game_id))

    conn.commit()

def update_points_submissions(conn):
    def update_sheet():
        scoreboardID = "1mq4spM6dc0GOzUna_6S5T8jGH_NhO7VxNEm93MD5dYA" #snag this opportunity to update scoreboard data (likely just 1 episode behind)
        scoreboardRange = "SimpleScoreboard!A1:AZ600"
        scoreboardFilename = os.path.join(".", "data", "sheets", "playerscore")
        GoogleSheetsAPI.main(scoreboardID, scoreboardRange, scoreboardFilename)
        return scoreboardFilename + "_values.csv"
    
    def getSubs(s):
        match = re.match(r'^(\d+)', s.strip())
        return match.group(1) if match else None
    def getMicros(s):
        match = re.search(r'\(([^)]*)\)', s.strip())
        return match.group(1) if match else None
    
    c = conn.cursor()

    fields = []
    rows = []
    
    with open(update_sheet(), 'r', encoding='utf8', errors='replace') as csvfile: #read csv
        csvreader = csv.reader(csvfile)
        fields = next(csvreader)
        for row in csvreader:
            rows.append(row)

    for row in rows:
        player_name = row[0]
        player_points = int(row[1])
        player_regular_subs = None
        player_micros = None
        player_submission_list = None
        player_is_chaser = (player_points < 0)
        try: #has any submissions at all
            player_regular_subs = getSubs(row[4])
            player_micros = getMicros(row[4])
            player_submission_list = row[5:]
        except:
            pass

        # print(player_name, player_points, player_regular_subs, player_micros, player_submission_list)
        c.execute("""
            INSERT INTO players (name, points, regular_subs, micro_subs, chaser)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name)
            DO UPDATE SET
                points = excluded.points;
        """, (player_name, player_points, player_regular_subs, player_micros, player_is_chaser))
        c.execute("SELECT id FROM players WHERE name = ?", (player_name,))
        player_id = c.fetchone()[0]
        
        if(player_submission_list is None):
            continue

        for game_name in player_submission_list:
            if "(m)" in game_name:
                game_name = game_name[:-4]
            game_id = get_base_id_from_game_name(conn, game_name) #errors if not found

            # print(player_name, player_id, game_name, game_id)

            c.execute("""
                UPDATE games
                SET submitter_id = ?
                WHERE id = ?
            """, (player_id, game_id))



    conn.commit()




def add_episode(conn):
    def is_episode_in_file(episode):
        with open(os.path.join(".","data","Chase_Episodes_Full.txt"), 'r', encoding='utf-8', errors='replace') as f:
            for l in f:
                if "c:\\users\\aakadarr\\desktop\\games\\q\\chase episodes 2\\The Chase VGM #" + episode + ".txt" in l.strip():
                    print("Episode " + episode + " is already in!")
                    return True
            f.close()
            return False
        
    def process_file(directory, filename):
        filepath = os.path.join(".", "data", "Chase_Episodes_Full.txt")
        with open(filepath, 'a', encoding='utf-8', errors='replace') as main_file:
            if filename.endswith('.txt') and filename.startswith("The_Chase_VGM_"):
                file_path = os.path.join(directory, filename)
                with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                    content = file.read()
                    numbers = re.findall(r'\d+', filename)
                    combined_number = ''.join(numbers) if numbers else 'NoNumberFound' #episode num of filename
    
                    print('Adding new episode: ' + combined_number)
                    main_file.write(content)
                os.remove(file_path)

    directory = os.path.join(".","files")
    for filename in [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]:
        if "The_Chase_VGM" in filename:
            new_episode_file_path = os.path.join(directory, filename)
            already_in = False

            with open(new_episode_file_path, 'r+', encoding='utf-8', errors='replace') as file: #update file to include header formatting and stuff
                content = file.read()
                numbers = re.findall(r'\d+', filename)
                combined_number = ''.join(numbers) if numbers else 'NoNumberFound' #episode num of filename
                already_in = is_episode_in_file(combined_number)

                if("************************************************************************\n") not in content:
                    file.seek(0)
                    file.write("c:\\users\\aakadarr\\desktop\\games\\q\\chase episodes 2\\The Chase VGM #" + combined_number + ".txt\n")
                    file.write("************************************************************************\n")
                    file.write("\n\n\n\n\n")
                    file.write(content + '\n\n\n\n')
                    file.truncate()
            if(not already_in):
                e = all_tracks(conn, os.path.join(directory, filename)) #read in the new file
                if e == None:
                    process_file(directory, filename)
                else:
                    return e
            else:
                print(f"Removing {filename}")
                os.remove(new_episode_file_path)


    
def reset(conn):
    c = conn.cursor() #reset everything :)
    c.execute("DELETE FROM games")
    c.execute("DELETE FROM game_alt_names")
    c.execute("DELETE FROM tracks")
    c.execute("DELETE FROM plays")
    # c.execute("DELETE FROM players") #dont do this one bro dont do it
    conn.commit()
    
    games_expansions_alternates_subs_comments_images(conn, os.path.join(".", "data", "game_versions.txt"))
    debuts(conn)
    sub_tracks(conn)
    all_tracks(conn)
    update_game_last_play(conn)
    print("Done reset")

def new_subs(conn): #just add the new subs
    games_expansions_alternates_subs_comments_images(conn, os.path.join(".", "data", "new_subs.txt"))
    debuts(conn) #grabs new subs and new batch
    print("Done new subs")
    
def new_episode(conn): #runs after each episode / batch drop
    e = add_episode(conn)
    if(e is None):
        update_game_last_play(conn)
        which_games_are_missing_arts(conn) #print out any games (base only) that have missing boxarts (or filename is wrong)
        update_points_submissions(conn)
        print("Done update")
    else:
        print(f"Error: {e}")
        return e
    



def main():
    conn = connect()
    
    # reset(conn)
    # new_subs(conn)
    new_episode(conn)
    

        
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root
    main()