import re

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import SPOTIPY_REDIRECT_URI, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

SCOPE = "playlist-read-private playlist-read-collaborative"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=".spotipy_cache"
))


def parse_spotify_link(url: str) -> dict | None:
    """
    Determines the type of Spotify link (playlist, track, or album)
    and extracts the title, track list, and cover art URL.

    Args:
        url (str): The Spotify URL.

    Returns:
        dict | None: Dictionary with type, title, tracks list, and cover_url.
    """
    playlist_match = re.search(r"playlist/([a-zA-Z0-9]+)", url)
    if playlist_match:
        return _process_playlist(playlist_match.group(1))

    track_match = re.search(r"track/([a-zA-Z0-9]+)", url)
    if track_match:
        return _process_single_track(track_match.group(1))

    album_match = re.search(r"album/([a-zA-Z0-9]+)", url)
    if album_match:
        return _process_album(album_match.group(1))

    print("Unsupported Spotify link format.")
    return None


def _process_playlist(playlist_id: str) -> dict | None:
    """Processes a Spotify playlist and returns its metadata."""
    try:
        playlist_info = sp.playlist(playlist_id, fields="name,images")
        playlist_name = playlist_info['name']

        cover_url = None
        if playlist_info.get('images') and len(playlist_info['images']) > 0:
            cover_url = playlist_info['images'][0]['url']

        results = sp.playlist_tracks(playlist_id)
        clean_tracks = []

        for item in results['items']:
            track = item.get('track')
            if track:
                artists = ", ".join(
                    [artist['name'] for artist in track['artists']]
                )
                clean_tracks.append(f"{artists} - {track['name']}")

        while results['next']:
            results = sp.next(results)
            for item in results['items']:
                track = item.get('track')
                if track:
                    artists = ", ".join(
                        [artist['name'] for artist in track['artists']]
                    )
                    clean_tracks.append(f"{artists} - {track['name']}")

        return {
            'type': 'playlist',
            'title': playlist_name,
            'tracks': clean_tracks,
            'cover_url': cover_url
        }
    except Exception as e:
        print(f"Error parsing playlist: {e}")
        return None


def _process_album(album_id: str) -> dict | None:
    """Processes a Spotify album and returns its metadata."""
    try:
        album_info = sp.album(album_id)
        album_artist = ", ".join(
            [artist['name'] for artist in album_info['artists']]
        )
        album_title = f"{album_artist} - {album_info['name']}"

        cover_url = None
        if album_info.get('images') and len(album_info['images']) > 0:
            cover_url = album_info['images'][0]['url']

        results = sp.album_tracks(album_id)
        clean_tracks = []

        for track in results['items']:
            artists = ", ".join(
                [artist['name'] for artist in track['artists']]
            )
            clean_tracks.append(f"{artists} - {track['name']}")

        while results['next']:
            results = sp.next(results)
            for track in results['items']:
                artists = ", ".join(
                    [artist['name'] for artist in track['artists']]
                )
                clean_tracks.append(f"{artists} - {track['name']}")

        return {
            'type': 'album',
            'title': album_title,
            'tracks': clean_tracks,
            'cover_url': cover_url
        }
    except Exception as e:
        print(f"Error parsing album: {e}")
        return None


def _process_single_track(track_id: str) -> dict | None:
    """Processes a single Spotify track and returns its metadata."""
    try:
        track_info = sp.track(track_id)
        artists = ", ".join(
            [artist['name'] for artist in track_info['artists']]
        )
        track_name = track_info['name']
        search_query = f"{artists} - {track_name}"

        cover_url = None
        if track_info.get('album') and track_info['album'].get('images'):
            cover_url = track_info['album']['images'][0]['url']

        return {
            'type': 'track',
            'title': search_query,
            'tracks': [search_query],
            'cover_url': cover_url
        }
    except Exception as e:
        print(f"Error parsing track: {e}")
        return None


def get_my_playlists() -> list:
    """Fetches the current user's playlists."""
    try:
        results = sp.current_user_playlists(limit=15)
        return [
            {'name': item['name'], 'id': item['id']}
            for item in results['items']
        ]
    except Exception as e:
        print(f"Error fetching user playlists: {e}")
        return []