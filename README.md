# Manga Image Scraper

Um spider Scrapy eficiente para baixar mangás pt-br, com suporte a coleta, downloads e monitoramento de atualizações.

## Funcionalidades

- 🔍 **Coleta de Séries**: Mapeia todas as séries disponíveis
- 📥 **Download em Lote**: Baixa múltiplas séries
- 🔄 **Sistema de Atualização**: Verifica e baixa novos capítulos
- 💾 **Cache Inteligente**: Evita downloads redundantes
- 📊 **Monitoramento**: Logs detalhados e relatórios de progresso

## Requisitos

### Python

- Python 3.9 ou superior

### Dependências

Instale todas as dependências necessárias usando:

```bash
pip install -r requirements.txt
```

### Principais Dependências

- **scrapy**: Framework de web scraping
- **pillow**: Processamento de imagens
- **scrapy-user-agents**: Rotação de User-Agents
- **tqdm**: Barras de progresso para downloads

### Dependências de Desenvolvimento

- **black**: Formatação de código
- **pylint**: Análise estática
- **mypy**: Verificação de tipos
- **pyflakes**: Verificação de código

### Ambiente Virtual (Recomendado)

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Verificando a Instalação

```bash
python -c "import scrapy; print(scrapy.__version__)"
```

Deve exibir a versão do Scrapy instalada.

Esta seção de requisitos mais detalhada no README ajuda os usuários a:

1. Entender todas as dependências necessárias
2. Configurar um ambiente virtual (prática recomendada)
3. Verificar se a instalação foi bem-sucedida
4. Identificar quais pacotes são para desenvolvimento

Além disso, o `requirements.txt` especifica as versões mínimas recomendadas para cada pacote, garantindo compatibilidade e funcionamento adequado do projeto.

## Estrutura do Projeto

```

scrapy/
├── scraper/
│ ├── spiders/
│ │ ├── **init**.py
│ │ ├── image_spider.py
│ │ └── series_spider.py
│ ├── **init**.py
│ ├── items.py
│ ├── middlewares.py
│ ├── pipelines.py
│ └── settings.py
├── downloads/ # Diretório onde os mangás são salvos
└── cache/ # Cache e logs do sistema

```

## Como Usar

### 1. Coletar Séries Disponíveis

```bash
scrapy crawl series_spider -a mode=collect
```

Este comando mapeia todas as séries disponíveis e as armazena no cache.

### 2. Baixar Séries

```bash
scrapy crawl series_spider -a mode=download
```

### 3. Verificar Atualizações

```bash
scrapy crawl series_spider -a mode=update
```

Verifica e baixa novos capítulos de séries já baixadas.

## Estrutura dos Downloads

```
downloads/
├── Nome_da_Serie_1/
│   ├── Capitulo_1/
│   │   ├── pagina_001.jpg
│   │   ├── pagina_002.jpg
│   │   └── ...
│   ├── Capitulo_2/
│   └── ...
├── Nome_da_Serie_2/
└── ...
```

## Cache e Logs

O sistema mantém vários arquivos de controle em `cache/`:

- `series_cache.json`: Lista de séries disponíveis
- `download_progress.json`: Progresso dos downloads
- `update_log.json`: Registro de atualizações
- `error_log.json`: Log de erros
- `stats_*.json`: Estatísticas de execução

## Monitoramento

### Logs em Tempo Real

```bash
tail -f cache/spider_*.log
```

### Relatórios

Após cada execução, um relatório detalhado é gerado em:

```
cache/report/report_[mode]_[timestamp].json
```

## Retomada de Downloads

O sistema mantém o estado dos downloads, permitindo retomar de onde parou em caso de interrupção.

## Tratamento de Erros

- Retry automático em caso de falhas
- Log detalhado de erros
- Backup automático do cache

## Configurações Avançadas

Edite `settings.py` para ajustar:

- Delays entre requisições
- Timeouts
- Configurações de proxy
- Headers personalizados
- Cache de requisições

## Resolução de Problemas

1. **Cache Corrompido**
   - O sistema usa backups automáticos
   - Apague manualmente arquivos corrompidos em `cache/`

## Contribuindo

1. Fork o repositório
2. Crie sua branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Notas

- Configure delays apropriados para evitar sobrecarga
- Mantenha backups dos arquivos importantes

## Suporte

Para problemas, dúvidas ou sugestões, abra uma issue no repositório.
