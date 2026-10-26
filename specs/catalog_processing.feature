# language: pt
@bdd @celery @processing @nightly_job
Funcionalidade: Processamento Noturno do Catálogo
  Como um motor de enriquecimento do Portal de Imóveis
  Eu quero processar em lote todas as descrições dos anúncios importados durante a madrugada
  Para que o catálogo público exiba descrições padronizadas e enriquecidas

  Regra: Enriquecimento em lote de todos os anúncios cadastrados

    Cenário: Job noturno process_properties enriquece a descrição de todos os anúncios da base
      Dado que existem os seguintes imóveis cadastrando descrições para processamento noturno:
        | external_id | description            |
        | NX-1        | Apartamento na Savassi |
        | NX-2        | Casa no Sion           |
      Quando a task assíncrona process_properties é executada
      Então todas as descrições recebem o prefixo de processamento:
        | description                       |
        | Processed: Apartamento na Savassi |
        | Processed: Casa no Sion           |
      E o worker invoca a rotina de processamento 2 vezes
