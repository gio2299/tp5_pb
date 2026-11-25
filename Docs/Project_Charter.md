# Project Charter — EquidadeJá Brasil

**Projeto de Bloco:** Inteligência Artificial Aplicada
**Autora:** Giovanna Silva
**Etapa:** TP5 (versão final, com LLM e dashboard)
**Metodologia:** TDSP (Team Data Science Process)

---

## 1. Contexto e problema de negócio

A desigualdade de gênero no mercado de trabalho brasileiro é acompanhada por indicadores oficiais, relatórios de transparência salarial e por uma produção contínua de notícias e artigos. Esse volume é grande, vem de fontes diferentes e está em texto livre, o que dificulta a leitura sistemática por quem precisa tomar decisões com base nele.

**Problema de negócio:** como transformar rapidamente textos jornalísticos e institucionais sobre equidade de gênero no trabalho em informação resumida, classificada e comparável, apoiando decisões de ESG e de políticas de diversidade?

## 2. Objetivos

**Objetivo geral:** automatizar a sumarização de notícias sobre equidade de gênero no trabalho com um LLM, classificando cada uma por tema, ODS, relevância e sentimento, e apresentar o resultado em um dashboard interativo.

**Objetivos específicos:**
1. Coletar notícias por RSS e web scraping e organizá-las em um corpus junto com indicadores de gênero.
2. Gerar, com um LLM e engenharia de prompts, resumo, tema, ODS e relevância de cada notícia.
3. Combinar essa saída com o sentimento calculado por um modelo local (TP4).
4. Disponibilizar tudo em um dashboard com dados, gráficos e interação em tempo real com o modelo.
5. Avaliar a qualidade dos resumos comparando-os com os textos originais.

## 3. Escopo

**Dentro do escopo**
- 15 notícias do Google News (RSS), com texto completo extraído por Selenium.
- Indicadores de gênero e trabalho (3 indicadores, de 2015 a 2022).
- Resumo individual, tema, ODS, relevância e sentimento de cada notícia.
- Briefing executivo gerado a partir de todos os resumos.
- Resumo em tempo real de um texto colado pelo usuário.
- Escolha do TP5: **Opção 2, automação de sumarização de textos com LLMs.**

**Fora do escopo**
- Previsão de tendências.
- Relatórios de sustentabilidade em PDF.
- Qualquer decisão automática sem revisão humana. Os resultados são sugestões.

## 4. Stakeholders

| Stakeholder | Interesse |
|---|---|
| Analistas de ESG e de RH | Acompanhar a pauta sem ler todos os textos |
| Gestores de diversidade e inclusão | Usar o briefing para priorizar ações |
| Estudantes e pesquisadores | Explorar os dados e os resumos no painel |

## 5. Evolução do projeto

O projeto foi construído em etapas, e cada uma alimenta a seguinte:

| Etapa | Entrega |
|---|---|
| Dashboard | Aplicação Streamlit com múltiplas páginas: indicadores, notícias, nuvem de palavras, upload e download, API e sobre |
| API | API FastAPI para consulta e envio de dados (indicadores, notícias e estatísticas) |
| Web scraping | Coleta de manchetes por RSS (Beautiful Soup) e do texto completo das matérias por Selenium |
| Corpus | Preparação de um corpus em CSV para uso com LLMs, com notícias e indicadores transformados em frases |
| TP4 | Análise de sentimento com modelo de linguagem local (HuggingFace), integrada à API |
| **TP5** | **Sumarização com LLM, avaliação dos resumos e página "Resumos IA" no dashboard** |

## 6. Como os dados, a IA e a engenharia de prompts resolvem o problema

**Dados.** As manchetes vêm do feed RSS do Google News (requests e Beautiful Soup). O texto completo de cada matéria foi extraído com Selenium. Esses textos, junto com os indicadores de gênero transformados em frases, formam o corpus usado pelo LLM.

**Por que um LLM.** Notícias são texto livre. Em uma única chamada, o LLM resume o texto, extrai o tema, associa os ODS e estima a relevância, devolvendo tudo em JSON. Uma regra tradicional não faria isso.

**Combinação de modelos.**

| Tarefa | Modelo | Onde roda |
|---|---|---|
| Sentimento das manchetes | `lxyuan/distilbert-base-multilingual-cased-sentiments-student` | Local (HuggingFace), sem custo e sem internet |
| Resumo, tema, ODS, relevância e briefing | `openai/gpt-oss-20b` | API do Groq, plano gratuito |

Antes dessa escolha, duas opções não funcionaram: o Gemini (plano gratuito indisponível para o projeto, erro 403) e o `llama-3.3-70b-versatile` (erro 404, modelo não disponível na conta).

**Engenharia de prompt.** O prompt usa cinco técnicas:
1. **Papel (system prompt):** analista de políticas públicas e ESG, especialista em equidade de gênero no trabalho.
2. **Regras anti-alucinação:** usar somente o texto, escrever "não informado" quando faltar informação e nunca inventar números, nomes ou datas.
3. **Saída estruturada em JSON** com as chaves `resumo` (até 3 frases), `tema`, `ods` e `relevancia`.
4. **Few-shot:** um exemplo de saída dentro do prompt.
5. **Temperatura baixa:** 0,2 para o resumo e 0,3 para o briefing, para respostas mais estáveis.

**Reprodutibilidade e custo.** Os resumos são gerados em lote e gravados em `Data/LLM/resumos_llm.csv`. O dashboard lê esse arquivo, então somente o briefing e o resumo de um texto novo chamam a API em tempo real.

## 7. Alinhamento com os ODS e com o ESG

- **ODS 5 (Igualdade de gênero):** a solução acompanha a participação de mulheres na liderança e a igualdade de oportunidades.
- **ODS 8 (Trabalho decente e crescimento econômico):** a solução acompanha a igualdade de remuneração para trabalho de igual valor.
- **ESG:** o pilar Social (equidade e inclusão) e o pilar de Governança (transparência salarial, exigida pela Lei 14.611/2023) aparecem em quase todas as notícias analisadas.

## 8. Métricas de sucesso e resultados

| Métrica | Resultado |
|---|---|
| Resumos gerados sem erro técnico | 15 de 15 |
| Notícias com texto útil para resumir | 13 de 15 |
| Qualidade dos resumos (avaliação manual das 13 avaliáveis) | 9 corretos, 4 parciais, 0 errados (69% corretos) |
| Notícias associadas ao ODS 8 / ao ODS 5 | 13 de 15 / 11 de 15 |
| Tema mais frequente | Remuneração (igualdade, desigualdade ou disparidade salarial): 8 de 15 |
| Relevância atribuída pelo LLM | 13 alta, 1 média, 1 baixa |
| Sentimento das manchetes (modelo local) | 11 negativo, 4 positivo, 0 neutro; 5 com confiança abaixo de 0,50 |

**Método da avaliação.** Cada resumo foi comparado com o texto original e classificado como correto, parcial ou errado. Duas notícias ficaram fora da conta por não terem base para verificação (uma só com a manchete e outra cujo texto coletado era o menu do site). A avaliação preliminar foi feita com apoio do Claude, e a autora conferiu os resumos classificados como parciais contra os textos originais. O detalhe de cada nota está em `avaliacao_resumos.csv`.

**Erros encontrados nos resumos parciais:**
- Dado numérico mal interpretado: o texto dizia que a participação feminina subiu *para* 40,6%, e o resumo disse que *aumentou* 40,6%.
- Fato trocado: a diferença de participação aumentou na pandemia, e o resumo disse que estagnou.
- Causa simplificada: o custo de cuidados infantis foi apresentado como causa única, quando o texto fala em "alguns dos motivos".
- ODS 5 e 8 atribuídos a um texto que cita apenas a Agenda 2030 de forma geral.

## 9. Riscos e mitigação

| Risco | Como se manifestou | Mitigação |
|---|---|---|
| Alucinação ou interpretação errada | 4 de 13 resumos parciais | Prompt restritivo, temperatura baixa, revisão humana e resultados tratados como sugestões |
| Falha na coleta | Em uma notícia, o texto coletado era o menu do site, mas o campo `base_resumo` indicou "texto completo" | Registrar a limitação; no futuro, validar o conteúdo coletado e não só o tamanho |
| Truncamento de texto | Cada notícia é enviada ao LLM com no máximo 4.000 caracteres, e há textos de até cerca de 15 mil | Documentar a limitação; no futuro, resumir em partes |
| Sentimento mede o tom, não o impacto | Manchete com avanço para a equidade classificada como negativa, e o inverso | Mostrar a confiança e tratar como indicador auxiliar |
| Dependência de API externa | Troca de provedor e de modelo durante o desenvolvimento, e limites do plano gratuito | Resumos salvos em CSV, para o painel funcionar sem nova chamada |
| Privacidade e direitos autorais | Textos de notícias públicas são enviados a uma API externa | Uso acadêmico, apenas conteúdo jornalístico público, sem dados pessoais |
| Segurança da chave de API | Chave guardada no arquivo `.env` | `.env` fora do repositório (`.gitignore`) e `.env.example` sem a chave |

## 10. Ciclo de Ciência de Dados

O projeto cobre o ciclo completo:
1. **Coleta:** RSS e Selenium.
2. **Preparação:** corpus de notícias e indicadores em frases.
3. **Modelagem com IA:** sentimento local e sumarização com LLM.
4. **Avaliação:** conferência manual dos resumos contra os textos originais.
5. **Comunicação:** dashboard Streamlit com dados, gráficos e interação com o modelo.

## 11. Entregáveis

- Código: `resumidor.py`, `pages/8_Resumos_IA.py` e os demais arquivos do projeto.
- Dados: `Data/LLM/corpus_llm.csv` e `Data/LLM/resumos_llm.csv`.
- Avaliação: `avaliacao_resumos.csv`.
- Documentação: este Project Charter, o `Data_Summary_Report.md`, o `Apresentacao_Solucao_Final.md` (com os prints do dashboard em `Docs/img/`) e o `README.md`.

## 12. Uso de IA

- **Em tempo de execução:** modelo local de sentimento (HuggingFace) e modelo `openai/gpt-oss-20b` via API do Groq, para resumo, tema, ODS, relevância e briefing.
- **No desenvolvimento:** o Claude (Anthropic) foi usado como apoio ao código (`resumidor.py` e a página do dashboard), à depuração, à avaliação preliminar dos resumos e à redação desta documentação, com revisão da autora.
- Resultados de IA podem conter erros e viés. As informações dos resumos foram conferidas contra os textos originais, e os casos divergentes estão registrados na avaliação.
