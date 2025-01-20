import scrapy

class ImageItem(scrapy.Item):
    image_url = scrapy.Field()
    source_url = scrapy.Field()
    filename = scrapy.Field()
    path = scrapy.Field()
    checksum = scrapy.Field()
    status = scrapy.Field()
    timestamp = scrapy.Field()

class ChapterItem(scrapy.Item):
    chapter = scrapy.Field()
    url = scrapy.Field()
    image_count = scrapy.Field()
    images = scrapy.Field()
    series_title = scrapy.Field()
    # Campos usados pelo pipeline (baixar imagens, cálculo de checksum, etc.)
    path = scrapy.Field()
    status = scrapy.Field()
    timestamp = scrapy.Field()
    checksum = scrapy.Field()

class SeriesItem(scrapy.Item):
    series_title = scrapy.Field()
    series_url = scrapy.Field()
    chapters = scrapy.Field()
    total_chapters = scrapy.Field()
