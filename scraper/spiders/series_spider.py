import scrapy
import re
from collections import deque
from urllib.parse import urljoin
from ..items import ChapterItem
import os
import json
from datetime import datetime
from scrapy.http.response.text import TextResponse
from typing import Set

class SeriesSpider(scrapy.Spider):
    name = 'series_spider'

    def __init__(self, start_page=1, mode='collect', *args, **kwargs):
        super(SeriesSpider, self).__init__(*args, **kwargs)
        self.base_url = 'https://hiper.cool/manga/'
        self.current_page = int(start_page)
        self.allowed_domains = ['hiper.cool']
        self.order_param = 'm_orderby=views'
        self.mode = mode

        # Diretórios de cache
        self.cache_dir = 'cache'
        self.report_dir = os.path.join(self.cache_dir, 'report')

        # Cria diretórios necessários
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)

        # Estruturas de cache
        self.series_cache = self.load_cache('series_cache.json', {'series': [], 'last_update': None})
        self.download_progress = self.load_cache('download_progress.json', {'completed': [], 'in_progress': None})

        # Fila de séries
        self.series_queue = deque()

        # Métricas e monitoramento
        self.stats = {
            'start_time': datetime.now(),
            'processed_series': 0,
            'downloaded_chapters': 0,
            'failed_downloads': 0,
            'total_bytes': 0
        }

    def load_cache(self, filename: str, default: dict) -> dict:
        """Carrega cache com tratamento de erro e backup"""
        filepath = os.path.join(self.cache_dir, filename)
        backup_filepath = f"{filepath}.backup"

        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            self.logger.error(f"Erro ao carregar {filename}, tentando backup...")
            if os.path.exists(backup_filepath):
                with open(backup_filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)

        return default

    def save_cache(self, data: dict, filename: str):
        """Salva cache com backup"""
        filepath = os.path.join(self.cache_dir, filename)
        backup_filepath = f"{filepath}.backup"

        # Cria backup do arquivo existente
        if os.path.exists(filepath):
            os.replace(filepath, backup_filepath)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def start_requests(self):
        """Inicia o spider baseado no modo de operação"""
        if self.mode == 'collect':
            url = f"{self.base_url}?{self.order_param}"
            if self.current_page > 1:
                url = f"{self.base_url}page/{self.current_page}/?{self.order_param}"

            self.logger.info(f"Iniciando coleta de séries a partir de: {url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse_series_list,
                errback=self.handle_error,
                dont_filter=True,
                meta={'dont_cache': False}
            )

        elif self.mode == 'download':
            self.logger.info("Iniciando downloads de séries em cache")
            yield from self.start_downloads()

        elif self.mode == 'update':
            self.logger.info("Iniciando verificação de atualizações")
            yield from self.start_updates()

    def parse_series_list(self, response):
        """Parse otimizado da lista de séries"""
        self.logger.info(f"Analisando página {self.current_page} - URL: {response.url}")

        series_links = set(
            urljoin(self.base_url, link.strip())
            for link in response.css('div.page-listing-item a::attr(href)').getall()
            if '/manga/' in link and not any(x in link for x in ['/capitulo-', '/vol-'])
        )

        self.logger.info(f"Página {self.current_page}: Encontradas {len(series_links)} séries")

        new_series = series_links - set(self.series_cache['series'])
        if new_series:
            self.series_cache['series'].extend(new_series)
            self.save_cache(self.series_cache, 'series_cache.json')
            self.logger.info(f"Página {self.current_page}: Adicionadas {len(new_series)} novas séries ao cache")
        else:
            self.logger.info(f"Página {self.current_page}: Nenhuma série nova encontrada")

        next_page = response.css('a.nextpostslink::attr(href)').get()
        if next_page:
            self.current_page += 1
            next_url = f"{self.base_url}page/{self.current_page}/?{self.order_param}"
            self.logger.info(f"Movendo para próxima página: {next_url}")
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_series_list,
                errback=self.handle_error
            )
        else:
            self.logger.info(f"Coleta concluída! Total de {len(self.series_cache['series'])} séries no cache")

    def start_downloads(self):
        """Inicia o processo de download das séries"""
        completed_series = set(self.download_progress['completed'])
        pending_series = [s for s in self.series_cache['series'] if s not in completed_series]

        if not pending_series:
            self.logger.info("Não há novas séries para baixar")
            return

        if self.download_progress['in_progress']:
            current_series = self.download_progress['in_progress']
            self.logger.info(f"Retomando downloads a partir de: {current_series}")
        else:
            current_series = pending_series[0]
            self.download_progress['in_progress'] = current_series
            self.save_cache(self.download_progress, 'download_progress.json')

        yield scrapy.Request(
            url=current_series,
            callback=self.parse_series,
            errback=self.handle_error,
            meta={'series_index': pending_series.index(current_series)}
        )

    def start_updates(self):
        """Inicia o processo de verificação de atualizações"""
        completed_series = self.download_progress['completed']
        if not completed_series:
            self.logger.info("Não há séries baixadas para verificar atualizações")
            return

        self.logger.info(f"Verificando atualizações para {len(completed_series)} séries")

        # Cria um novo arquivo de log para as atualizações
        self.update_log = {
            'started': datetime.now().isoformat(),
            'updates': []
        }

        # Verifica cada série completada
        for series_url in completed_series:
            yield scrapy.Request(
                url=series_url,
                callback=self.check_series_updates,
                errback=self.handle_error,
                meta={'update_mode': True},
                dont_filter=True
            )

    def check_series_updates(self, response):
        """Verifica se há novos capítulos para uma série"""
        series_title = response.css('h1::text').get('').strip()

        # Obtém o caminho da série
        clean_name = self.clean_title(series_title)
        series_path = os.path.join('downloads', clean_name)

        # Processa capítulos disponíveis
        chapter_links = response.css('a[href*="/capitulo-"]::attr(href), a[href*="/vol-"]::attr(href)').getall()
        chapter_links = list(set(chapter_links))

        # Mapeia capítulos já baixados
        downloaded_chapters = self.get_downloaded_chapters(series_path)

        # Filtra e identifica novos capítulos
        new_chapters = []
        for link in chapter_links:
            match = re.search(r'(?:capitulo|vol)-(\d+(?:\.\d+)?)', link, re.IGNORECASE)
            if match and float(match.group(1)) not in downloaded_chapters:
                new_chapters.append(link)

        if new_chapters:
            # Ordena os novos capítulos
            new_chapters.sort(key=lambda x: float(re.search(r'(?:capitulo|vol)-(\d+(?:\.\d+)?)', x).group(1)))

            self.logger.info(f"[{series_title}] Encontrados {len(new_chapters)} novos capítulos")

            # Registra a atualização no log
            self.update_log['updates'].append({
                'series': series_title,
                'url': response.url,
                'new_chapters': len(new_chapters),
                'timestamp': datetime.now().isoformat()
            })

            # Salva o log de atualização
            with open(os.path.join(self.report_dir, 'update_log.json'), 'w', encoding='utf-8') as f:
                json.dump(self.update_log, f, indent=2)

            # Inicia o download dos novos capítulos
            yield from self._crawl_next_unit(series_title, new_chapters, 0, response.url)
        else:
            self.logger.info(f"[{series_title}] Nenhum novo capítulo encontrado")

    def parse_series(self, response):
        """Parse da página da série para coletar capítulos"""
        series_title = response.css('h1::text').get('').strip()

        # Preparação do diretório
        clean_name = self.clean_title(series_title)
        series_path = os.path.join('downloads', clean_name)

        # Coleta todos os links de capítulos
        chapter_links = response.css('a[href*="/capitulo-"]::attr(href), a[href*="/vol-"]::attr(href)').getall()
        chapter_links = list(set(chapter_links))

        # Filtra e ordena capítulos
        numeric_links = []
        for link in chapter_links:
            match = re.search(r'(?:capitulo|vol)-(\d+(?:\.\d+)?)', link, re.IGNORECASE)
            if match:
                numeric_links.append(link.strip())

        numeric_links.sort(key=lambda x: float(re.search(r'(?:capitulo|vol)-(\d+(?:\.\d+)?)', x).group(1)))

        if numeric_links:
            # Verifica capítulos já baixados
            downloaded_chapters = self.get_downloaded_chapters(series_path)

            # Filtra capítulos pendentes
            pending_chapters = []
            for link in numeric_links:
                match = re.search(r'(?:capitulo|vol)-(\d+(?:\.\d+)?)', link, re.IGNORECASE)
                if match and float(match.group(1)) not in downloaded_chapters:
                    pending_chapters.append(link)

            if pending_chapters:
                yield from self._crawl_next_unit(series_title, pending_chapters, 0, response.url)
            else:
                # Série completa
                self.download_progress['completed'].append(response.url)
                self.download_progress['in_progress'] = None
                self.save_cache(self.download_progress, 'download_progress.json')
                self.stats['processed_series'] += 1

                # Próxima série
                yield from self.process_next_series(response)

    def _crawl_next_unit(self, series_title, unit_links, index, original_url):
        """Processa próximo capítulo/volume"""
        if index < len(unit_links):
            next_unit_url = urljoin(self.base_url, unit_links[index])
            yield scrapy.Request(
                url=next_unit_url,
                callback=self.parse_chapter_or_volume,
                errback=self.handle_error,
                meta={
                    'series_title': series_title,
                    'unit_links': unit_links,
                    'index': index,
                    'original_url': original_url,
                    'update_mode': self.mode == 'update'
                }
            )
        else:
            if self.mode != 'update':
                self.download_progress['completed'].append(original_url)
                self.download_progress['in_progress'] = None
                self.save_cache(self.download_progress, 'download_progress.json')

            response = TextResponse(url=original_url)
            yield from self.process_next_series(response)

    def parse_chapter_or_volume(self, response):
        """Parse do capítulo/volume para coletar imagens"""
        series_title = response.meta['series_title']
        unit_links = response.meta['unit_links']
        index = response.meta['index']
        original_url = response.meta['original_url']

        match = re.search(r'(?:capitulo|vol)-(\d+(?:\.\d+)?)', response.url, re.IGNORECASE)
        unit_number = match.group(1) if match else str(index + 1)

        images = self.extract_images(response)

        if images:
            self.stats['downloaded_chapters'] += 1

            yield ChapterItem(
                chapter=unit_number,
                url=response.url,
                image_count=len(images),
                images=images,
                series_title=series_title
            )

            # Próximo capítulo
            yield from self._crawl_next_unit(series_title, unit_links, index + 1, original_url)
        else:
            self.logger.warning(f"[{series_title}] Unidade {unit_number}: nenhuma imagem encontrada")
            # Tenta próximo capítulo mesmo sem imagens
            yield from self._crawl_next_unit(series_title, unit_links, index + 1, original_url)

    def extract_images(self, response) -> list:
        """Extração otimizada de imagens"""
        images = []
        page_number = 1

        for i in range(1, 300):
            padded_num = str(i).zfill(2)
            sel_full = response.css(f'#image-{padded_num}')
            sel_short = response.css(f'#image-{i}')

            if not sel_full and not sel_short:
                break

            sel = sel_full if sel_full else sel_short
            img_url = sel.xpath('@src').get()

            if img_url:
                images.append({
                    'url': urljoin(response.url, img_url.strip()),
                    'page': page_number
                })
                page_number += 1

        return images

    def process_next_series(self, response):
        """Processa próxima série pendente"""
        if self.mode == 'update':
            return

        current_url = response.url
        try:
            current_index = self.series_cache['series'].index(current_url)
            next_index = current_index + 1

            if next_index < len(self.series_cache['series']):
                next_series = self.series_cache['series'][next_index]
                if next_series not in self.download_progress['completed']:
                    self.download_progress['in_progress'] = next_series
                    self.save_cache(self.download_progress, 'download_progress.json')

                    yield scrapy.Request(
                        url=next_series,
                        callback=self.parse_series,
                        errback=self.handle_error,
                        meta={'series_index': next_index}
                    )
                else:
                    response = TextResponse(url=next_series)
                    yield from self.process_next_series(response)
            else:
                self.logger.info("Todas as séries foram processadas")
        except ValueError:
            self.logger.error(f"Série não encontrada no cache: {current_url}")

    def get_downloaded_chapters(self, series_path: str) -> Set[float]:
        """Retorna conjunto de capítulos já baixados"""
        downloaded = set()
        if os.path.exists(series_path):
            for item in os.listdir(series_path):
                if match := re.search(r'Capitulo_(\d+(?:\.\d+)?)', item):
                    try:
                        downloaded.add(float(match.group(1)))
                    except ValueError:
                        self.logger.warning(f"Número de capítulo inválido: {item}")
        return downloaded

    def handle_error(self, failure):
        """Tratamento de erros de requisição"""
        self.stats['failed_downloads'] += 1
        request = failure.request

        error_data = {
            'url': request.url,
            'error': str(failure.value),
            'timestamp': datetime.now().isoformat()
        }

        error_log_file = os.path.join(self.report_dir, 'error_log.json')
        try:
            if os.path.exists(error_log_file):
                with open(error_log_file, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            else:
                errors = []

            errors.append(error_data)

            with open(error_log_file, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao salvar log de erro: {str(e)}")

    def clean_title(self, title: str) -> str:
        """Limpa o título da série para uso em nome de arquivo/diretório"""
        return "".join(c if c.isalnum() or c in ('-_ ') else '_' for c in title)

    def closed(self, reason):
        """Finalização com relatório detalhado"""
        self.save_cache(self.series_cache, 'series_cache.json')
        self.save_cache(self.download_progress, 'download_progress.json')

        duration = datetime.now() - self.stats['start_time']

        report = {
            'mode': self.mode,
            'duration': str(duration),
            'processed_series': self.stats['processed_series'],
            'downloaded_chapters': self.stats['downloaded_chapters'],
            'failed_downloads': self.stats['failed_downloads'],
            'total_bytes': self.stats['total_bytes'],
            'average_speed': f"{self.stats['total_bytes']/duration.total_seconds()/1024:.2f} KB/s" if duration.total_seconds() > 0 else "N/A",
            'finish_reason': reason,
            'timestamp': datetime.now().isoformat()
        }

        report_file = os.path.join(
            self.report_dir,
            f'report_{self.mode}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Spider finalizado: {report}")
