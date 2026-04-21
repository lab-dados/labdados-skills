# Changelog

Todas as mudanças notaveis deste marketplace serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/); versionamento
segue [Semantic Versioning](https://semver.org/).

## [1.1.0] — 2026-04-20

### Adicionado

- `raspe` — raspagem de dados de fontes oficiais brasileiras (Presidencia,
  Camara, Senado, CNJ, IPEA, CFM, ANS, ANVISA, SaudeLegis) e imprensa (Folha
  de Sao Paulo, New York Times) via biblioteca raspe. Scrapers HTTP para 8
  fontes e Playwright (com stealth para Cloudflare) para ANS/ANVISA/SaudeLegis.
  References detalhados por fonte + guia de setup de navegador.

## [1.0.0] — 2026-04-20

Primeira publicacao do marketplace `labdados-skills` com tres plugins:

- `juscraper` — raspagem de dados judiciais brasileiros (22 tribunais estaduais
  + Datajud + JusBR) via biblioteca juscraper.
- `dataframeit` — enriquecimento de DataFrames com LLMs (extracao estruturada
  via Pydantic, classificacao, busca web, multi-provedor).
- `openalex` — busca e download de literatura academica via OpenAlex (460M+
  obras): API para descoberta + CLI para downloads em massa.
