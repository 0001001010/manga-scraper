BOT_NAME = 'image_scraper'
SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'

# Configurações básicas
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Configurações de Middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scraper.middlewares.CustomRetryMiddleware': 100,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 400,
}

# Ajustes de concorrência
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 16

# Delays e timeouts
DOWNLOAD_DELAY = 0
RANDOMIZE_DOWNLOAD_DELAY = False
DOWNLOAD_TIMEOUT = 180

# Configurações de retry
RETRY_ENABLED = True
RETRY_TIMES = 10
RETRY_HTTP_CODES = [429, 500, 502, 503, 504, 522, 524, 408, 403, 404]
RETRY_DELAY = 5
RETRY_BACKOFF = True
RETRY_BACKOFF_MAX = 60
RETRY_PRIORITY_ADJUST = 2

# Cache
HTTPCACHE_ENABLED = False

# Headers e Cookies
COOKIES_ENABLED = True
COOKIES_DEBUG = False
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

# Autothrottle
AUTOTHROTTLE_ENABLED = False
AUTOTHROTTLE_START_DELAY = 0
AUTOTHROTTLE_MAX_DELAY = 0.1
AUTOTHROTTLE_TARGET_CONCURRENCY = 16.0
AUTOTHROTTLE_DEBUG = True

# Configurações de Download
IMAGES_STORE = 'downloads'
MEDIA_ALLOW_REDIRECTS = True
IMAGES_URLS_FIELD = 'image_urls'
IMAGES_RESULT_FIELD = 'images'
IMAGES_EXPIRES = 365

# Pipelines
ITEM_PIPELINES = {
    'scraper.pipelines.ImageValidationPipeline': 100,
    'scraper.pipelines.ImageDownloadPipeline': 200,
    'scraper.pipelines.ChecksumPipeline': 300,
}

# Otimizações gerais
ROBOTSTXT_OBEY = False
DOWNLOAD_MAXSIZE = 52428800
DOWNLOAD_WARNSIZE = 20971520
DOWNLOAD_FAIL_ON_DATALOSS = False
REDIRECT_MAX_TIMES = 10
REDIRECT_ENABLED = True
REACTOR_THREADPOOL_MAXSIZE = 50
DNSCACHE_ENABLED = False
AJAXCRAWL_ENABLED = True
LOG_LEVEL = 'INFO'
DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'
DUPEFILTER_DEBUG = False
TELNETCONSOLE_ENABLED = False

# Otimizações de memória e performance
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 4096
MEMUSAGE_CHECK_INTERVAL_SECONDS = 60
MEMDEBUG_ENABLED = False

# Otimizações de scheduler
SCHEDULER_PRIORITY_QUEUE = 'scrapy.pqueues.DownloaderAwarePriorityQueue'
SCHEDULER = 'scrapy.core.scheduler.Scheduler'
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
DEPTH_PRIORITY = 1

# Configurações de compressão
COMPRESSION_ENABLED = True

# Configurações de estatísticas
STATS_DUMP = True
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'

# Configurações de codificação
FEED_EXPORT_ENCODING = 'utf-8'
