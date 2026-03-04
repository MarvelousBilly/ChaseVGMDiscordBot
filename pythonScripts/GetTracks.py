import sys
import os
import discord

sys.path.append(os.path.join(".", "pythonScripts"))  # so Python can find the module
from GameInfo import *
from GeneralSQL import *
from Helpers import *

def get_track_plays(conn, game_name):
    c = conn.cursor()
    
    game_id, _ = get_id_and_formatted_game_name(conn, game_name)
        
    c.execute("""
        SELECT t.id, t.name
        FROM tracks t
        JOIN games g ON g.id = t.game_id
        WHERE g.id = ? OR g.expansion_game_id = ?;
    """, (game_id, game_id))
    tracks = c.fetchall()
    
    track_plays = {}
    
    for track_id, name in tracks:    
        c.execute("""
            SELECT episode, mode
            FROM plays
            WHERE track_id = ?
        """, (track_id, ))
        
        if name in track_plays:
            track_plays[name] += c.fetchall()
            track_plays[name] = sorted(track_plays[name])
        else:
            track_plays[name] = sorted(c.fetchall())
        
    return track_plays 
    

def get_track_embed(conn, game_name, track_plays, page, per_page, total_pages, glorp_image):
    _, base_game_name = get_base_id_and_formatted_game_name(conn, game_name)

    embed=discord.Embed(title=f"**{game_name}**", color=0xa0df82, description="**Regular Rounds** / __Time Raid__ / Final Chase\n------------------------------------------------\n")
        
    filepath = os.path.join(".", "data", "boxarts", cleanFilename(base_game_name) + ".png")
    filename = filepath if os.path.exists(filepath) else os.path.join(".", "data", "0.png")
    if(glorp_image != None):
        filename = glorp_image
    
    file = discord.File(filename, filename="image.png")
    
    embed.set_thumbnail(url="attachment://image.png")            
    embed.set_footer(text=f"({page}/{total_pages})")
    track_plays = tuple(track_plays.items())[(page-1)*(per_page):page*per_page]
        
    for song, plays in track_plays:
        
        tracks_string = "["
        for play in plays:
            episode, mode = play
            tracks_string += ((f"__{episode}__") if mode == Play_Mode.TIME_RAID.value else (f"**{episode}**") if mode == Play_Mode.REGULAR.value else (f"{episode}")) + ", "
            
        if(tracks_string != "["):
            tracks_string = tracks_string[:-2] + "]"
            embed.add_field(name=song[:255], value=f"\u2800\u2800({len(plays)})  {tracks_string}", inline=False)
        else:
            embed.add_field(name=song[:255], value=f"\u2800\u2800(0)", inline=False)
            
    return embed, file


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root
    # conn = connect()
    
    # get_tracks(conn, "arknights")