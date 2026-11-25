"""TP5 - Sumarização automática de notícias com LLM (Google Gemini).

Uso (gera Data/LLM/resumos_llm.csv):
    python resumidor.py

Requer GROQ_API_KEY (console.groq.com) OU GEMINI_API_KEY (aistudio.google.com) no .env.
"""
import json
import os
import time

import pandas as pd
from dotenv import load_dotenv

from dados import ROOT

load_dotenv()

USAR_GROQ = bool(os.getenv("GROQ_API_KEY"))
if USAR_GROQ:
    MODELO_LLM = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
else:
    MODELO_LLM = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
ARQ_CORPUS_LLM = ROOT / "Data" / "LLM" / "corpus_llm.csv"
ARQ_RESUMOS = ROOT / "Data" / "LLM" / "resumos_llm.csv"
MAX_CHARS = 4000        # limite de texto enviado por notícia
PAUSA_SEGUNDOS = 6      # evita estourar o limite por minuto do plano gratuito

# ---------------------- ENGENHARIA DE PROMPT ----------------------
# Técnicas: papel (system prompt), regras anti-alucinação, saída estruturada
# em JSON, few-shot (1 exemplo) e temperatura baixa.
SYSTEM = (
    "Você é um analista de políticas públicas e ESG, especialista em equidade "
    "de gênero no mercado de trabalho brasileiro. Resuma textos de forma "
    "objetiva, em português, usando SOMENTE informações presentes no texto. "
    "Se uma informação não estiver no texto, escreva 'não informado'. "
    "Nunca invente números, nomes ou datas."
)

EXEMPLO = {
    "resumo": "Empresas brasileiras ampliam a presença de mulheres em cargos de "
              "liderança, mas a diferença salarial segue relevante.",
    "tema": "liderança feminina",
    "ods": [5, 8],
    "relevancia": "alta",
}


def montar_prompt(titulo: str, texto: str) -> str:
    return f"""Resuma a notícia abaixo e responda APENAS com um JSON válido, com as chaves:
- "resumo": no máximo 3 frases;
- "tema": 2 a 4 palavras (ex.: "igualdade salarial", "liderança feminina");
- "ods": lista de números de ODS relacionados (use 5 e 8 quando fizer sentido; outros só se claramente citados);
- "relevancia": "alta", "média" ou "baixa" para a pauta de equidade de gênero no trabalho.

Exemplo de saída:
{json.dumps(EXEMPLO, ensure_ascii=False)}

Título: {titulo}
Texto: {texto[:MAX_CHARS]}"""


def _gerar(prompt: str, temperatura: float, json_mode: bool, tentativas: int = 3) -> str:
    """Chama o LLM (Groq ou Gemini), com nova tentativa em caso de limite/erro."""
    for t in range(1, tentativas + 1):
        try:
            if USAR_GROQ:
                import requests  # chamada direta à API do Groq (compatível com a da OpenAI)
                corpo = {
                    "model": MODELO_LLM,
                    "temperature": temperatura,
                    "messages": [{"role": "system", "content": SYSTEM},
                                 {"role": "user", "content": prompt}],
                }
                if json_mode:
                    corpo["response_format"] = {"type": "json_object"}
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
                    json=corpo, timeout=60)
                if resp.status_code != 200:
                    raise RuntimeError(f"Groq {resp.status_code}: {resp.text[:300]}")
                return resp.json()["choices"][0]["message"]["content"]
            chave = os.getenv("GEMINI_API_KEY")
            if not chave:
                raise RuntimeError("Defina GROQ_API_KEY ou GEMINI_API_KEY no .env.")
            from google import genai
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM, temperature=temperatura,
                response_mime_type="application/json" if json_mode else "text/plain")
            cliente = genai.Client(api_key=chave)
            r = cliente.models.generate_content(
                model=MODELO_LLM, contents=prompt, config=config)
            return r.text
        except Exception:
            if t == tentativas:
                raise
            time.sleep(20)


def resumir_noticia(titulo: str, texto: str = "") -> dict:
    """Resume uma notícia e devolve dict com resumo, tema, ods, relevancia."""
    bruto = _gerar(montar_prompt(titulo, texto), temperatura=0.2, json_mode=True)
    dados = json.loads(bruto)
    dados["ods"] = [int(x) for x in dados.get("ods", []) if str(x).isdigit()]
    return dados


def gerar_briefing(resumos: list[str]) -> str:
    """Sumariza todos os resumos em um briefing executivo único."""
    lista = "\n".join(f"- {r}" for r in resumos)
    prompt = ("Com base APENAS nos resumos abaixo, escreva um briefing executivo "
              "(máx. 6 linhas) com: principais tendências, riscos e 2 recomendações "
              "práticas para empresas, ligando ao ODS 5 e ao ODS 8.\n\n" + lista)
    return _gerar(prompt, temperatura=0.3, json_mode=False).strip()


def _sentimento_local(titulo: str) -> tuple[str, float]:
    """Reaproveita o modelo local do TP4 (HuggingFace)."""
    try:
        import llm
        if not llm.modelo_carregado():
            llm.carregar_modelo()
        s = llm.classificar(titulo)
        return s["label"].lower(), round(float(s["score"]), 4)
    except Exception:
        return "indisponível", 0.0


def main():
    if not (USAR_GROQ or os.getenv("GEMINI_API_KEY")):
        raise SystemExit("Nenhuma chave encontrada. Coloque GROQ_API_KEY no arquivo .env.")
    print(f"Provedor: {'Groq' if USAR_GROQ else 'Gemini'} | Modelo: {MODELO_LLM}")
    corpus = pd.read_csv(ARQ_CORPUS_LLM)
    noticias = corpus[corpus["tipo"] == "noticia"].reset_index(drop=True)
    linhas = []
    for i, row in noticias.iterrows():
        titulo = str(row["titulo"])
        conteudo = str(row["conteudo"])
        base = "texto completo" if len(conteudo) > len(titulo) + 300 else "apenas manchete"
        print(f"[{i + 1}/{len(noticias)}] {titulo[:70]}...")
        rotulo, conf = _sentimento_local(titulo)
        try:
            res = resumir_noticia(titulo, conteudo)
            erro = ""
        except Exception as e:
            res = {"resumo": "", "tema": "", "ods": [], "relevancia": ""}
            erro = str(e)[:200]
            print("  erro:", erro)
        linhas.append({
            "titulo": titulo, "fonte": row["fonte"], "data": row["data"],
            "base_resumo": base,
            "resumo": res.get("resumo", ""), "tema": res.get("tema", ""),
            "ods": ",".join(str(x) for x in res.get("ods", [])),
            "relevancia": res.get("relevancia", ""),
            "sentimento": rotulo, "confianca_sentimento": conf, "erro": erro,
        })
        time.sleep(PAUSA_SEGUNDOS)
    df = pd.DataFrame(linhas)
    ARQ_RESUMOS.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ARQ_RESUMOS, index=False)
    print(f"Salvo em {ARQ_RESUMOS} ({(df['erro'] == '').sum()}/{len(df)} sem erro)")


if __name__ == "__main__":
    main()
