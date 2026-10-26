# Portal de Imóveis

Agrega anúncios de imóveis de portais parceiros em um catálogo único e expõe esse
catálogo por uma API REST.

Cada portal parceiro publica seu catálogo em um formato próprio. Um importador por
portal busca esses dados, normaliza e grava na nossa base. Os importadores rodam
periodicamente via Celery Beat.

Hoje existe um portal integrado: o **Portal Nexo**, que publica o catálogo em um
arquivo XML regenerado de madrugada. O feed do Nexo fica em `data/nexo_catalogo.xml`.

## Como subir

```bash
cp .env.example .env
docker compose up -d
docker compose exec web python manage.py migrate
```

A API fica em `http://localhost:8000/api/properties/` e o admin em
`http://localhost:8000/admin/`.

Para rodar um import manualmente:

```bash
docker compose exec web python manage.py shell -c \
  "from apps.properties.tasks import import_nexo_properties; import_nexo_properties()"
```

## Testes

Os testes usam o Postgres do compose:

```bash
docker compose up -d db
uv run pytest src
```

Fora o banco, a suíte não depende de rede nem de API externa.

## Mapa do código

```
data/                           feeds publicados pelos portais parceiros
└── nexo_catalogo.xml

src/
├── config/                     configuração do Django e do Celery
│   ├── settings.py             inclui CELERY_BEAT_SCHEDULE
│   └── celery.py
├── apps/properties/
│   ├── models/
│   │   ├── property.py         o anúncio normalizado
│   │   ├── property_photo.py   as fotos de cada anúncio
│   │   └── import_run.py       registro de cada execução de import
│   ├── services/
│   │   ├── importers/          um importador por portal parceiro
│   │   │   └── nexo.py
│   │   └── processing.py       processamento noturno do catálogo
│   ├── tasks/                  entrypoints assíncronos
│   └── api/                    serializers, filtros e viewsets
└── tests/
    └── fixtures/               recortes de catálogo usados nos testes
```

## Fluxo de importação

1. O Celery Beat dispara a task do portal no horário agendado.
2. A task instancia o importador correspondente e chama `run()`.
3. O importador abre um `ImportRun`, lê o catálogo publicado pelo portal e percorre os anúncios.
4. Cada anúncio é validado, normalizado e gravado — criado se for novo, atualizado
   se já tiver sido importado antes.
5. O `ImportRun` é fechado com os contadores da execução.

Anúncios que não estão mais disponíveis no portal continuam na base, marcados como
inativos, e deixam de aparecer na API.

## Convenções

- Python 3.11, código tipado, `ruff` para formatação e lint.
- Testes com pytest, em funções (não em classes), com mock em toda chamada externa.
