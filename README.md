# Telegram Spotify & SoundCloud Downloader Bot

An asynchronous Telegram bot built with `aiogram 3` that acts as a bridge between Spotify and Telegram. It allows users to parse Spotify links (tracks, albums, playlists), automatically find the corresponding audio on SoundCloud, download them in high quality (320 kbps), and send them to Telegram chats or channels as neat media groups with original cover arts.

## 🏗 Architecture
1. **Parser (`spotify_parser.py`):** Uses the `spotipy` library to authenticate via OAuth 2.0. It extracts the track list, artists, and cover image URLs based on the provided Spotify link.
2. **Downloader (`downloader.py`):** Uses `yt-dlp` to search for the query (e.g., "Artist - Track Name") specifically on SoundCloud (`scsearch1:`) to find explicit/original versions, downloads the audio, and uses FFmpeg to convert it to MP3.
3. **Telegram Router (`handlers.py`):** Manages the user interface, FSM (Finite State Machine) for inputs, and constructs `MediaGroupBuilder` objects for delivery.
