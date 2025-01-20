import hashlib
from datetime import datetime
import os
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.python import to_bytes
import scrapy
from scraper.items import ChapterItem
import logging
import mimetypes
from typing import List

class ImageValidationPipeline:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item, spider):
        if isinstance(item, ChapterItem):
            if not item['images']:
                raise DropItem("Capítulo sem imagens")
        return item

class ImageDownloadPipeline(ImagesPipeline):
    def __init__(self, store_uri, download_func=None, settings=None):
        super().__init__(store_uri, download_func=download_func, settings=settings)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _fingerprint(self, request):
        """Gera um fingerprint para o request"""
        return hashlib.sha1(to_bytes(request.url)).hexdigest()

    def get_media_requests(self, item, info) -> List[scrapy.Request]:
        requests = []
        if isinstance(item, ChapterItem):
            for image in item['images']:
                headers = {
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://hiper.cool/',
                    'Origin': 'https://hiper.cool',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }

                requests.append(scrapy.Request(
                    url=image['url'],
                    headers=headers,
                    meta={
                        'series_title': item['series_title'],
                        'chapter_number': item['chapter'],
                        'page': image['page'],
                        'dont_redirect': False,
                        'handle_httpstatus_list': [301, 302],
                        'original_url': image['url']
                    },
                    dont_filter=True
                ))
        return requests

    def file_path(self, request, response=None, info=None, *, item=None):
        try:
            series_title = request.meta['series_title']
            chapter_number = request.meta['chapter_number']
            page_number = request.meta['page']

            # Limpa o nome da série
            clean_series_title = "".join(c if c.isalnum() or c in (' -_') else '_' for c in series_title)

            # Determina a extensão do arquivo
            if response and response.headers.get('Content-Type'):
                content_type = response.headers['Content-Type'].decode('utf-8')
                ext = mimetypes.guess_extension(content_type) or '.jpg'
            else:
                ext = os.path.splitext(request.meta['original_url'])[1]
                if not ext:
                    ext = '.jpg'
                elif ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    ext = '.jpg'

            # Remove o ponto inicial da extensão se existir
            ext = ext.lstrip('.')

            # Define o caminho do arquivo
            filename = f"{clean_series_title}/Capitulo_{chapter_number}/pagina_{str(page_number).zfill(3)}.{ext}"

            return filename
        except Exception as e:
            self.logger.error(f"Erro ao gerar caminho do arquivo: {e}")
            return f"error/image_{self._fingerprint(request)}.jpg"

    def item_completed(self, results, item, info):
        if isinstance(item, ChapterItem):
            image_paths = [x['path'] for ok, x in results if ok]
            failed_images = [x for ok, x in results if not ok]

            if failed_images:
                self.logger.error(f"Falha ao baixar {len(failed_images)} imagens do capítulo {item['chapter']} de {item['series_title']}")

            if not image_paths:
                raise DropItem(f"Nenhuma imagem baixada para o capítulo {item['chapter']} de {item['series_title']}")

            item['path'] = image_paths
            item['status'] = 'downloaded'
            item['timestamp'] = datetime.now().isoformat()

            self.logger.info(f"Baixadas {len(image_paths)} imagens para {item['series_title']} - Capítulo {item['chapter']}")

        return item

class ChecksumPipeline:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item, spider):
        if isinstance(item, ChapterItem) and item.get('path'):
            # Calcula o checksum baseado nos caminhos das imagens
            combined = ''.join(item['path']).encode('utf-8')
            item['checksum'] = hashlib.md5(combined).hexdigest()
        return item
