from mutagen._file import File
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4
import os
from ffmpeg import FFmpeg
import shutil

chase_dir = r"/home/mia/Documents/Chase_Music/"

def replace_filename(filename):
    for ch in ['/', '*', '"', '\\', '<', '>', ':', '|']:
        filename = filename.replace(ch, "-")
    filename = filename.replace("?", "？")
    return filename

def get_tags(path):
    try:
        audio = File(path, easy=True)

        if audio:
            album = audio.get('album', ['Unknown Album'])[0]
            title = audio.get('title', ['Unknown Title'])[0]
            return replace_filename(album), replace_filename(title)

    except Exception:
        pass

    try:
        audio = MP4(path)
        album = audio.tags.get('\xa9alb', ['Unknown Album'])[0] # type: ignore
        title = audio.tags.get('\xa9nam', ['Unknown Title'])[0] # type: ignore
        return replace_filename(album), replace_filename(title)
    except Exception:
        pass

    try:
        audio = EasyID3(path)
        album = audio.get('album', ['Unknown Album'])[0] # type: ignore
        title = audio.get('title', ['Unknown Title'])[0] # type: ignore
        return replace_filename(album), replace_filename(title)
    except Exception:
        pass

    return "Unknown Album", os.path.splitext(os.path.basename(path))[0]

def process_file(root, file):
    path = ""
    album = ""
    title = ""
    new_file = ""

    try:
        if file.lower().endswith(".jpg"):
            return

        path = os.path.join(root, file)

        if not file.lower().endswith((".mp3", ".flac", ".m4a", ".aac", ".wav")):
            return
        
        album, title = get_tags(path)

        if (not album or not title) or (album == "Unknown Album" or title == "Unknown Title"):
            raise Exception("Could not read metadata")

        album_dir = os.path.join(chase_dir, album)
        new_file = os.path.join(album_dir, f"{title}.opus")

        os.makedirs(album_dir, exist_ok=True)

        # if os.path.exists(new_file):
        #     print(f"File {new_file} already exists, deleting {path}.")
        #     os.remove(path)
        #     return

        ffmpeg = (
            FFmpeg()
            .option("y")
            .input(path)
            .output(
                new_file,
                {"codec:a": "libopus", "b:a": "128k"},
                map_metadata="0"
            )
        )
        ffmpeg.execute()

        print(f"!!!!!!!!!! Conversion successful: {new_file}, deleting {path}")
        os.remove(path)

    except Exception as e:
        print(f"Error with {file}: {e}.", end='')

        if new_file and os.path.exists(new_file):
            print(f"\n\tCleaning broken file {new_file}", end='')
            os.remove(new_file)

        print()



tasks = [] 
for root, dirs, files in os.walk(r"/home/mia/Documents/Chase_Music_Inbox"): 
    for file in files: 
        process_file(root, file)