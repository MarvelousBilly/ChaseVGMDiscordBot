from google.oauth2 import service_account
from googleapiclient.discovery import build
from natsort import natsorted
import os

from GeneralSQL import *
from Helpers import *

def write_to_sheet(sheet_ID, range, values):
    # service account key file
    SERVICE_ACCOUNT_FILE = os.path.join(".", "data", "long-equinox-460223-f6-db89ecf412ff.json")
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # credentials and service
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()
    
    body = {
        "values": values
    }
    
    result = sheet.values().update(
        spreadsheetId=sheet_ID,
        range=range,
        valueInputOption="RAW",
        body=body
    ).execute()
    
    return result
    
def update_google_sheet(conn):
    c = conn.cursor()
    c.execute("""
        SELECT *
        FROM games_and_tracks
    """)

    rows = c.fetchall()

    games = {}
    games_unplayed_sub_tracks = {}
    games_played_sub_tracks = {}
    games_played_boosts = {}
    games_tracks = {}

    for game_name, track_name, sub_track, has_played, last_played, game_played_rr, game_played_at_all in rows:
        if game_name not in games:
            if game_played_rr: #played in regular rounds
                games[game_name] = f"({last_played})"
            elif game_played_at_all: #played only in time raid / final chase
                games[game_name] = f"[{last_played}]"
            else: #game has yet to play
                games[game_name] = f"<{last_played}>"
        if(sub_track and has_played):
            games_played_sub_tracks.setdefault(game_name, []).append(track_name)
        elif(sub_track):
            games_unplayed_sub_tracks.setdefault(game_name, []).append(track_name)
        else:
            games_played_boosts.setdefault(game_name, []).append(track_name)

        games_tracks.setdefault(game_name, []).append(track_name)

    values = []
    for game_name in games:
        if game_name == "Excitebike":
            continue
        
        played_sub_tracks = [] if game_name not in games_played_sub_tracks else games_played_sub_tracks[game_name]
        unplayed_sub_tracks = [] if game_name not in games_unplayed_sub_tracks else games_unplayed_sub_tracks[game_name]
        other_tracks = [] if game_name not in games_played_boosts else games_played_boosts[game_name]
  
        unplayed_formatted = "\n".join(t for t in unplayed_sub_tracks)
        played_formatted   = "\n".join(t for t in played_sub_tracks)
        other_formatted    = "\n".join(t for t in other_tracks)
        all_tracks         = " || ".join(sorted(t for t in games_tracks[game_name]))

        values.append([game_name, unplayed_formatted, played_formatted, other_formatted, all_tracks, games[game_name], games[game_name][1:-1]]) #[GAME, TRACKS, TRACKSLEFT]

    values = natsorted(values, key=lambda x: x[0].lower())    
        
    res = write_to_sheet(
        "1_UdKlca1olhvFfx0yRLleZvcYL5NWCeyxs-N8mlg9aA",
        'Data!A2:G',
        values
    )
    
    update_episode = [[f"Last updated: {c.execute('SELECT MAX(episode) FROM plays').fetchone()[0]}"]]
    
    res = write_to_sheet(
        "1_UdKlca1olhvFfx0yRLleZvcYL5NWCeyxs-N8mlg9aA",
        'Data!M1',
        update_episode
    )
    print(res)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root
    conn = connect()
    update_google_sheet(conn)
