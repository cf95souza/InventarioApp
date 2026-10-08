import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from sqlalchemy import text
from inventario_ops import (
    get_engine_sqlserver,
    ler_material_estoque,
    ler_lista_contagem,
    ler_material_rescaldo,
    ler_lista_rescaldo,
    inserir_dados_sqlserver,
    carga_incremental_familia
)
from load_familia_produto_incremental import carga_incremental

st.set_page_config(
    page_title="Inventário - Acotubo",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --corp-primary: #1e3a5f;
        --corp-secondary: #2c5282;
        --corp-accent: #3182ce;
        --corp-bg: #f7f8fc;
        --corp-surface: #ffffff;
        --corp-text: #1a202c;
        --corp-muted: #718096;
        --corp-border: #e2e8f0;
        --corp-success: #38a169;
        --corp-danger: #e53e3e;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 1400px !important;
    }

    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown li,
    div[data-testid="stSidebar"] caption,
    div[data-testid="stSidebar"] label {
        color: #2d3748 !important;
    }

    div[data-testid="stSidebar"] [data-testid="stExpander"] summary {
        color: #1e3a5f !important;
    }

    div[data-testid="stSidebar"] hr {
        border-color: #e2e8f0 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px !important;
        background: #edf2f7 !important;
        border-radius: 10px !important;
        padding: 4px !important;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: #4a5568 !important;
        border: none !important;
        background: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #1e3a5f !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    h1 {
        color: #1e3a5f !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }

    h2, h3 {
        color: #2d3748 !important;
        font-weight: 600 !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2c5282, #3182ce) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 2px 8px rgba(49, 130, 206, 0.3) !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 14px rgba(49, 130, 206, 0.45) !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button:not([kind="primary"]) {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background: #ffffff !important;
        color: #4a5568 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        border-color: #3182ce !important;
        color: #3182ce !important;
        background: #ebf8ff !important;
    }

    .stDownloadButton > button {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background: #ffffff !important;
        color: #4a5568 !important;
        font-weight: 500 !important;
    }

    .stDownloadButton > button:hover {
        border-color: #38a169 !important;
        color: #38a169 !important;
        background: #f0fff4 !important;
    }

    [data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }

    [data-testid="stExpander"] summary {
        font-weight: 600 !important;
        color: #2d3748 !important;
        padding: 12px 16px !important;
    }

    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 0 16px 16px !important;
    }

    .stDataFrame {
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }

    [data-testid="stForm"] {
        background: #f7fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 16px !important;
    }

    .stRadio > div {
        gap: 8px !important;
    }

    .stRadio > div > label {
        padding: 6px 14px !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        transition: all 0.2s !important;
    }

    .stRadio > div > label:hover {
        border-color: #3182ce !important;
        background: #ebf8ff !important;
    }

    .stInfo {
        background: #ebf8ff !important;
        border: 1px solid #bee3f8 !important;
        border-radius: 8px !important;
    }

    .stSuccess {
        background: #f0fff4 !important;
        border: 1px solid #c6f6d5 !important;
        border-radius: 8px !important;
    }

    .stError {
        background: #fff5f5 !important;
        border: 1px solid #fed7d7 !important;
        border-radius: 8px !important;
    }

    .stMetric {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }

    .stSpinner > div {
        border-color: #3182ce transparent transparent transparent !important;
    }
</style>
""", unsafe_allow_html=True)

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="dados")
    return output.getvalue()

def mostrar_df(df: pd.DataFrame, title: str = "Resultado"):
    if df is None or df.empty:
        st.info("Nenhum registro retornado.")
    else:
        st.write(f"**{title}** — {len(df)} registros")
        st.dataframe(df, width='stretch', height=400)
        excel_bytes = to_excel_bytes(df)
        st.download_button(
            label="📥 Baixar Excel",
            data=excel_bytes,
            file_name=f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch'
        )

def solicitar_motivo_ui(suffix: str = ""):
    return int(
        st.radio(
            "Motivo da carga",
            options=[0, 1],
            format_func=lambda x: "🟢 Inicial" if x == 0 else "🔴 Final",
            key=f"motivo_{suffix}",
            horizontal=True
        )
    )

def tab_site_nave_ou_lista(key_prefix, ler_fn, tabela_destino, titulo_tab, inv_id, motivo):
    modo = st.radio("Buscar por", options=["Site/Nave", "Lista de Materiais"], key=f"modo_{key_prefix}", horizontal=True)

    if modo == "Site/Nave":
        col_site, col_nave = st.columns(2)
        with col_site:
            site = st.text_input("SITE", key=f"s_{key_prefix}", placeholder="Ex: RMZ")
        with col_nave:
            nave = st.text_input("NAVE", key=f"n_{key_prefix}", placeholder="Ex: MP-NV01")
        materiais = None
    else:
        materiais_text = st.text_area("Códigos separados por vírgula", placeholder="A0001234,A0005678", key=f"m_{key_prefix}")
        materiais = [m.strip() for m in materiais_text.split(",") if m.strip()] if materiais_text else None
        site, nave = None, None

    col_preview, col_load = st.columns(2)
    with col_preview:
        if st.button("🔍 Consultar", key=f"preview_{key_prefix}", width='stretch'):
            with st.spinner("Consultando Oracle..."):
                try:
                    df_preview = ler_fn(int(inv_id), site=site, nave=nave, materiais=materiais, motivo=motivo)
                    mostrar_df(df_preview, f"Preview {titulo_tab}")
                except Exception as e:
                    st.error(f"❌ Consulta: {e}")

    with col_load:
        if st.button("▶️ Inserir no Banco", key=f"load_{key_prefix}", width='stretch', type="primary"):
            with st.spinner("Inserindo dados..."):
                try:
                    df_load = ler_fn(int(inv_id), site=site, nave=nave, materiais=materiais, motivo=motivo)
                    result = inserir_dados_sqlserver(df_load, tabela_destino)
                    if result["sucesso"]:
                        st.success(f"✅ {result['mensagem']}")
                    else:
                        st.error(f"❌ {result['mensagem']}")
                except Exception as e:
                    st.error(f"❌ Inserção: {e}")

def tab_lista(key_prefix, ler_fn, tabela_destino, titulo_tab, inv_id, motivo):
    numero_lista = st.text_input("Número da lista", key=f"lista_{key_prefix}", placeholder="Ex: 482")

    col_preview, col_load = st.columns(2)
    with col_preview:
        if st.button("🔍 Consultar", key=f"preview_{key_prefix}", width='stretch'):
            with st.spinner("Consultando Oracle..."):
                try:
                    df_preview = ler_fn(numero_lista, int(inv_id), motivo=motivo)
                    mostrar_df(df_preview, f"Preview {titulo_tab}")
                except Exception as e:
                    st.error(f"❌ Consulta: {e}")

    with col_load:
        if st.button("▶️ Inserir no Banco", key=f"load_{key_prefix}", width='stretch', type="primary"):
            with st.spinner("Inserindo dados..."):
                try:
                    df_load = ler_fn(numero_lista, int(inv_id), motivo=motivo)
                    result = inserir_dados_sqlserver(df_load, tabela_destino)
                    if result["sucesso"]:
                        st.success(f"✅ {result['mensagem']}")
                    else:
                        st.error(f"❌ {result['mensagem']}")
                except Exception as e:
                    st.error(f"❌ Inserção: {e}")

st.markdown(
    '<div style="padding: 0 0 8px 0;">'
    '<h1 style="margin:0; font-size:1.8rem; color:#1e3a5f; letter-spacing:-0.5px;">Sistema de Inventário</h1>'
    '<p style="margin:0; color:#718096; font-size:0.95rem;">Acotubo — Controle de Estoques e Contagens</p>'
    '</div>',
    unsafe_allow_html=True
)

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding: 16px 0 20px 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 16px;">'
        '<div style="width:52px; height:52px; background:linear-gradient(135deg,#2c5282,#3182ce); border-radius:12px; display:inline-flex; align-items:center; justify-content:center; font-size:24px; margin-bottom:10px; box-shadow:0 4px 12px rgba(49,130,206,0.3);">📦</div>'
        '<div style="font-size:17px; font-weight:700; color:#1e3a5f;">AuditoriaApp</div>'
        '<div style="font-size:11px; color:#718096; margin-top:2px; font-weight:400;">Gestão de Inventário</div>'
        '</div>',
        unsafe_allow_html=True
    )

    with st.expander("📋 Inventários", expanded=True):
        if st.button("🔄 Atualizar lista", width='stretch'):
            st.rerun()
        try:
            engine = get_engine_sqlserver()
            df_inv = pd.read_sql(
                "SELECT ID_INVENTARIO, SITE, NAVE, RESPONSAVEL, ATIVO, DATACADASTRO FROM Inventario ORDER BY ID_INVENTARIO DESC",
                engine,
            )
            if not df_inv.empty:
                itens_por_pagina = 3
                total_paginas = (len(df_inv) - 1) // itens_por_pagina + 1

                if "page_inv" not in st.session_state:
                    st.session_state.page_inv = 1

                pagina_atual = st.session_state.page_inv
                inicio = (pagina_atual - 1) * itens_por_pagina
                fim = inicio + itens_por_pagina
                df_pagina = df_inv.iloc[inicio:fim]

                for _, row in df_pagina.iterrows():
                    col_id, col_site, col_nave, col_btn = st.columns([1, 1.2, 1.5, 0.8])
                    with col_id:
                        st.caption("ID")
                        st.markdown(f"**{row['ID_INVENTARIO']}**")
                    with col_site:
                        st.caption("SITE")
                        st.markdown(f"{row['SITE']}")
                    with col_nave:
                        st.caption("NAVE")
                        st.markdown(f"{row['NAVE']}")
                    with col_btn:
                        st.caption("&nbsp;")
                        if st.button("✏️", key=f"edit_{row['ID_INVENTARIO']}"):
                            st.session_state[f"editando_{row['ID_INVENTARIO']}"] = True
                    st.markdown("<hr style='margin:5px 0;border-color:#e0e0e0'>", unsafe_allow_html=True)

                    if st.session_state.get(f"editando_{row['ID_INVENTARIO']}", False):
                        with st.expander(f"✏️ Editar Inventário #{row['ID_INVENTARIO']}", expanded=True):
                            with st.form(f"form_edit_{row['ID_INVENTARIO']}"):
                                edit_site = st.text_input("SITE", value=row['SITE'])
                                edit_nave = st.text_input("NAVE", value=row['NAVE'])
                                edit_resp = st.text_input("RESPONSÁVEL", value=row['RESPONSAVEL'])
                                edit_ativo = st.checkbox("ATIVO", value=bool(row['ATIVO']))

                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Salvar", type="primary"):
                                        try:
                                            with engine.connect() as conn:
                                                conn.execute(
                                                    text("UPDATE Inventario SET SITE=:site, NAVE=:nave, RESPONSAVEL=:resp, ATIVO=:ativo WHERE ID_INVENTARIO=:id"),
                                                    {"site": edit_site, "nave": edit_nave, "resp": edit_resp, "ativo": 1 if edit_ativo else 0, "id": row['ID_INVENTARIO']}
                                                )
                                                conn.commit()
                                            st.success("Atualizado!")
                                            st.session_state[f"editando_{row['ID_INVENTARIO']}"] = False
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro: {e}")
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancelar"):
                                        st.session_state[f"editando_{row['ID_INVENTARIO']}"] = False
                                        st.rerun()

                if total_paginas > 1:
                    col_prev, col_info, col_next = st.columns([1, 2, 1])
                    with col_prev:
                        if st.button("◀️", key="prev_page", disabled=(pagina_atual == 1)):
                            st.session_state.page_inv -= 1
                    with col_info:
                        st.caption(f"Página {pagina_atual}/{total_paginas}")
                    with col_next:
                        if st.button("▶️", key="next_page", disabled=(pagina_atual == total_paginas)):
                            st.session_state.page_inv += 1
            else:
                st.info("Nenhum inventário encontrado.")
        except Exception as e:
            st.error(f"Erro: {e}")

    st.markdown("---")

    with st.expander("➕ Novo Inventário"):
        with st.form("form_criar_inventario"):
            site_new = st.text_input("SITE", placeholder="Ex: RMZ")
            nave_new = st.text_input("NAVE", placeholder="Ex: MP-NV01")
            resp_new = st.text_input("RESPONSÁVEL", placeholder="Nome do responsável")
            criar_sub = st.form_submit_button("Criar Inventário", width='stretch', type="primary")
            if criar_sub:
                if not site_new or not nave_new or not resp_new:
                    st.error("Preencha todos os campos.")
                else:
                    try:
                        engine = get_engine_sqlserver()
                        with engine.connect() as conn:
                            conn.execute(
                                text("INSERT INTO Inventario (SITE, NAVE, RESPONSAVEL, ATIVO) VALUES (:site, :nave, :resp, 1)"),
                                {"site": site_new, "nave": nave_new, "resp": resp_new}
                            )
                            conn.commit()
                        st.success("Inventário criado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.markdown("---")

    with st.expander("🔄 Carga Incremental"):
        if st.button("Atualizar Família Produto", width='stretch'):
            with st.spinner("Atualizando..."):
                try:
                    result = carga_incremental_familia()
                    st.success(result["mensagem"])
                    st.info(f"Novos: {result['novos']} | Alterados: {result['alterados']}")
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; padding: 4px 0;">'
        '<span style="color:#718096; font-size:0.75rem; font-weight:500;">AuditoriaApp v2.0.0</span><br>'
        '<span style="color:#a0aec0; font-size:0.65rem;">Acotubo © 2025</span>'
        '</div>',
        unsafe_allow_html=True
    )

# =============================
# TABS PRINCIPAIS
# =============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Material de Estoque",
    "📋 Lista de Contagem",
    "🧮 Rescaldo Estoque",
    "🧾 Rescaldo Contagem",
    "🔄 Família Produto"
])

# TAB 1 - MATERIAL ESTOQUE
with tab1:
    st.header("Material de Estoque")
    col_id, col_motivo = st.columns(2)
    with col_id:
        inv_id = st.number_input("ID do Inventário", min_value=1, step=1, value=1, key="inv1")
    with col_motivo:
        motivo_val = solicitar_motivo_ui("estoque")
    tab_site_nave_ou_lista("estoque", ler_material_estoque, "MaterialEstoque", "Material Estoque", inv_id, motivo_val)

# TAB 2 - LISTA CONTAGEM
with tab2:
    st.header("Lista de Contagem")
    col_id2, col_motivo2 = st.columns(2)
    with col_id2:
        inv_id2 = st.number_input("ID do Inventário", min_value=1, step=1, value=1, key="inv2")
    with col_motivo2:
        motivo2 = solicitar_motivo_ui("lista")
    tab_lista("lista", ler_lista_contagem, "RelContagem", "Lista de Contagem", inv_id2, motivo2)

# TAB 3 - MATERIAL RESCALDO
with tab3:
    st.header("Material de Estoque Rescaldo")
    col_id3, col_motivo3 = st.columns(2)
    with col_id3:
        inv_id3 = st.number_input("ID do Inventário", min_value=1, step=1, value=1, key="inv3")
    with col_motivo3:
        motivo3 = solicitar_motivo_ui("rescaldo")
    tab_site_nave_ou_lista("rescaldo", ler_material_rescaldo, "MaterialEstoqueRescaldo", "Material Rescaldo", inv_id3, motivo3)

# TAB 4 - CONTAGEM RESCALDO
with tab4:
    st.header("Lista de Contagem Rescaldo")
    col_id4, col_motivo4 = st.columns(2)
    with col_id4:
        inv_id4 = st.number_input("ID do Inventário", min_value=1, step=1, value=1, key="inv4")
    with col_motivo4:
        motivo4 = solicitar_motivo_ui("contagem_rescaldo")
    tab_lista("contagem_rescaldo", ler_lista_rescaldo, "RelContagemRescaldo", "Contagem Rescaldo", inv_id4, motivo4)

# TAB 5 - FAMILIA PRODUTO
with tab5:
    st.header("Carga Incremental - Família Produto")
    st.markdown("Atualiza a tabela `FamiliaProduto` no SQL Server com dados do Oracle.")

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info("**Tabela destino:** dbo.FamiliaProduto")
    with col_info2:
        st.info("**Fonte:** Oracle (inventory_part + part_catalog)")

    if st.button("🔄 Executar Carga Incremental", width='stretch', type="primary", key="btn_familia"):
        with st.spinner("Executando carga incremental... (pode levar alguns minutos)"):
            try:
                result = carga_incremental()
                st.success(f"✅ {result['mensagem']}")
                col_r1, col_r2, col_r3 = st.columns(3)
                with col_r1:
                    st.metric("Total Oracle", result["total_oracle"])
                with col_r2:
                    st.metric("Novos", result["novos"])
                with col_r3:
                    st.metric("Alterados", result["alterados"])
            except Exception as e:
                st.error(f"❌ Erro na carga incremental: {e}")

st.markdown("---")
st.markdown(
    '<div style="text-align:center; padding: 12px 0;">'
    '<p style="color:#a0aec0; font-size:0.8rem; margin:0;">AuditoriaApp v2.0.0 — Acotubo © 2025. Todos os direitos reservados.</p>'
    '</div>',
    unsafe_allow_html=True
)
