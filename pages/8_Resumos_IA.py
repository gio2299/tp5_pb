import pandas as pd
import plotly.express as px
import streamlit as st

import resumidor

st.set_page_config(page_title="Resumos com IA", page_icon="🤖", layout="wide")
st.title("🤖 Resumos com IA")
st.caption("Coleta (RSS + Selenium) → corpus → sentimento (modelo local) → resumo (LLM) → insights")

if not resumidor.ARQ_RESUMOS.exists():
    st.warning("Ainda não há resumos. Rode `python resumidor.py` no terminal e recarregue a página.")
    st.stop()

df = pd.read_csv(resumidor.ARQ_RESUMOS).fillna("")
ok = df[df["erro"] == ""]

c1, c2, c3 = st.columns(3)
c1.metric("Notícias resumidas", len(ok))
c2.metric("Texto completo (critério automático)", int((ok["base_resumo"] == "texto completo").sum()))
c3.metric("Relevância alta", int((ok["relevancia"] == "alta").sum()))

tab1, tab2, tab3, tab4 = st.tabs(["Resumos", "Gráficos", "Briefing executivo", "Resumir novo texto"])

with tab1:
    filtro = st.multiselect("Relevância", ["alta", "média", "baixa"])
    d = ok[ok["relevancia"].isin(filtro)] if filtro else ok
    for _, r in d.iterrows():
        with st.expander(f"{r['titulo']}  ·  {r['fonte']}"):
            st.write(r["resumo"])
            st.caption(f"Tema: {r['tema']} | ODS: {r['ods'] or '-'} | Relevância: {r['relevancia']} | "
                       f"Sentimento (modelo local): {r['sentimento']} ({r['confianca_sentimento']}) | "
                       f"Base: {r['base_resumo']}")

with tab2:
    g1, g2 = st.columns(2)
    sent = ok["sentimento"].value_counts().reset_index()
    sent.columns = ["sentimento", "quantidade"]
    g1.plotly_chart(px.bar(sent, x="sentimento", y="quantidade", title="Sentimento das manchetes (modelo local)"),
                    use_container_width=True)
    temas = ok[ok["tema"] != ""]["tema"].str.lower().value_counts().head(10).reset_index()
    temas.columns = ["tema", "quantidade"]
    g2.plotly_chart(px.bar(temas, x="quantidade", y="tema", orientation="h", title="Temas mais frequentes (LLM)"),
                    use_container_width=True)
    ods = ok["ods"].astype(str).str.split(",").explode().str.strip()
    ods = ods[ods != ""].value_counts().reset_index()
    ods.columns = ["ODS", "quantidade"]
    if not ods.empty:
        ods = ods.sort_values("ODS", key=lambda c: c.astype(int))
        ods["ODS"] = "ODS " + ods["ODS"].astype(str)
        fig_ods = px.bar(ods, x="ODS", y="quantidade", title="ODS associados às notícias")
        fig_ods.update_xaxes(type="category")  # evita o eixo numérico (4, 5, 6...)
        st.plotly_chart(fig_ods, use_container_width=True)

with tab3:
    st.write("Gera um resumo único a partir de todos os resumos individuais.")
    if st.button("Gerar briefing"):
        with st.spinner("Consultando o LLM..."):
            try:
                st.session_state["briefing"] = resumidor.gerar_briefing(ok["resumo"].tolist())
            except Exception as e:
                st.error(f"Erro: {e}")
    if "briefing" in st.session_state:
        st.info(st.session_state["briefing"])

with tab4:
    titulo = st.text_input("Título")
    texto = st.text_area("Texto da notícia/relatório", height=200)
    if st.button("Resumir") and (titulo or texto):
        with st.spinner("Consultando o LLM..."):
            try:
                res = resumidor.resumir_noticia(titulo or texto[:80], texto)
                st.write(res["resumo"])
                st.caption(f"Tema: {res['tema']} | ODS: {res['ods']} | Relevância: {res['relevancia']}")
            except Exception as e:
                st.error(f"Erro: {e}")
