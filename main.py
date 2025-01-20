import argparse
import asyncio
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.series_spider import SeriesSpider
import os
import requests
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MangaScraper:
    def __init__(self):
        self.settings = get_project_settings()
        self.process = CrawlerProcess(self.settings)
        self.results = []

    def setup_crawler(self):
        self.process.crawl(
            SeriesSpider,
            start_url='https://hiper.cool/',
            callback=self.handle_item
        )

    def handle_item(self, item):
        """Callback para processar cada item raspado"""
        self.results.append(item)
        logger.info(f"Capturado: {item['series_title']} - Capítulo {item['chapter']}")

    def download_images(self, output_dir="downloads"):
        """Download das imagens capturadas"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for item in self.results:
            series_dir = Path(output_dir) / item['series_title']
            chapter_dir = series_dir / f"capitulo_{item['chapter']}"
            chapter_dir.mkdir(parents=True, exist_ok=True)

            for image in item['images']:
                image_path = chapter_dir / f"pagina_{image['page']:03d}.jpg"

                try:
                    response = requests.get(image['url'], timeout=30)
                    if response.status_code == 200:
                        image_path.write_bytes(response.content)
                        logger.info(f"Baixado: {image_path}")
                    else:
                        logger.error(f"Erro ao baixar {image['url']}: {response.status_code}")
                except Exception as e:
                    logger.error(f"Falha ao baixar {image['url']}: {str(e)}")

    def run(self):
        """Executa o scraping"""
        logger.info("Iniciando scraping...")
        self.setup_crawler()
        self.process.start()

        if self.results:
            logger.info("Iniciando download das imagens...")
            self.download_images()
        else:
            logger.warning("Nenhum resultado encontrado")

def main():
    parser = argparse.ArgumentParser(description='Manga Image Scraper')
    parser.add_argument('--output', '-o', default='downloads',
                      help='Diretório de saída para as imagens (padrão: downloads)')
    args = parser.parse_args()

    scraper = MangaScraper()
    scraper.run()

if __name__ == "__main__":
    main()
