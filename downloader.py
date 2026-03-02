import difflib
import os

import yt_dlp


def get_similarity(a: str, b: str) -> float:
    """Возвращает коэффициент схожести двух строк от 0.0 до 1.0"""
    # Переводим в нижний регистр для точного сравнения
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def download_track(search_query: str) -> dict | None:
    """
    Ищет топ-5 треков на SoundCloud, выбирает наиболее точное совпадение
    по названию и скачивает только его.
    """
    print(f"Ищем на SoundCloud: {search_query}...")

    download_folder = "downloads"
    os.makedirs(download_folder, exist_ok=True)

    
    # Получаем Топ-5 результатов БЕЗ скачивания
    
    search_opts = {
        'extract_flat': True,  # Только метаданные
        'quiet': True,
        'no_warnings': True,
    }

    # Ищем 5 результатов вместо 1
    query = f"scsearch5:{search_query}"
    
    best_match_url = None
    best_sc_title = ""
    best_sc_uploader = ""

    try:
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries', [])

            if not entries:
                print(f"Ничего не найдено по запросу: {search_query}")
                return None

            highest_score = -1.0

            # Перебираем все 5 результатов и ищем самое точное совпадение
            for entry in entries:
                sc_title = entry.get('title', '')
                sc_uploader = entry.get('uploader', '')
                
                # Формируем строку как она выглядит на SC: "Автор - Название"
                sc_full_name = f"{sc_uploader} {sc_title}"

                # Сравниваем то, что ищем, с названием трека на SC
                # Проверяем два варианта: чистое название и Название+Автор, берем лучший
                score1 = get_similarity(search_query, sc_title)
                score2 = get_similarity(search_query, sc_full_name)
                local_best_score = max(score1, score2)

                # Если нашли более точное совпадение, запоминаем его
                if local_best_score > highest_score:
                    highest_score = local_best_score
                    # yt-dlp может отдавать ссылку в 'url' или 'webpage_url'
                    best_match_url = entry.get('url') or entry.get('webpage_url')
                    best_sc_title = sc_title
                    best_sc_uploader = sc_uploader

    except Exception as e:
        print(f"Ошибка при поиске трека: {e}")
        return None

    if not best_match_url:
        return None

    print(f"Выбран лучший трек: {best_sc_uploader} - {best_sc_title} (Схожесть: {highest_score:.2f})")

   
    # Скачиваем конкретный выбранный трек
   
    download_opts = {
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

    try:
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            # Качаем уже не по тексту, а по прямой ссылке на трек с наибольшим совпадением
            info = ydl.extract_info(best_match_url, download=True)

            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'

            if os.path.exists(mp3_filename):
                return {
                    'filepath': mp3_filename,
                    'sc_title': best_sc_title,
                    'sc_uploader': best_sc_uploader
                }
            return None

    except Exception as e:
        print(f"Ошибка при скачивании файла: {e}")
        return None
