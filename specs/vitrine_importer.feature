# language: pt
@bdd @importer @vitrine
Funcionalidade: Importador Vitrine Imóveis
  Como um agregador de anúncios do Portal de Imóveis
  Eu quero importar e sincronizar o catálogo JSON publicado pelo portal Vitrine Imóveis
  Para que os imóveis disponíveis fiquem atualizados, com preços corretos, inativados quando saírem do ar e com fotos ordenadas

  Regra: Importação, precisão financeira e validação do catálogo JSON

    @json @price
    Cenário: Importação inicial cria imóveis válidos com preços precisos a partir do catálogo JSON do Vitrine Imóveis
      Dado que o caminho do feed JSON aponta para a fixture do Vitrine Imóveis
      Quando o VitrineImporter executa a importação do catálogo JSON
      Então a execução do Vitrine fecha com status "SUCCESS" e 3 imóveis criados
      E a base de dados persiste 3 anúncios da fonte VITRINE com o imóvel "VT-4471" custando "845000.00"

    @validation @price
    Cenário: Importador do Vitrine ignora anúncio sem preço sem abortar o lote
      Dado que o caminho do feed JSON aponta para a fixture do Vitrine Imóveis
      Quando o VitrineImporter executa a importação do catálogo JSON
      Então o contador skipped_count do Vitrine registra 1 anúncio descartado
      E o anúncio sem preço "VT-4802" não é gravado na tabela Property

    @availability @inactive
    Cenário: Anúncio marcado como vendido no JSON do Vitrine é salvo como inativo
      Dado que o caminho do feed JSON aponta para a fixture do Vitrine Imóveis
      Quando o VitrineImporter executa a importação do catálogo JSON
      Então o imóvel vendido "VT-4519" fica persistido com is_active falso
      E o imóvel ativo "VT-4471" permanece com is_active verdadeiro

    @availability @inactive
    Cenário: Anúncio do Vitrine removido do JSON em carga subsequente é marcado como inativo
      Dado que o caminho do feed JSON aponta para a fixture do Vitrine Imóveis
      E que o anúncio "VT-4744" do Vitrine estava ativo na base após uma carga anterior
      Quando o VitrineImporter executa a importação do catálogo JSON
      Então o imóvel removido "VT-4744" fica persistido com is_active falso
      E o imóvel ativo "VT-4471" permanece com is_active verdadeiro

  Regra: Idempotência na reimportação de imóveis e fotos do Vitrine

    @upsert @idempotency
    Cenário: Reimportação do Vitrine atualiza dados de imóvel já existente in-place sem duplicar registro
      Dado que o caminho do feed JSON aponta para a fixture do Vitrine Imóveis
      E que o catálogo do Vitrine foi importado e o imóvel "VT-4471" teve o título alterado para "titulo antigo"
      Quando o VitrineImporter executa a importação do catálogo JSON
      Então o imóvel "VT-4471" recupera o título "Apartamento 3 quartos no Buritis" e preço "845000.00"
      E o total de imóveis do Vitrine permanece 3 com updated_count igual a 3

    @photos @ordering
    Cenário: Fotos do anúncio do Vitrine são gravadas respeitando a ordem exata publicada pelo portal
      Dado que o caminho do feed JSON aponta para a fixture do Vitrine Imóveis
      Quando o VitrineImporter executa a importação do catálogo JSON
      Então as URLs das fotos do imóvel "VT-4471" seguem a sequência publicada pelo Vitrine:
        | posicao | url                                                  |
        | 0       | https://fotos.vitrineimoveis.com.br/VT-4471/01.jpg   |
        | 1       | https://fotos.vitrineimoveis.com.br/VT-4471/02.jpg   |
        | 2       | https://fotos.vitrineimoveis.com.br/VT-4471/03.jpg   |

    @photos @idempotency
    Cenário: Reimportação do Vitrine substitui as fotos do imóvel sem acumular registros duplicados
      Dado que o caminho do feed JSON aponta para a fixture do Vitrine Imóveis
      E que o imóvel "VT-4471" do Vitrine já possui 3 fotos importadas
      Quando o VitrineImporter executa a importação do catálogo JSON
      Então a contagem de fotos do imóvel "VT-4471" continua sendo exatamente 3

  Regra: Resiliência operacional e normalização de campos do Vitrine

    @resilience @error_handling
    Cenário: Ausência do arquivo JSON registra ImportRun com status FAILED e mensagem de erro
      Dado que o caminho do feed aponta para um arquivo JSON inexistente
      Quando o VitrineImporter tenta executar a importação do arquivo JSON ausente
      Então o ImportRun do Vitrine termina com status "FAILED" e mensagem de erro preenchida

    @celery @task
    Cenário: Task Celery import_vitrine_properties aciona o importador e persiste o ImportRun
      Dado que o caminho do feed JSON aponta para a fixture do Vitrine Imóveis
      Quando a task Celery import_vitrine_properties é disparada
      Então um ImportRun da fonte VITRINE com status "SUCCESS" é registrado no banco

    @parser @price @pt_br
    Esquema do Cenário: Conversão de preço no formato do Vitrine retorna Decimal normalizado sem multiplicar por 100
      Quando VitrineImporter._parse_price recebe o texto "<raw>"
      Então o valor decimal retornado pelo VitrineImporter é "<expected>"

      Exemplos:
        | raw        | expected   |
        | 845000,00  | 845000.00  |
        | 2890,00    | 2890.00    |
        | 1180000,00 | 1180000.00 |

    @parser @address
    Cenário: Formatação de endereço do Vitrine concatena rua, número e complemento disponíveis
      Dado que a localização do Vitrine possui rua "Rua Fernandes Tourinho", número "88" e complemento vazio
      Quando VitrineImporter._build_address monta a linha de endereço
      Então o endereço formatado pelo VitrineImporter é "Rua Fernandes Tourinho, 88"
