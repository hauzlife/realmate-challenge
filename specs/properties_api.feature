# language: pt
@bdd @api @rest
Funcionalidade: Listagem e Filtros de Busca do Catálogo (/api/properties/)
  Como um consumidor da API pública do Portal de Imóveis
  Eu quero listar imóveis ativos e filtrar por preço, quartos, cidade e tipo de transação
  Para que eu encontre apenas anúncios disponíveis que atendam aos critérios de busca

  Contexto:
    Dado que existe um imóvel ativo "NX-1" à venda em "Belo Horizonte" por "500000.00" com 2 quartos

  Regra: Visibilidade de anúncios na listagem pública

    @catalog
    Cenário: GET /api/properties/ retorna imóveis ativos paginados com rótulos legíveis
      Quando o cliente consulta GET "/api/properties/"
      Então a API responde HTTP 200 com count igual a 1
      E o primeiro item retornado possui external_id "NX-1", source "Nexo Portal" e transaction "Sale"

    @security @inactive
    Cenário: GET /api/properties/ omite imóveis marcados como inativos
      Dado que o imóvel "NX-1" foi desativado na base
      Quando o cliente consulta GET "/api/properties/"
      Então a API responde HTTP 200 com count igual a 0 e lista vazia

  Regra: Filtragem avançada do catálogo por parâmetros de consulta

    @filters @min_price
    Cenário: Filtro min_price exclui imóveis abaixo do valor mínimo solicitado
      Quando o cliente consulta GET "/api/properties/" com o filtro min_price "600000"
      Então a API responde HTTP 200 com count igual a 0 e lista vazia

    @filters @combined_filters
    Cenário: Filtros combinados refinam o catálogo por cidade, transação, preço máximo e quartos mínimos
      Dado que existe também um imóvel ativo "NX-2" para aluguel em "Sao Paulo" por "2500.00" com 1 quarto
      Quando o cliente aplica os filtros combinados na API:
        | parametro    | valor          |
        | city         | Belo Horizonte |
        | transaction  | SALE           |
        | max_price    | 550000         |
        | min_bedrooms | 2              |
      Então a API responde HTTP 200 com count igual a 1
      E apenas o imóvel "NX-1" é retornado na listagem

    @photos @n_plus_one
    Cenário: GET /api/properties/ inclui fotos ordenadas sem introduzir queries N+1 por imóvel
      Dado que o imóvel "NX-1" possui as fotos "https://fotos.vitrineimoveis.com.br/VT-1/01.jpg" e "https://fotos.vitrineimoveis.com.br/VT-1/02.jpg"
      E que existe também um imóvel ativo "NX-2" para aluguel em "Sao Paulo" por "2500.00" com 1 quarto
      Quando o cliente consulta GET "/api/properties/" monitorando o número de queries SQL
      Então a API devolve as URLs das fotos do imóvel "NX-1" na ordem cadastrada
      E a listagem executa no máximo 3 queries SQL sem N+1 em PropertyPhoto
