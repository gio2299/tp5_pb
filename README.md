# EquidadeJá Brasil

Painel de equidade de gênero no mercado de trabalho brasileiro.
Projeto de Bloco: Inteligência Artificial Aplicada — Giovanna Silva.

## O que o projeto tem
- Aplicação Streamlit com múltiplas páginas (indicadores, notícias, nuvem de palavras, upload/download, API, sobre e **Resumos IA**)
- API com FastAPI (consulta e envio de dados)
- Web scraping dinâmico com Selenium (texto completo das notícias)
- Corpus de dados preparado para uso com LLMs
- **(TP4)** Análise de sentimento com um modelo de linguagem da HuggingFace executado localmente e integrado à API
- **(TP5)** Sumarização automática das notícias com um LLM via API, avaliação dos resumos e página "Resumos IA" no dashboard

## Como instalar
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1    # Windows PowerShell | Mac/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```
O `requirements.txt` inclui `torch` e `transformers`. Na primeira execução da API, o modelo é baixado automaticamente (cerca de 541 MB); depois disso funciona offline, pelo cache local.

## Como rodar
**Aplicação (Streamlit):**
```bash
streamlit run app.py
```

**API (FastAPI)**, em outro terminal:
```bash
python -m uvicorn api:app --reload --port 8000
```
Documentação interativa: http://localhost:8000/docs
(ao iniciar, a API carrega o modelo de linguagem; aguarde `Application startup complete`)

**Scraping com Selenium** (requer Google Chrome instalado):
```bash
python scraping_selenium.py
```

**Preparar o corpus para LLM:**
```bash
python preparar_corpus.py
```

**Gerar os resumos com LLM (TP5):** veja a seção TP5 abaixo.

## Rotas da API
| Método | Rota | Função |
|---|---|---|
| GET | `/` | Verifica se a API está no ar |
| GET | `/indicadores` | Lista indicadores (filtros `ano_inicio`, `ano_fim`) |
| GET | `/noticias` | Lista notícias (filtros `fonte`, `limite`) |
| POST | `/noticias` | Cadastra uma notícia |
| GET | `/estatisticas` | Resumo dos dados |
| GET | `/status_modelo` | **(TP4)** Informa se o modelo local está carregado |
| POST | `/processar_texto` | **(TP4)** Analisa o sentimento de um texto com o modelo local |

---

## TP4: Integração com LLM local (HuggingFace + FastAPI)

A API analisa o sentimento de textos (por exemplo, manchetes sobre equidade de gênero) com um modelo de linguagem que roda **localmente**, sem nuvem e sem chave de API.

### Modelo escolhido
`lxyuan/distilbert-base-multilingual-cased-sentiments-student` (HuggingFace Hub)
- Tarefa: classificação de sentimento (positivo, neutro, negativo), com suporte a português (12 idiomas)
- Origem: modelo destilado (professor: `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`; aluno: `distilbert-base-multilingual-cased`), treinado com o dataset `tyqiangz/multilingual-sentiments`
- Tamanho: cerca de 0,1 bilhão de parâmetros; arquivo de pesos (`model.safetensors`) de 541 MB
- Licença: Apache 2.0
- Execução em CPU, tempo medido de 20 a 35 ms por texto

### Ambiente de teste
- Windows 10 Home Single Language, versão 22H2 (build 19045.6466), 64 bits, Python 3.14.7
- Intel Core i7-9750H 2.60 GHz, 16 GB de RAM (GPU NVIDIA RTX 2060 presente, mas não utilizada)
- torch 2.15.0+cpu, transformers 5.23.0

### Como a integração foi feita
1. `llm.py` carrega o modelo com `pipeline("text-classification")` da biblioteca Transformers e expõe a função `classificar`.
2. `schemas.py` define os Response Models (Pydantic).
3. `api.py` carrega o modelo uma única vez no `lifespan` do FastAPI e expõe as rotas `/status_modelo` e `/processar_texto`.
4. Ajustes: `truncation=True` e `max_length=512` (textos longos), `asyncio.to_thread` e `asyncio.wait_for` (a inferência não trava a API e tem limite de 15 s) e PyTorch versão CPU (dispensa GPU).

### Exemplo de uso
Requisição `POST /processar_texto`:
```json
{"texto": "Brasil avança na igualdade salarial e mais mulheres chegam à liderança"}
```
Resposta (200):
```json
{
  "texto_original": "Brasil avança na igualdade salarial e mais mulheres chegam à liderança",
  "tipo_analise": "analise_de_sentimento",
  "modelo": "lxyuan/distilbert-base-multilingual-cased-sentiments-student",
  "resultado": {"rotulo": "positive", "rotulo_pt": "positivo", "confianca": 0.7829},
  "tempo_processamento_ms": 21.34
}
```

### Tratamento de erros
| Código | Cenário | Origem |
|---|---|---|
| 400 | Texto contém apenas espaços | HTTPException na rota |
| 409 | Notícia já cadastrada (`POST /noticias`) | HTTPException na rota |
| 422 | Texto vazio, curto (< 3) ou longo (> 5000 caracteres) | Validação Pydantic |
| 500 | Erro inesperado durante a inferência | HTTPException na rota |
| 503 | Modelo não carregado | HTTPException na rota |
| 504 | Processamento excedeu 15 s | HTTPException na rota |

### Arquivos novos do TP4
- `llm.py`: carrega o modelo e classifica textos
- `schemas.py`: Response Models
- `api.py`: rotas atualizadas, com `lifespan`

### Problemas encontrados na instalação
- O índice do PyTorch CPU (`--index-url`) não contém o `transformers`; os pacotes foram instalados em comandos separados.
- A pasta `.venv` copiada do TP3 apontava para o caminho antigo; foi recriada e passou-se a usar `python -m pip`.
- O aviso do `huggingface_hub` sobre *symlinks* no Windows não afeta o funcionamento (apenas usa mais disco no cache).

### Limitações
- O modelo erra mais em frases mistas (ex.: "presença feminina cresce, mas desigualdades persistem" saiu como negativo com 50,8% de confiança). Confiança baixa indica incerteza.
- Os resultados são sugestões e devem ser revisados.

---

## TP5: Sumarização com LLM e dashboard

Nesta etapa o projeto ganhou uma camada de **sumarização automática** das notícias com um LLM (Opção 2 do TP5), integrada a uma nova página do dashboard Streamlit. O ciclo completo fica assim:

```
Google News (RSS) → Selenium (texto completo) → preparar_corpus.py → corpus_llm.csv
→ sentimento (modelo local, TP4) + resumo/tema/ODS/relevância (LLM via API)
→ resumos_llm.csv → dashboard (página "Resumos IA")
```

### O que a página "Resumos IA" faz
- **Resumos:** lista os resumos das notícias, com filtro por relevância e detalhes de tema, ODS e sentimento.
- **Gráficos:** sentimento das manchetes, temas mais frequentes e ODS associados.
- **Briefing executivo:** o LLM resume todos os resumos em um texto único, com tendências, riscos e recomendações.
- **Resumir novo texto:** o usuário cola um texto e recebe resumo, tema, ODS e relevância em tempo real.

### Como configurar e rodar
```bash
# 1. Ambiente (Windows PowerShell; Mac/Linux: source .venv/bin/activate)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 2. Chave de API: copie .env.example para .env e preencha a chave
#    (o arquivo .env NÃO vai para o GitHub)

# 3. Coletar e preparar os dados (se ainda não existirem)
python coletor_noticias.py
python scraping_selenium.py
python preparar_corpus.py

# 4. Gerar os resumos (cria Data/LLM/resumos_llm.csv)
python resumidor.py

# 5. Abrir o dashboard
streamlit run app.py
```

Conteúdo do `.env.example` (copie para `.env` e preencha a chave):
```
GROQ_API_KEY=cole-sua-chave-aqui
GROQ_MODEL=openai/gpt-oss-20b
```
A chave gratuita do Groq é criada em console.groq.com. O `resumidor.py` também aceita `GEMINI_API_KEY` (aistudio.google.com) como alternativa, mas ela só é usada se não houver `GROQ_API_KEY`.

### Arquivos novos do TP5
- `resumidor.py`: gera os resumos e o briefing com o LLM e junta o sentimento do modelo local
- `pages/8_Resumos_IA.py`: página do dashboard
- `Data/LLM/resumos_llm.csv`: saída do LLM (15 notícias)
- `avaliacao_resumos.csv`: avaliação manual dos resumos
- `.env.example`: modelo de configuração, sem chave

### Modelos usados
| Tarefa | Modelo | Onde roda |
|---|---|---|
| Sentimento das manchetes | `lxyuan/distilbert-base-multilingual-cased-sentiments-student` | Local (HuggingFace) |
| Resumo, tema, ODS, relevância e briefing | `openai/gpt-oss-20b` | API do Groq (plano gratuito) |

### Engenharia de prompt
- **Papel:** analista de políticas públicas e ESG, especialista em equidade de gênero no trabalho.
- **Regras anti-alucinação:** usar somente o texto, escrever "não informado" quando faltar informação e nunca inventar números, nomes ou datas.
- **Saída estruturada:** JSON com `resumo` (até 3 frases), `tema`, `ods` e `relevancia`.
- **Few-shot:** um exemplo de saída no prompt.
- **Temperatura baixa:** 0,2 para o resumo e 0,3 para o briefing.
- **Limite de entrada:** no máximo 4.000 caracteres de cada notícia são enviados ao modelo.

### Colunas de `resumos_llm.csv`
`titulo`, `fonte`, `data`, `base_resumo`, `resumo`, `tema`, `ods`, `relevancia`, `sentimento`, `confianca_sentimento`, `erro`.

### Resultados e avaliação
Cada resumo foi comparado com o texto original. A avaliação preliminar foi feita com apoio do Claude, e a autora conferiu os resumos classificados como parciais. Detalhes em `avaliacao_resumos.csv`.

| Avaliação | Quantidade |
|---|---|
| Correto | 9 |
| Parcial | 4 |
| Errado | 0 |
| Sem base para verificar | 2 |

- Resumos gerados sem erro técnico: 15 de 15.
- Notícias com texto útil: 13 de 15.
- Mais citados: ODS 8 em 13 de 15 notícias e ODS 5 em 11 de 15.
- Tema mais frequente: remuneração (igualdade, desigualdade ou disparidade salarial), em 8 de 15.
- Sentimento das manchetes: 11 negativo, 4 positivo e nenhum neutro; 5 com confiança abaixo de 0,50.

### Problemas encontrados
- **Gemini:** a chave gerou erro 403 (plano gratuito indisponível para o projeto), então a solução passou para o Groq.
- **Groq:** o modelo `llama-3.3-70b-versatile` retornou erro 404 (não disponível na conta) e foi trocado por `openai/gpt-oss-20b`.
- **Biblioteca `openai`:** causou o erro "client has been closed" neste ambiente; a chamada ao Groq passou a usar `requests` diretamente.
- **PowerShell:** foi preciso ativar o ambiente virtual com `.\.venv\Scripts\Activate.ps1` a partir da pasta do projeto.

### Limitações
- Amostra pequena (15 notícias): os números não devem ser generalizados.
- **Resumos parciais (4 de 13):** dado numérico mal interpretado (40,6%), fato trocado (a diferença de participação aumentou na pandemia, e o resumo disse que estagnou), causa simplificada e ODS atribuídos a um texto que não os cita.
- **Falha de coleta:** em uma notícia, o texto coletado era o menu do site e não o artigo, e o campo `base_resumo` marcou "texto completo" por engano, pois só considera o tamanho do conteúdo.
- **Truncamento:** textos maiores que 4.000 caracteres são resumidos só a partir do começo.
- **Sentimento:** o modelo mede o tom das palavras da manchete, não o impacto para a equidade (por exemplo, uma notícia com avanço saiu como negativa).
- Os resultados são sugestões e devem ser revisados por uma pessoa.

---

## Documentação
Veja a pasta `Docs/`:
- `Project_Charter.md`: problema, escopo, uso de dados, IA e prompts, ODS, métricas e riscos
- `Data_Summary_Report.md`: fontes, fluxo, volume, dicionário de dados e qualidade
- `Apresentacao_Solucao_Final.md`: apresentação e argumentação da solução final, com os prints do dashboard

## Uso de IA
- **Em tempo de execução:** a aplicação usa um modelo de linguagem local da HuggingFace para o sentimento e o modelo `openai/gpt-oss-20b`, via API do Groq, para resumo, tema, ODS, relevância e briefing. Portanto, **gerar resumos novos depende de uma API de IA em nuvem**; o dashboard consegue exibir o `resumos_llm.csv` já gerado sem chamar a API.
- **No desenvolvimento:** o Claude (Anthropic) foi usado como apoio ao código, à depuração, à avaliação preliminar dos resumos e à redação da documentação, com revisão da autora.
- Resultados de IA podem conter erros e viés; as informações dos resumos foram conferidas contra os textos originais.
