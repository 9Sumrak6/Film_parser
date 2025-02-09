import scrapy
from scrapy.http import Request
from movie_parser.items import MovieParserItem
from scrapy.exceptions import CloseSpider
import time


class MovieSpider(scrapy.Spider):
    name = "movie_spider"
    allowed_domains = ["ru.wikipedia.org", "www.imdb.com"]
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"]

    def parse(self, response):
        # Собираем ссылки на фильмы
        for i, movie_link in enumerate(response.css('div.mw-category-group ul li a::attr(href)').getall()):
            if i < 2:
                continue
            movie_url = response.urljoin(movie_link)
            # print(i, movie_url)
            yield Request(movie_url, callback=self.parse_movie)


        # Переход на следующую страницу категории, если есть
        next_page = response.css('a:contains("Следующая страница")::attr(href)').get()
        if next_page:
            yield Request(url=f"https://ru.wikipedia.org/{next_page}", callback=self.parse)

    def parse_movie(self, response):
        item = MovieParserItem()

        # Название фильма
        item['title'] = response.xpath('//h1[@id="firstHeading"]/span/text()').get()

        # Жанр
        item['genre'] = response.css('th:contains("Жанр") + td a::text').getall()
        if not item['genre']:
            item['genre'] = response.css('th:contains("Жанры") + td a::text').getall()

        # Режиссер
        item['director'] = response.css('th:contains("Режиссёр") + td a::text').getall()
        if not item['director']:
            item['director'] = response.css('th:contains("Режиссёры") + td a::text').getall()

        # Страна
        item['country'] = response.css('th:contains("Страна") + td a::text').getall()
        if not item['country']:
            item['country'] = response.css('th:contains("Страны") + td a::text').getall()
        if not item['country']:
            item['country'] = response.css('th:contains("Страна") + td span span span a span::text').getall()

        # Год
        item['year'] = " ".join(response.css('th:contains("Год") + td span span span a::text').getall())
        if not item['year']:
            item['year'] = " ".join(response.css("td.plainlist span.dtstart::text").getall())
        if not item['year']:
            item['year'] = ", ".join(response.css('th:contains("Дата выхода") + td::text').getall())

        # Ссылка на IMDb
        imdb_link = response.css('a.extiw[href*="imdb.com"]::attr(href)').get()
        if imdb_link:
            # Переходим на страницу IMDb для сбора рейтинга
            yield Request(
                url=imdb_link,
                callback=self.get_imdb_rating,
                cb_kwargs={'item': item},
            )
        else:
            # Если ссылки на IMDb нет, устанавливаем рейтинг как '-'
            item['imdb_rating'] = '-'
        yield item

    def get_imdb_rating(self, response, item):
        # Сбор рейтинга IMDb
        item['imdb_rating'] = response.css(
            'div[data-testid="hero-rating-bar__aggregate-rating__score"] span::text'
        ).get()
        yield item

    # def handle_imdb_error(self, failure, item):
        # Обработка ошибок при запросе к IMDb
        # self.logger.error(f"Failed to fetch IMDb page: {failure}")
        # item['imdb_rating'] = '-'  # Устанавливаем рейтинг как '-' в случае ошибки
        # yield item
