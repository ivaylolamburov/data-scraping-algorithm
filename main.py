from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd

SEARCH_FOR = 'cannabis clubs'
FILE = 'cities.txt'

with open(FILE, 'r') as read_file:  # if you have no file, you can manually write them in CITIES
    CITIES = [city.replace('\n', '') for city in read_file.readlines()]
    read_file.close()

IN_ONE_FILE = False


@dataclass
class Business:
    city: str = None
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None


@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)

    def dataframe(self):
        return pd.json_normalize([asdict(business) for business in self.business_list], sep='_')


def main():
    directory = ''

    if IN_ONE_FILE:
        writer = pd.ExcelWriter(f'{SEARCH_FOR.replace(" ", "_")}.xlsx')
    else:
        from pathlib import Path
        directory = Path(f'{SEARCH_FOR.replace(" ", "_")}/')
        directory.mkdir(exist_ok=True)

    for city in CITIES:
        search = f'{SEARCH_FOR} in {city}'
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)  # headless can be removed
            page = browser.new_page()

            page.goto('https://www.google.com/maps', timeout=60_000)
            page.wait_for_timeout(5)

            page.locator('(//button[@jsname="b3VHJd"])[1]').click()

            page.locator('//input[@id="searchboxinput"]').fill(search)

            page.keyboard.press('Enter')
            page.wait_for_timeout(2_000)

            page.hover('(//a[contains(@href, "https://www.google.com/maps/place")])[1]')

            while True:
                if page.locator('//span[@class="HlvSq"]').count() > 0:
                    listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                    break

                page.mouse.wheel(0, 10000)
                page.wait_for_timeout(5_000)

            business_list = BusinessList()
            for listing in listings:
                listing.click()
                page.wait_for_timeout(3_000)

                name_xpath = '//h1[@class="DUwDvf lfPIob"]'
                address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, ' \
                                     '"fontBodyMedium")] '

                business = Business()

                business.city = city

                if page.locator(name_xpath).count() > 0:
                    business.name = page.locator(name_xpath).inner_text()
                else:
                    continue

                if page.locator(address_xpath).count() > 0:
                    business.address = page.locator(address_xpath).inner_text()
                else:
                    continue

                if page.locator(website_xpath).count() > 0:
                    business.website = page.locator(website_xpath).inner_text()
                else:
                    business.website = ''

                # sometimes goes off for no particular reason
                if page.locator(phone_number_xpath).count() > 0:
                    business.phone_number = page.locator(phone_number_xpath).inner_text()
                else:
                    business.phone_number = ''

                if business not in business_list.business_list:
                    business_list.business_list.append(business)

            if not IN_ONE_FILE:
                writer = directory / f'{city.replace(" ", "_")}.xlsx'

            business_list.dataframe().to_excel(writer, sheet_name=city, index=False)

            browser.close()

    if IN_ONE_FILE:
        writer.close()


if __name__ == '__main__':
    main()
