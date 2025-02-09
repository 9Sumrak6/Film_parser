import scrapy

class MovieParserItem(scrapy.Item):
    title = scrapy.Field()
    genre = scrapy.Field()
    director = scrapy.Field()
    country = scrapy.Field()
    year = scrapy.Field()
    imdb_rating = scrapy.Field()
