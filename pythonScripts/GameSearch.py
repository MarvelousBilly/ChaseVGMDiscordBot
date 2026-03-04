from rapidfuzz import process, fuzz
import re
import os
import random
from enum import Enum
import time

from GeneralSQL import *

shorthands = {
    #" ": ["  "],
    "1080 snowboarding": ["1080"],
    "the legend of zelda: breath of the wild": ["botw"],
    "civilization": ["civ"],
    "grand theft auto": ["gta"],
    "the last of us": ["tlou"],
    "phantasy star online": ["pso"],
    "virtues last reward": ["vlr"],
    "final fantasy": ["ff", "ff1",    "ffi",      "final fantasy i"],
    "final fantasy 2":     ["ff2",    "ffii",     "final fantasy ii"],
    "final fantasy 3":     ["ff3",    "ffiii",    "final fantasy iii"],
    "final fantasy 4":     ["ff4",    "ffiv",     "final fantasy iv"],
    "final fantasy 5":     ["ff5",    "ffv",      "final fantasy v"],
    "final fantasy 6":     ["ff6",    "ffvi",     "final fantasy vi"],
    "final fantasy 7":     ["ff7",    "ffvii",    "final fantasy vii"],
    "final fantasy 8":     ["ff8",    "ffviii",   "final fantasy viii"],
    "final fantasy 9":     ["ff9",    "ffix",     "final fantasy ix"],
    "final fantasy 10":    ["ff10",   "ffx",      "final fantasy x"],
    "final fantasy 11":    ["ff11",   "ffxi",     "final fantasy xi"],
    "final fantasy 12":    ["ff12",   "ffxii",    "final fantasy xii"],
    "final fantasy 13":    ["ff13",   "ffxiii",   "final fantasy xiii"],
    "final fantasy 14":    ["ff14",   "ffxiv",    "final fantasy xiv"],
    "final fantasy 15":    ["ff15",   "ffxv",     "final fantasy xv"],
    "final fantasy 16":    ["ff16",   "ffxvi",    "final fantasy xvi"],
    "final fantasy 10-2":  ["ff10-2", "ffx-2",    "final fantasy x2", "final fantasy x-2", "final fantasy 10 2"],
    "final fantasy 13-2":  ["ff13-2", "ffxiii-2", "final fantasy xiii2", "final fantasy xiii-2", "final fantasy 13 2"],
    "final fantasy tactics advance": ["ffta", "final fantasy ta"],
    "final fantasy tactics advance 2": ["ffta2"],
    "fire emblem": ["fe"],
    "the world ends with you": ["twewy"],
    "marvel vs capcom": ["mvc"],
    "shin megami tensei": ["smt"],
    "super smash bros": ["smash bros", "smash", "ssb"],
    "ultimate": ["ult"],
    "donkey kong country": ["dkc"],
    "pokemon mystery dungeon": ["pmd"],
    "kingdom hearts": ["kh"],
    "king of fighters": ["kof"],
    "battle for bikini bottom": ["bfbb"],
    "gold and silver": ["hgss"],
    "ruby and sapphire": ["oras"],
    "red and blue": ["frlg"],
    "sun and moon": ["usum"],
    "pokemon legends arceus": ["pla"],
    "call of duty": ["cod"],
    "gran turismo": ["gt"],
    "metal gear solid": ["mgs"],
    "the thousand year door": ["ttyd"],
    "mario kart": ["mk"],
    "super mystery dungeon": ["smd"],
    "persona 4 dancing": ["p4d", "p4 dancing"],
    "the great ace attorney": ["tgaa"],
    "the great ace attorney 2": ["tgaa2"],
    "the great ace attorney chronicles": ["tgaac"],
    "dead or alive": ["doa"],
    "devil may cry": ["dmc"],
    "dragon quest": ["dq"],
    "dragon quest 7": ["dq7"],
    "dragon quest 8": ["dq8"],
    "golden sun the lost age": ["golden sun lost age"],
    "super castlevania 4": ["castlevania 4", "castlevania iv"],
}

# perfect match shortcuts (if your search is JUST this then it gets swapped)
perfect_match = {
    "hikwysog": "adventure time: hey ice king",
    "sonic": "sonic the hedgehog",
    "sonic 3": "sonic 3 and knuckles",
    "sonic 2": "sonic the hedgehog 2",
    "super smash bros": "super smash bros 64",
    "wanda to kyozo": "shadow of the colossus",
    "mk64": "mario kart 64",
    "mkds": "mario kart ds",
    "mk8": "mario kart 8",
    "mkwii": "mario kart wii",
    "mkdd": "mario kart double dash",
    "mario": "super mario bros",
    "mario 2": "super mario bros 2",
    "mario 3": "super mario bros 3",
    "mario world": "super mario world",
    "mario 64": "super mario 64",
    "moon": "moon: remix rpg adventure",
    "x": "x (lunar chase)",
    "lunar chase": "x (lunar chase)",
    "klonoa": "klonoa: door to phantomile",
    "klboa": "klonoa: door to phantomile",
    "klonoa 2": "klonoa 2: lunatea's veil",
    "ys 3": "ys: the oath in felghana",
    "999": "999: nine hours, nine persons, nine doors",
    "metal slug 2": "metal slug x",
    "ftl": "ftl: faster than light",
    "pokemon red": "pokemon red and blue",
    "pokemon blue": "pokemon red and blue",
    "pokemon gold": "pokemon gold and silver",
    "pokemon silver": "pokemon gold and silver",
    "pokemon crystal": "pokemon gold and silver",
    "pokemon ruby": "pokemon ruby and sapphire",
    "pokemon sapphire": "pokemon ruby and sapphire",
    "pokemon emerald": "pokemon ruby and sapphire",
    "pokemon fire red": "pokemon red and blue",
    "pokemon leaf green": "pokemon red and blue",
    "pokemon diamond": "pokemon diamond and pearl",
    "pokemon pearl": "pokemon diamond and pearl",
    "pokemon platinum": "pokemon diamond and pearl",
    "pokemon heart gold": "pokemon gold and silver",
    "pokemon soul silver": "pokemon gold and silver",
    "pokemon black": "pokemon black and white",
    "pokemon white": "pokemon black and white",
    "pokemon black 2": "pokemon black and white 2",
    "pokemon white 2": "pokemon black and white 2",
    "pokemon x": "pokemon x and y",
    "pokemon y": "pokemon x and y",
    "pokemon omega ruby": "pokemon ruby and sapphire",
    "pokemon alpha sapphire": "pokemon ruby and sapphire",
    "pokemon sun": "pokemon sun and moon",
    "pokemon moon": "pokemon sun and moon",
    "pokemon ultra sun": "pokemon sun and moon",
    "pokemon ultra moon": "pokemon sun and moon",
    "pokemon sword": "pokemon sword and shield",
    "pokemon shield": "pokemon sword and shield",
    "pokemon scarlet": "pokemon scarlet and violet",
    "pokemon violet": "pokemon scarlet and violet",
    "phantasy star online 3": "phantasy star online episode 3: c.a.r.d. revolution",
    "phantasy star online episode 3": "phantasy star online episode 3: c.a.r.d. revolution",
    "phantasy star online card revolution": "phantasy star online episode 3: c.a.r.d. revolution",
    "road trip adventure": "choro-q hg 2",
    "clair obscur": "clair obscur: expedition 33",
    "expedition 33": "clair obscur: expedition 33",
}

def normalize(text):
    return re.sub(r'[^a-z0-9 ]+', '', text.lower().strip())

def smart_game_search(query, all_game_names, top_n=5):

    query_full = normalize(query)

    results = []

    for title, game_id in all_game_names:
        title_norm = normalize(title)

        if title_norm == query_full:
            results.append((title, 100, game_id))
            continue

        score_strict = fuzz.ratio(query_full, title_norm)
            
        score_partial = fuzz.partial_ratio(query_full, title_norm)
            
        base_score = min(score_strict, score_partial)

        len_penalty = abs(len(title_norm.split()) - len(query_full.split())) * 2
        
        prefix_bonus = 5 if title_norm.startswith(query_full) else 0
        
        final_score = base_score - len_penalty + prefix_bonus
        final_score = max(0, min(final_score, 99))
        avg = (score_strict + score_partial + fuzz.token_set_ratio(query_full, title_norm)) / 3

        results.append((title, avg, game_id))

    results.sort(key=lambda x: -x[1])
    
    return results[:top_n]


def search(conn, game):
    c = conn.cursor()
    c.execute("""
        SELECT name, id FROM games
        UNION
        SELECT alt_name, game_id FROM game_alt_names;
    """)
    all_game_names = c.fetchall()
    
    def extract_trailing_number(text):
        match = re.search(r'(\d+)$', text)
        return int(match.group(1)) if match else None

    results = smart_game_search(game, all_game_names)
    best_by_id = {}

    for title, score, game_id in results:
        if game_id not in best_by_id or score > best_by_id[game_id][1]:
            best_by_id[game_id] = (title, score, game_id)

    results = sorted(best_by_id.values(), key=lambda x: -x[1])

    best_match, best_score, best_id = results[0]
    second_score = results[1][1] if len(results) > 1 else 0
    score_gap = best_score - second_score

    HIGH_CONFIDENCE = 80
    TIE_MARGIN = 1
    LOWEST_SCORE = 60

    # Extract trailing numbers from input and best match
    input_num = extract_trailing_number(game)
    match_num = extract_trailing_number(best_match)
    #print(input_num, match_num)

    # If both have numbers but differ, be more strict
    if (input_num is not None) and (match_num is not None) and (input_num != match_num):
    
        # Reject if score is not perfect (100)
        if best_score < 100:
            out_message = f"**{game}** is not in the Chase. Did you mean one of these:\n"
            added = False
            for i, (gameVal, score, game_id) in enumerate(results, start=1):
                if score >= LOWEST_SCORE:
                    added = True
                    score = round(score)
                    out_message += f"({i})\t{gameVal} ({score}%)\n"
            if not added:
                out_message = f"**{game}** is not in the Chase."
            return False, None, None, out_message
    
    # Normal acceptance conditions
    if best_score == 100:
        return True, best_match, best_id, best_score

    if best_score >= HIGH_CONFIDENCE and score_gap > TIE_MARGIN:
        return True, best_match, best_id, best_score

    out_message = f"**{game}** can't be found. Did you mean one of these:\n"
    added = False
    for i, (game_val, score, game_id) in enumerate(results, start=1):
        if score >= LOWEST_SCORE:
            added = True
            score = round(score)
            out_message += f"({i})\t{game_val} ({score}%)\n"
    if not added:
        out_message = f"**{game}** is not in the Chase."
    return False, None, None, out_message    

def main():
    conn = connect()

    while True:
        game = input("Game name: ")
        match, game_name, game_id, msg = search(conn, game)
        print(match, "|", game_name, "|", game_id, "|", msg)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.chdir("..")
    main()