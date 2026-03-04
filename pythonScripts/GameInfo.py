from enum import Enum, Flag, auto

class Type(Flag):
    REGULAR   = auto() #1
    MICRO     = auto() #2
    LEGACY    = auto() #4
    GRADUATED = auto() #8

class Play_Mode(Enum):
    REGULAR         = 1
    TIME_RAID       = 2
    FINAL_CHASE     = 3
    SPECIAL_EPISODE = 4

class Game:
    def __init__(self, name, subtype = Type.REGULAR, debut = None, last_play = None, last_rr_play = None, submitter_id = None, comment = None, expansion_game_id = None):
        self.name = name.strip()
        self.subtype = subtype.value
        self.debut = debut
        self.last_play = last_play
        self.last_rr_play = last_rr_play
        self.submitter_id = submitter_id
        self.comment = comment
        self.expansion_game_id = expansion_game_id
        
class Track:
    def __init__(self, game, name, sub_track, play = None):
        self.game = game.strip()
        self.name = name.strip()
        self.sub_track = sub_track
        self.play = play

class Play:
    def __init__(self, episode, mode, track_num):
        self.episode = episode
        self.mode = mode.value
        self.track_num = track_num

