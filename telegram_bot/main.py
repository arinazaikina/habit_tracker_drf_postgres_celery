from aiogram import executor

import handlers  # noqa
from bot import dp

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
