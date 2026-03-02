import asyncio
import os

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder


import app.keyboards as kb
from downloader import download_track
from spotify_parser import parse_spotify_link, search_spotify_text


router = Router()


class FindTrack(StatesGroup):
    """Класс состояний для поиска трека/альбома/плейлиста."""
    
    wait_input = State()  # Ожидание ссылки или названия трека


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработка сообщения /start.
    Приветствует пользователя и предлагает выбрать действие.
    """
    user_name = message.from_user.username or message.from_user.first_name
    text = (
        f"Привет, *{user_name}*!\n\n"
        f"Я твой личный музыкальный ассистент. Я умею переносить треки и "
        f"плейлисты из Spotify в твой Telegram-канал.\n\n"
        f"Выбери нужное действие в меню ниже:"
    )
    
    await message.answer(
        text=text,
        reply_markup=kb.main,
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(F.text == 'Найти трек/альбом')
async def answ_btn_find_track(message: Message, state: FSMContext):
    """
    Обработка нажатия кнопки "Найти трек/альбом".
    Переводит пользователя в состояние ожидания ввода.
    """
    await message.answer(
        "Пришли ссылку на плейлист/трек Spotify или напиши "
        "сюда название песни/альбома."
    )
    await state.set_state(FindTrack.wait_input)


@router.message(FindTrack.wait_input, F.text.contains("spotify.com"))
async def find_link(message: Message, state: FSMContext):
    """
    Обработка ссылки Spotify.
    Парсит ссылку, скачивает треки и отправляет их медиагруппами.
    """
    url = message.text
    status_msg = await message.answer("Начинаю парсинг...")
    
    await state.clear()
    
    result = parse_spotify_link(url)
    
    if not result:
        await status_msg.edit_text(
            "Ошибка парсинга. Убедись, что ссылка ведет на "
            "трек, альбом или плейлист."
        )
        return

    link_type = result['type']
    title = result['title']
    tracks_list = result['tracks']
    cover_url = result.get('cover_url')
    total_tracks = len(tracks_list)
    
    type_names = {'track': 'трек', 'album': 'альбом', 'playlist': 'плейлист'}
    item_type_name = type_names.get(link_type, 'объект')
    
    await status_msg.edit_text(
        f"Найден {item_type_name}: *{title}*\n"
        f"Треков в очереди: {total_tracks}.\n\n"
        f"Начинаю загрузку пачками по 10 штук...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    success_count = 0
    chunk_size = 10
    chunks = [
        tracks_list[i:i + chunk_size] 
        for i in range(0, total_tracks, chunk_size)
    ]
    
    for chunk_index, chunk in enumerate(chunks, start=1):
        
        # Строим текст для пачки
        if len(chunks) > 1:
            group_caption = f"*{title}* (Часть {chunk_index}/{len(chunks)})"
        else:
            group_caption = f"*{title}*"
            
        # Билдер ТОЛЬКО для аудио
        media_group = MediaGroupBuilder()
        downloaded_filepaths = [] 
        
        for search_query in chunk:
            progress_msg = await message.answer(
                f"Качаю:\n_{search_query}_...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            track_data = await asyncio.to_thread(download_track, search_query)
            await progress_msg.delete()
            
            if track_data:
                filepath = track_data['filepath']
                downloaded_filepaths.append(filepath)
                
                # Добавляем аудио в группу
                media_group.add_audio(
                    media=FSInputFile(filepath),
                    title=track_data['sc_title'],       
                    performer=track_data['sc_uploader'] 
                )
                success_count += 1
                
        # Отправка
        if downloaded_filepaths:
            try:
                # СНАЧАЛА ОТПРАВЛЯЕМ ОБЛОЖКУ 
                # Отправляем ее только для первой пачки, чтобы не спамить
                if cover_url and chunk_index == 1:
                    await message.answer_photo(
                        photo=cover_url, 
                        caption=group_caption, 
                        parse_mode=ParseMode.MARKDOWN
                    )
                # Если обложки нет, или это вторая пачка треков, шлем текст
                elif not cover_url or chunk_index > 1:
                    await message.answer(
                        text=group_caption, 
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                # ЗАТЕМ ОТПРАВЛЯЕМ ПАЧКУ АУДИО
                await message.answer_media_group(media=media_group.build())
                
            except Exception as e:
                await message.answer(f"Ошибка отправки: {e}")
            finally:
                # Удаляем файлы
                for fp in downloaded_filepaths:
                    if os.path.exists(fp):
                        os.remove(fp)
                        
        # Задержка перед следующей пачкой во избежание флуд-контроля Telegram
        await asyncio.sleep(3)

    # Итог работы функции
    await message.answer(
        f"Готово! Успешно отправлено {success_count} из {total_tracks} треков."
    )

@router.message(FindTrack.wait_input)
async def text_search(message: Message, state: FSMContext):
    """
    Обрабатывает текстовый запрос пользователя (если это не ссылка).
    Ищет совпадения в Spotify и выдает Inline-кнопки.
    """
    query = message.text
    status_msg = await message.answer(f"Ищу в Spotify: _{query}_...", parse_mode=ParseMode.MARKDOWN)

    result = search_spotify_text(query)
    
    if not result:
        await status_msg.edit_text("Ничего не найдено")
        return
    
    builder_btn = InlineKeyboardBuilder()

    for index, item in enumerate(result):
        short_id = item['url'].split('spotify.com/')[-1]

        builder_btn.row(InlineKeyboardButton(
            text=item['name'],
            callback_data=f'dl_{short_id}'
        ))
    await status_msg.edit_text("Выберите нужный альбом/трек",
                               reply_markup=builder_btn.as_markup()
                               )
    await state.clear()

@router.callback_query(F.data.startswith("dl_"))
async def process_search_result(callback: CallbackQuery, state: FSMContext):
    """
    Реагирует на нажатие кнопки из результатов поиска.
    Перенаправляет бота на скачивание.
    """
    # Достаем короткий ID из кнопки
    short_id = callback.data.replace("dl_", "")
    
    # Превращаем его в нормальную ссылку Spotify
    full_spotify_url = f"https://open.spotify.com/{short_id}"
    
    # Убираем кнопки, чтобы юзер не нажал дважды
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # ИСПРАВЛЕНИЕ: Создаем "клон" сообщения с нужным нам текстом
    fake_message = callback.message.model_copy(update={"text": full_spotify_url})
    
    # Передаем этого клона в твою основную функцию скачивания
    await find_link(fake_message, state)
    
    # Говорим Телеграму, что нажатие обработано
    await callback.answer()



