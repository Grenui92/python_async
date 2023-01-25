import platform
from datetime import date, timedelta, datetime
import aiohttp
import asyncio
import aiofile


class PrivateCurrencyChange:

    def __init__(self, curs):
        self.currencies: set = {'EUR', 'USD'}
        if isinstance(curs, str):
            self.currencies.add(curs)
        elif isinstance(curs, list):
            self.currencies.update(curs)

        self.exchange_list = []  # тут ми зберігатимемо отримані результати за кожен день
        self.url = 'https://api.privatbank.ua/p24api/exchange_rates?date='
        self.today = date.today()

    async def get_exchange_course(self, days: int):
        await self.log_to_file(f'{datetime.now()}--Begin connection to PrivatBank with var: days = {days} and currencies = {self.currencies}\n')
        tasks = []
        async with aiohttp.ClientSession() as session:
            await self.log_to_file(f'{datetime.now()}--Connection create\n')
            for i in range(days):
                # Додаэмо в список витягування котировок за кожний день. Кожен день - окрема асинхронна операція
                data_to_get = (self.today - timedelta(i)).strftime('%d.%m.%Y')
                url = f'{self.url}{data_to_get}'
                tasks.append(asyncio.create_task(self.get_one_day_rate(session, url)))
            # Виконуємо створений вище список задач
            await asyncio.gather(*tasks)

        return await self.show_exchange_rate()

    async def get_one_day_rate(self, session, url):
        try:
            async with session.get(url) as response:
                await self.log_to_file(f'{datetime.now()}--session with {url} successfully create\n')
                one_day_request = await response.json()
                self.exchange_list.append(one_day_request)
                await self.log_to_file(f'{datetime.now()}--session with {url} successfully end\n')
        except aiohttp.ClientConnectorError:
            await self.log_to_file(f'{datetime.now()}--Connection error: {url}\n')

    async def show_exchange_rate(self):
        result = ''
        for one_day in sorted(self.exchange_list, key=lambda x: x['date']):
            result += f'Date: {one_day["date"]}\n'
            for currency in one_day['exchangeRate']:
                if currency['currency'] in self.currencies:
                    try:
                        result += f'Val: {currency["currency"]} >> Sale: {currency["saleRate"]}, Buy: {currency["purchaseRate"]}\n'
                    except KeyError:
                        result += f'We dont have {currency["currency"]} in our bank now, but we can show NB exchange rate.\n' \
                                  f'Val: {currency["currency"]} >> Sale: {currency["saleRateNB"]}, Buy: {currency["purchaseRateNB"]}\n'
        return result

    async def log_to_file(self, text):
        try:
            async with aiofile.async_open('py_loger.log', 'a') as file:
                await file.write(text)
        except FileNotFoundError:
            async with aiofile.async_open('py_loger.log', 'w') as file:
                await file.write(text)


async def main(days_from_chat, currencies):
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        days = int(days_from_chat)
        assert 0<days<11
    except (ValueError, AssertionError):
        return 'Wrong days format. You can enter only numbers between 1 and 10 inclusive.'

    private = PrivateCurrencyChange(curs=currencies)
    exchange_rate = await private.get_exchange_course(days)

    return exchange_rate
