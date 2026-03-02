import os
import yt_dlp


def download_track(search_query: str) -> dict | None:
    """
    Searches for a track on SoundCloud and downloads a clean 320kbps MP3.

    Args:
        search_query (str): The search string (e.g., "Artist - Track Name").

    Returns:
        dict | None: Dictionary with file path and metadata for Telegram,
        or None if an error occurs.
    """
    print(f"Searching on SoundCloud: {search_query}...")

    download_folder = "downloads"
    os.makedirs(download_folder, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{download_folder}/%(title)s [%(id)s].%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'writethumbnail': False,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }
        ],
    }

    query = f"scsearch1:{search_query}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)

            if 'entries' in info and len(info['entries']) > 0:
                entry = info['entries'][0]

                filename = ydl.prepare_filename(entry)
                mp3_filename = os.path.splitext(filename)[0] + '.mp3'

                if os.path.exists(mp3_filename):
                    sc_title = entry.get('title', 'Unknown Track')
                    sc_uploader = entry.get('uploader', 'Unknown Artist')

                    return {
                        'filepath': mp3_filename,
                        'sc_title': sc_title,
                        'sc_uploader': sc_uploader
                    }
                else:
                    return None
            else:
                return None

    except Exception as e:
        print(f"Error downloading track: {e}")
        return None
