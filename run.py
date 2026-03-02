import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from config import TOKEN
from app.handlers import router

session = AiohttpSession(timeout = 500) # для дольшего ожидания ответа, так как скачивание альбомов происходит долго

bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main()) 
    except KeyboardInterrupt: 
        print('Exit')
        
