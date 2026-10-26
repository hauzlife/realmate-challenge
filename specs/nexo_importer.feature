# language: pt
@bdd @importer @nexo
Funcionalidade: Importador Portal Nexo
  Como um agregador de anúncios do Portal de Imóveis
  Eu quero importar e sincronizar o catálogo XML publicado pelo Portal Nexo
  Para que os imóveis disponíveis fiquem atualizados, validados e com fotos ordenadas na base

  Regra: Importação e validação do catálogo XML

    @xml
    Cenário: Importação inicial cria imóveis válidos a partir do catálogo XML do Portal Nexo
      Dado que o caminho do feed XML aponta para a fixture do Portal Nexo
      Quando o NexoImporter executa a importação do catálogo XML
      Então a execução fecha com status "SUCCESS" e 3 imóveis criados
      E a base de dados persiste exatamente 3 anúncios válidos

    @validation @price
    Cenário: Importador ignora anúncio com preço inválido sem abortar o lote
      Dado que o caminho do feed XML aponta para a fixture do Portal Nexo
      Quando o NexoImporter processa o feed contendo item sem preço numérico
      Então o contador skipped_count registra 1 anúncio descartado
      E o anúncio inválido "NX-11288" não é gravado na tabela Property

    @availability @inactive
    Cenário: Anúncio marcado como vendido no XML é salvo como inativo
      Dado que o caminho do feed XML aponta para a fixture do Portal Nexo
      Quando o NexoImporter importa o feed com o imóvel "NX-10488" vendido
      Então o imóvel "NX-10488" fica persistido com is_active falso
      E o imóvel disponível "NX-10233" permanece com is_active verdadeiro

  Regra: Idempotência na reimportação de imóveis e fotos

    @upsert @idempotency
    Cenário: Reimportação atualiza dados de imóvel já existente in-place sem duplicar registro
      Dado que o caminho do feed XML aponta para a fixture do Portal Nexo
      E que o catálogo foi importado e o imóvel "NX-10233" teve o preço alterado para "1.00"
      Quando o NexoImporter roda novamente sobre o catálogo atualizado
      Então o preço do imóvel "NX-10233" volta para "1250000.00"
      E o total de imóveis permanece 3 com updated_count igual a 3

    @photos @ordering
    Cenário: Fotos do anúncio são gravadas respeitando a ordem exata publicada pelo portal
      Dado que o caminho do feed XML aponta para a fixture do Portal Nexo
      Quando o NexoImporter importa o catálogo com as fotos do imóvel "NX-10233"
      Então as URLs das fotos do imóvel "NX-10233" seguem a sequência publicada pelo portal:
        | posicao | url                                             |
        | 0       | https://fotos.portalnexo.com.br/NX-10233/01.jpg |
        | 1       | https://fotos.portalnexo.com.br/NX-10233/02.jpg |
        | 2       | https://fotos.portalnexo.com.br/NX-10233/03.jpg |

    @photos @idempotency
    Cenário: Reimportação substitui as fotos do imóvel sem acumular registros duplicados
      Dado que o caminho do feed XML aponta para a fixture do Portal Nexo
      E que o imóvel "NX-10233" já possui 3 fotos importadas
      Quando o NexoImporter executa uma segunda carga do mesmo feed
      Então a contagem de fotos do imóvel "NX-10233" continua sendo exatamente 3

  Regra: Resiliência operacional e execução via fila assíncrona

    @resilience @error_handling
    Cenário: Ausência do arquivo XML registra ImportRun com status FAILED e mensagem de erro
      Dado que o caminho do feed aponta para um arquivo XML inexistente
      Quando o NexoImporter tenta executar a importação do arquivo ausente
      Então o ImportRun termina com status "FAILED" sem lançar exceção não tratada
      E a mensagem do erro e o timestamp finished_at ficam preenchidos

    @celery @task
    Cenário: Task Celery import_nexo_properties aciona o importador e persiste o ImportRun
      Dado que o caminho do feed XML aponta para a fixture do Portal Nexo
      Quando a task Celery import_nexo_properties é disparada
      Então um ImportRun com status "SUCCESS" é registrado no banco
      E os 3 imóveis do catálogo ficam disponíveis na base

  Regra: Normalização de preços e endereços do portal

    @parser @price @pt_br
    Esquema do Cenário: Conversão de preço em formato pt-BR retorna Decimal normalizado
      Quando _parse_price recebe o texto "<raw>"
      Então o valor decimal retornado é "<expected>"

      Exemplos:
        | raw          | expected   |
        | 1.250.000,00 | 1250000.00 |
        | 3.400,00     | 3400.00    |
        | 890,50       | 890.50     |
        | 450000       | 450000     |

    @parser @price @negative_test
    Cenário: Conversão de preço não numérico retorna None com segurança
      Quando _parse_price recebe o texto "sob consulta"
      Então o retorno de _parse_price é None sem lançar InvalidOperation

    @parser @address
    Cenário: Formatação de endereço concatena logradouro, número e complemento não vazios
      Dado que o endereço bruto possui logradouro "Rua Pernambuco", número "1255" e complemento vazio
      Quando _build_address monta a linha de endereço
      Então o endereço formatado final é "Rua Pernambuco, 1255"

    @validation @negative_test
    Cenário: Importador descarta anúncios incompletos ou com tipo de negócio desconhecido
      Dado que existe um ImportRun em andamento e dois payloads inválidos
      Quando _import_listing processa ambos os anúncios inválidos e _parse_int recebe texto inválido
      Então skipped_count contabiliza 2 descartes e _parse_int inválido retorna None

    @models
    Cenário: Representação textual de Property, PropertyPhoto e ImportRun reflete identificadores de domínio
      Dado que o caminho do feed XML aponta para a fixture do Portal Nexo
      Quando o NexoImporter executa a importação do catálogo XML
      Então as representações textuais de Property, PropertyPhoto e ImportRun exibem fonte, código e posição
