import platform
from datetime import date, timedelta
import aiohttp
import asyncio


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

        tasks = []
        async with aiohttp.ClientSession() as session:
            for i in range(days):
                # Додаэмо в список витягування котировок за кожний день. Кожен день - окрема асинхронна операція
                data_to_get = (self.today - timedelta(i)).strftime('%d.%m.%Y')
                url = f'{self.url}{data_to_get}'
                tasks.append(asyncio.create_task(self.get_one_day_rate(session, url)))
            # Виконуємо створений вище список задач
            await asyncio.gather(*tasks)

        await self.show_exchange_rate()

    async def get_one_day_rate(self, session, url):
        try:
            async with session.get(url) as response:
                one_day_request = await response.json()
                self.exchange_list.append(one_day_request)
        except aiohttp.ClientConnectorError:
            print(f'Connection error: {url}')
    async def show_exchange_rate(self):
        for one_day in sorted(self.exchange_list, key=lambda x: x['date']):
            print(f'Date: {one_day["date"]}')
            for currency in one_day['exchangeRate']:
                if currency['currency'] in self.currencies:
                    print(f'Val: {currency["currency"]} >> '
                          f'Sale: {currency["saleRateNB"]}, '
                          f'Buy: {currency["purchaseRateNB"]}')


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        days = int(input('Enter days: '))
        if days > 10:
            print('The maximum value can be no more than 10. Now it will be 10.')
            days = 10
        if days < 1:
            print('The minimum value can be at least 1. Now it will be 1.')
            days = 1
    except ValueError:
        print('Wrong days format. You can enter only numbers between 1 and 10 inclusive. Now it will be 1')
        days = 1

    currencies = input('What currencies would you like to see? (EUR and USD - default, if nothing enter): ')

    private = PrivateCurrencyChange(curs=currencies.split())
    asyncio.run(private.get_exchange_course(days))
