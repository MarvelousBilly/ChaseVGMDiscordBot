import sqlite3
import os
import sys
import re
import csv
from collections import defaultdict
from enum import Enum

sys.path.append(os.path.join(".", "pythonScripts"))  # so Python can find the module
from GameInfo import *
from GeneralSQL import *
from ResetData import *
from Helpers import *
from UpdateGoogleSheet import *
import GoogleSheetsAPI

def update_scores(conn):
    def update_sheet():
        scoreID = "1qJ1Pkeqy7DTlGwDymSalzyUXKJZfYPIi6r3Qvq7KXHE"
        scoreRange = "Boost Data!A2:H1500"
        scoreFilename = os.path.join(".", "data", "sheets", "scores")
        GoogleSheetsAPI.main(scoreID, scoreRange, scoreFilename)
        return (scoreFilename + "_values.csv"), (scoreFilename + "_notes.csv")
    
    c = conn.cursor()
    score_values_name, score_notes_name = update_sheet()

    game_boosts = {}
    
    row_notes = []
    row_value = []
    
    with open(score_values_name, 'r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            row_value.append(row)

    with open(score_notes_name, 'r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            row_notes.append(row)

    for i, row in enumerate(row_value):
        if len(row) < 4:
            continue  # skip incomplete rows

        game_id = row[0]
        grad = (1 if row[5].lower().strip() == "yes" else (-1 if row[5].lower().strip() == "n/a" else 0)) #1 if grad, 0 if not, -1 if micro
        easy = (1 if row[7].lower().strip() == "yes" else 0)
        firstnoost = '1' if "*" in (row[6] if len(row) > 6 else '') else '0'
        score = (row[6] if len(row) > 6 else '').replace('*','')

        game_boosts[game_id] = {
            'graduated': grad       if len(row) > 5 else None,
            'score':     int(score) if len(row) > 6 else None,
            'easy':      easy       if len(row) > 7 else None,
            'firstnoost': firstnoost if len(row) > 6 else None,
            'double_boosts': None,
            'boosts': None,
            'neutrals': None,
            'noosts': None,
            'double_noosts': None
        }
        
    for i, row in enumerate(row_notes):
        if i >= len(row_value):
            break  # Extra note rows not present in values

        game_id = row_value[i][0]

        # Use safe extraction for each column
        boost_note  = row[1] if len(row) > 1 else ''
        neust_note  = row[2] if len(row) > 2 else ''
        noost_note  = row[3] if len(row) > 3 else ''

        split_boosts = boost_note.split('\n') if boost_note else []
        split_neusts = neust_note.split('\n') if neust_note else []
        split_noosts = noost_note.split('\n') if noost_note else []

        doubleboosts = sum('(x2)' in element for element in split_boosts)
        singles      = len(split_boosts) - doubleboosts if split_boosts else 0
        neusts       = len(split_neusts)
        doublenoosts = sum('(x2)' in element for element in split_noosts)
        noosts       = len(split_noosts) - doublenoosts if split_noosts else 0
                    
        if game_id in game_boosts:
            game_boosts[game_id]['double_boosts'] = doubleboosts
            game_boosts[game_id]['boosts']        = singles
            game_boosts[game_id]['neutrals']      = neusts
            game_boosts[game_id]['noosts']        = noosts
            game_boosts[game_id]['double_noosts'] = doublenoosts
            
    # print(game_boosts)
    for key, value in game_boosts.items():

        c.execute("""
            SELECT g.id
            FROM games g
            LEFT JOIN game_alt_names a ON a.game_id = g.id
            WHERE g.name = ? COLLATE NOCASE
                OR a.alt_name = ? COLLATE NOCASE
            LIMIT 1
        """, (key, key))

        game_id = c.fetchone()
        if(game_id == None):
            # raise ValueError(f"Aakadarian has a weird name for {key} :(")
            intended_id = int(input(f"What's the ID of {key}: "))
            #create alternate name for game_id intended_id with value of key
            c.execute("""
                INSERT OR IGNORE INTO game_alt_names (game_id, alt_name)
                VALUES (?, ?)
            """, (intended_id, key))
            conn.commit()

            c.execute("""
                SELECT g.id
                FROM games g
                LEFT JOIN game_alt_names a ON a.game_id = g.id
                WHERE g.name = ? COLLATE NOCASE
                    OR a.alt_name = ? COLLATE NOCASE
                LIMIT 1
            """, (key, key))
            game_id = c.fetchone()

        game_id = game_id[0]

        c.execute("""
            INSERT INTO boosts (game_id, double_noosts, noosts, neutrals, boosts, double_boosts, score, easy, graduated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                double_noosts = excluded.double_noosts,
                noosts        = excluded.noosts,
                neutrals      = excluded.neutrals,
                boosts        = excluded.boosts,
                double_boosts = excluded.double_boosts,
                score         = excluded.score,
                easy          = excluded.easy,
                graduated     = excluded.graduated
        """, (game_id, value['double_noosts'], value['noosts'], value['neutrals'], value['boosts'], value['double_boosts'], value['score'], value['easy'], value['graduated']))

    conn.commit()




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
                points = excluded.points,
                regular_subs = excluded.regular_subs,
                micro_subs = excluded.micro_subs;        
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
    class Episode_Status(Enum):
        BRAND_NEW    = 0
        HAD_ERROR    = 1
        ALREADY_IN   = 2

    def is_episode_in_file(conn, episode):
        c = conn.cursor()
        c.execute("""SELECT count(episode) FROM plays WHERE episode = ?""", (episode, )) #check db for the episode first
        if c.fetchone()[0] > 0:
            print("Episode " + episode + " is already in the database!")
            return Episode_Status.ALREADY_IN
        
        with open(os.path.join(".","data","Chase_Episodes_Full.txt"), 'r', encoding='utf-8', errors='replace') as f:
            for l in f:
                if "c:\\users\\aakadarr\\desktop\\games\\q\\chase episodes 2\\The Chase VGM #" + episode + ".txt" in l.strip():
                    print("Episode " + episode + " is already in the file, but not the database!") 
                    return Episode_Status.HAD_ERROR
            f.close()

        return Episode_Status.BRAND_NEW
        
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
                already_in = is_episode_in_file(conn, combined_number)

                if("************************************************************************\n") not in content: #if need to add the fancy bits
                    file.seek(0)
                    file.write("c:\\users\\aakadarr\\desktop\\games\\q\\chase episodes 2\\The Chase VGM #" + combined_number + ".txt\n")
                    file.write("************************************************************************\n")
                    file.write("\n\n\n\n\n")
                    file.write(content + '\n\n\n\n')
                    file.truncate()
                    
            if(already_in == Episode_Status.BRAND_NEW):
                e = all_tracks(conn, os.path.join(directory, filename)) #read in the new file
                if e == None:
                    process_file(directory, filename)
                else:
                    print(f"Removing {filename}") #remove files in case of error
                    os.remove(new_episode_file_path)
                    return e
                
            elif(already_in == Episode_Status.HAD_ERROR):
                e = all_tracks(conn, os.path.join(directory, filename)) #read in the new file
                if not (e == None): #had error adding (again lols), return the error message
                    print(f"Removing {filename}") #remove files in case of error
                    os.remove(new_episode_file_path)
                    return e
                
            else: #ALREADY_IN
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
    update_points_submissions(conn)
    update_google_sheet(conn)
    print("Done new subs")
    
def new_episode(conn): #runs after each episode / batch drop
    e = add_episode(conn)
    if(e is None): #if the episode add is all fine and dandy:
        update_game_last_play(conn)
        which_games_are_missing_arts(conn) #print out any games (base only) that have missing boxarts (or filename is wrong)
        update_points_submissions(conn)
        update_google_sheet(conn)
        print("Done update")
    else:
        print(f"Error: {e}")
        return e
    

def main():
    conn = connect()
    
    # reset(conn)
    # new_subs(conn)
    # debuts(conn)
    # update_game_last_play(conn)
    # update_points_submissions(conn)
    # update_google_sheet(conn)
    update_scores(conn)
    

        
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root
    main()