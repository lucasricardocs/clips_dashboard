import streamlit as st
import gspread
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound
import warnings

# Suprimir warnings específicos do pandas
warnings.filterwarnings("ignore", category=FutureWarning, message=".*observed=False.*")

# --- Configurações Globais e Constantes ---
SPREADSHEET_ID = "1NTScbiIna-iE7roQ9XBdjUOssRihTFFby4INAAQNXTg" # Use o ID da sua planilha
WORKSHEET_NAME = "Vendas" # Nome da aba na planilha
# LOGO_URL original: "https://raw.githubusercontent.com/lucasricardocs/clipsburger/refs/heads/main/logo.png"
LOGO_URL = "https://raw.githubusercontent.com/lucasricardocs/clips_dashboard/main/logo.png" # URL Raw da nova logo

# Configuração da página Streamlit
st.set_page_config(
    page_title="Clips Burger - Mobile",
    layout="centered", # Layout centralizado fica melhor em mobile
    page_icon=LOGO_URL,
    initial_sidebar_state="collapsed" # Sidebar recolhida por padrão
)

# Configuração de tema para gráficos
alt.data_transformers.enable("json")

# Paleta de cores para modo escuro
CORES_MODO_ESCURO = ["#4c78a8", "#54a24b", "#f58518", "#e45756", "#72b7b2", "#ff9da6", "#9d755d", "#bab0ac"]

# Ordem dos meses
meses_ordem = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
meses_dict = {nome: i+1 for i, nome in enumerate(meses_ordem)}

# --- CSS Customizado para App-Like Mobile Dark --- #
def inject_mobile_dark_css():
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Remove Streamlit header/footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Body/App Background */
        html, body, .stApp {
            background: #0f172a !important; /* Cor de fundo escura principal (Tailwind Slate 900) */
            color: #e2e8f0; /* Cor de texto clara (Tailwind Slate 200) */
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Main content padding */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%; /* Ocupar toda a largura no mobile */
        }

        /* Logo responsiva para mobile */
        div.block-container img {
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 1.5rem;
            max-width: 200px;        /* Tamanho máximo da logo */
            width: 60%;             /* 60% da largura do container */
            height: auto;           /* Mantém proporção */
        }

        /* Ajuste específico para telas muito pequenas */
        @media screen and (max-width: 480px) {
            div.block-container img {
                max-width: 150px;   /* Logo menor em telas pequenas */
                width: 50%;         /* 50% da largura em mobile */
            }
        }

        /* Ajuste para telas médias (tablets) */
        @media screen and (min-width: 481px) and (max-width: 768px) {
            div.block-container img {
                max-width: 180px;
                width: 55%;
            }
        }

        /* Títulos H2 */
        h2 {
            color: #cbd5e1; /* Tailwind Slate 300 */
            font-size: 1.2rem;
            border-bottom: 1px solid #334155; /* Tailwind Slate 700 */
            padding-bottom: 0.5rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }

        /* Metric card styling */
        .stMetric {
            background-color: #1e293b; /* Tailwind Slate 800 */
            padding: 1rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            border: 1px solid #334155; /* Tailwind Slate 700 */
        }
        .stMetric > label {
            color: #94a3b8; /* Tailwind Slate 400 */
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }
        .stMetric > div[data-testid="stMetricValue"] {
            color: #f1f5f9; /* Tailwind Slate 100 */
            font-size: 1.8rem; /* Ajuste leve no tamanho para caber melhor */
            font-weight: 600;
            line-height: 1.2;
        }
        .stMetric > div[data-testid="stMetricDelta"] {
            font-size: 0.8rem;
            color: #64748b; /* Tailwind Slate 500 */
        }

        /* Monthly summary styling */
        .monthly-summary-container {
            background-color: #1e293b; /* Tailwind Slate 800 */
            padding: 1rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            border: 1px solid #334155; /* Tailwind Slate 700 */
        }
        .monthly-summary-item {
            display: flex;
            justify-content: space-between;
            padding: 0.4rem 0;
            border-bottom: 1px solid #334155; /* Linha divisória sutil */
        }
        .monthly-summary-item:last-child {
            border-bottom: none;
        }
        .monthly-summary-month {
            color: #cbd5e1; /* Tailwind Slate 300 */
            font-weight: 500;
        }
        .monthly-summary-value {
            color: #f1f5f9; /* Tailwind Slate 100 */
            font-weight: 600;
        }

        /* Chart container styling */
        .stAltairChart {
             background-color: #1e293b; /* Fundo do container do gráfico */
             padding: 1rem;
             border-radius: 0.75rem;
             margin-top: 1rem;
             border: 1px solid #334155;
        }

        /* Specific chart adjustments */
        .stAltairChart vega-embed details summary {
            color: #94a3b8; /* Cor do botão de exportação */
        }

        /* Hide sidebar toggle button if not needed */
        button[kind="header"] {
            display: none;
        }

        /* Tabela de Vendas Diárias */
        .stDataFrame {
            background-color: #1e293b; /* Fundo da tabela */
            border-radius: 0.75rem;
            border: 1px solid #334155;
            margin-top: 1rem;
        }
        .stDataFrame thead th {
            background-color: #334155; /* Fundo do cabeçalho */
            color: #e2e8f0; /* Texto do cabeçalho */
        }
        .stDataFrame tbody tr:nth-child(even) {
            background-color: #1e293b; /* Cor linha par */
        }
        .stDataFrame tbody tr:nth-child(odd) {
            background-color: #283447; /* Cor linha ímpar (ligeiramente diferente) */
        }
        .stDataFrame tbody td {
            color: #e2e8f0; /* Cor do texto da célula */
        }

        /* Heatmap Calendar Styling */
        .heatmap-container {
            background-color: #1e293b;
            padding: 1rem;
            border-radius: 0.75rem;
            margin: 1rem 0;
            border: 1px solid #334155;
        }

    </style>
    """, unsafe_allow_html=True)

inject_mobile_dark_css()

# --- Funções de Cache e Acesso ao Google Sheets --- #
@st.cache_resource
def get_google_auth():
    """Autoriza o acesso ao Google Sheets."""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    try:
        if "google_credentials" in st.secrets:
            credentials_dict = st.secrets["google_credentials"]
            if credentials_dict:
                creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
                return gspread.authorize(creds)
            else:
                st.warning("Credenciais do Google em st.secrets estão vazias. Tentando carregar de 'credentials.json'.")
        try:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
            return gspread.authorize(creds)
        except FileNotFoundError:
            st.error("Erro: Arquivo 'credentials.json' não encontrado E credenciais não configuradas em st.secrets.")
            st.info("Configure suas credenciais em .streamlit/secrets.toml ou coloque credentials.json na raiz.")
            return None
        except Exception as e_file:
            st.error(f"Erro ao carregar 'credentials.json': {e_file}")
            return None
    except Exception as e_auth:
        st.error(f"Erro geral de autenticação com Google: {e_auth}")
        return None

@st.cache_data(ttl=600) # Cache de 10 minutos
def read_sales_data(_gc):
    """Lê e processa os dados da planilha."""
    if not _gc:
        return pd.DataFrame() # Retorna vazio se não autenticado
    try:
        spreadsheet = _gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        rows = worksheet.get_all_records()
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        
        # Processamento e limpeza
        for col in ["Cartão", "Dinheiro", "Pix"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            else:
                df[col] = 0

        if "Data" not in df.columns:
            st.error("Coluna 'Data' não encontrada na planilha!")
            return pd.DataFrame()

        try:
            df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
            if df["Data"].isnull().any():
                df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        except Exception:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

        df.dropna(subset=["Data"], inplace=True)
        if df.empty:
            return pd.DataFrame()

        df["Total"] = df["Cartão"] + df["Dinheiro"] + df["Pix"]
        df["Ano"] = df["Data"].dt.year
        df["Mês"] = df["Data"].dt.month
        df["Dia"] = df["Data"].dt.day
        df["MêsNome"] = df["Mês"].apply(lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido")
        df["DiaSemana"] = df["Data"].dt.dayofweek # 0 = Segunda, 6 = Domingo

        return df.sort_values("Data") # Ordena por data

    except SpreadsheetNotFound:
        st.error(f"Planilha com ID '{SPREADSHEET_ID}' não encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler ou processar dados da planilha: {e}")
        return pd.DataFrame()

# --- Função para criar heatmap estilo GitHub --- #
def create_github_heatmap(df_month, mes_nome, ano):
    """Cria um heatmap estilo GitHub calendar para o mês selecionado."""
    if df_month.empty:
        return None
    
    # Criar um DataFrame completo para todos os dias do mês
    primeiro_dia = datetime(ano, df_month['Mês'].iloc[0], 1)
    if df_month['Mês'].iloc[0] == 12:
        ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, df_month['Mês'].iloc[0] + 1, 1) - timedelta(days=1)
    
    # Criar range de datas para o mês completo
    datas_mes = pd.date_range(start=primeiro_dia, end=ultimo_dia, freq='D')
    df_completo = pd.DataFrame({'Data': datas_mes})
    df_completo['Dia'] = df_completo['Data'].dt.day
    df_completo['DiaSemana'] = df_completo['Data'].dt.dayofweek
    df_completo['Semana'] = ((df_completo['Data'].dt.day - 1) // 7)
    
    # Mapear dias da semana para nomes
    dias_semana_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
    df_completo['DiaSemanaTexto'] = df_completo['DiaSemana'].map(dias_semana_map)
    
    # Fazer merge com os dados de vendas
    df_vendas_agrupado = df_month.groupby('Dia')['Total'].sum().reset_index()
    df_heatmap = df_completo.merge(df_vendas_agrupado, on='Dia', how='left')
    df_heatmap['Total'] = df_heatmap['Total'].fillna(0)
    
    # Ajustar a semana para começar no domingo (padrão GitHub)
    df_heatmap['DiaSemana'] = (df_heatmap['DiaSemana'] + 1) % 7
    df_heatmap['DiaSemanaTexto'] = df_heatmap['DiaSemana'].map({
        0: 'Dom', 1: 'Seg', 2: 'Ter', 3: 'Qua', 4: 'Qui', 5: 'Sex', 6: 'Sáb'
    })
    
    # Calcular a semana baseada no primeiro domingo do mês
    primeiro_domingo = primeiro_dia
    while primeiro_domingo.weekday() != 6:  # 6 = domingo
        primeiro_domingo -= timedelta(days=1)
    
    df_heatmap['Semana'] = ((df_heatmap['Data'] - primeiro_domingo).dt.days // 7)
    
    # Criar o heatmap
    heatmap = alt.Chart(df_heatmap).mark_rect(
        stroke='#334155',
        strokeWidth=1
    ).encode(
        x=alt.X('Semana:O', 
                axis=alt.Axis(
                    title='Semanas do Mês',
                    labelColor='#94a3b8',
                    titleColor='#94a3b8',
                    grid=False
                )),
        y=alt.Y('DiaSemanaTexto:O', 
                scale=alt.Scale(domain=['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']),
                axis=alt.Axis(
                    title='Dia da Semana',
                    labelColor='#94a3b8',
                    titleColor='#94a3b8',
                    grid=False
                )),
        color=alt.Color('Total:Q',
                       scale=alt.Scale(
                           range=['#1e293b', '#0f4c75', '#3282b8', '#4c78a8', '#6bb6ff'],
                           domain=[0, df_heatmap['Total'].max()]
                       ),
                       legend=alt.Legend(
                           title="Vendas (R$)",
                           titleColor='#94a3b8',
                           labelColor='#94a3b8',
                           orient='bottom'
                       )),
        tooltip=[
            alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
            alt.Tooltip('DiaSemanaTexto:N', title='Dia da Semana'),
            alt.Tooltip('Total:Q', title='Vendas (R$)', format=',.2f')
        ]
    ).properties(
        width=300,
        height=150,
        title=alt.TitleParams(
            text=f'Calendário de Vendas - {mes_nome} {ano}',
            color='#cbd5e1',
            fontSize=14
        )
    ).configure_view(
        stroke=None
    ).configure(
        background='transparent'
    )
    
    return heatmap

# --- Funções de Gráficos (Otimizadas para Mobile) --- #
def create_cumulative_chart_mobile(df_month):
    """Gráfico de área acumulado para o mês selecionado."""
    if df_month.empty:
        return None
    df_month = df_month.copy().sort_values("Dia")
    df_month["Total_Acumulado"] = df_month["Total"].cumsum()
    chart = alt.Chart(df_month).mark_area(
        interpolate="monotone",
        line={"color": CORES_MODO_ESCURO[0], "strokeWidth": 2},
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color=CORES_MODO_ESCURO[0], offset=0), alt.GradientStop(color="#1e293b", offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X("Dia:O", axis=alt.Axis(title="Dia do Mês", labelAngle=0, labelColor="#94a3b8", titleColor="#94a3b8", gridColor="#334155")),
        y=alt.Y("Total_Acumulado:Q", axis=alt.Axis(title="Acumulado (R$)", labelColor="#94a3b8", titleColor="#94a3b8", gridColor="#334155")),
        tooltip=[
            alt.Tooltip("Data:T", title="Data", format="%d/%m/%Y"),
            alt.Tooltip("Total:Q", title="Venda Dia (R$)", format=",.2f"),
            alt.Tooltip("Total_Acumulado:Q", title="Acumulado (R$)", format=",.2f")
        ]
    ).properties(height=300).configure_view(stroke=None).configure(background="transparent")
    return chart

def create_daily_sales_chart_mobile(df_month):
    """Gráfico de barras de vendas diárias para o mês selecionado."""
    if df_month.empty:
        return None
    chart = alt.Chart(df_month).mark_bar(
        color=CORES_MODO_ESCURO[1], size=10
    ).encode(
        x=alt.X("Dia:O", axis=alt.Axis(title="Dia do Mês", labelAngle=0, labelColor="#94a3b8", titleColor="#94a3b8", gridColor="#334155")),
        y=alt.Y("Total:Q", axis=alt.Axis(title="Venda Diária (R$)", labelColor="#94a3b8", titleColor="#94a3b8", gridColor="#334155")),
        tooltip=[
            alt.Tooltip("Data:T", title="Data", format="%d/%m/%Y"),
            alt.Tooltip("Total:Q", title="Venda (R$)", format=",.2f")
        ]
    ).properties(height=300).configure_view(stroke=None).configure(background="transparent")
    return chart

# --- Função para formatar moeda --- #
def format_brl(value):
    if pd.isna(value) or not isinstance(value, (int, float)):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

# --- Aplicação Principal --- #
def main():
    # Autenticação e Leitura de Dados
    gc = get_google_auth()
    df_all = read_sales_data(gc)

    if df_all.empty:
        st.warning("Não foi possível carregar os dados da planilha ou ela está vazia.")
        return

    # --- Logo Centralizada (CORRIGIDA) --- #
    st.image(LOGO_URL, use_container_width=False, width=200)

    # --- Filtros de Mês e Ano --- #
    anos_disponiveis = sorted(df_all["Ano"].unique(), reverse=True)
    meses_disponiveis = meses_ordem

    # Valores padrão: mês e ano atuais
    ano_atual = datetime.now().year
    mes_atual_nome = meses_ordem[datetime.now().month - 1]

    # Define o índice padrão para o ano atual (se existir nos dados)
    try:
        default_year_index = anos_disponiveis.index(ano_atual)
    except ValueError:
        default_year_index = 0 # Usa o ano mais recente se o atual não estiver nos dados

    # Define o índice padrão para o mês atual
    default_month_index = meses_disponiveis.index(mes_atual_nome)

    col_filtros1, col_filtros2 = st.columns(2)
    with col_filtros1:
        ano_selecionado = st.selectbox(
            "Ano",
            anos_disponiveis,
            index=default_year_index
        )
    with col_filtros2:
        mes_selecionado_nome = st.selectbox(
            "Mês",
            meses_disponiveis,
            index=default_month_index
        )

    mes_selecionado_num = meses_dict[mes_selecionado_nome]

    # Filtrar dados com base na seleção
    df_filtered_year = df_all[df_all["Ano"] == ano_selecionado]
    df_filtered_month = df_filtered_year[df_filtered_year["Mês"] == mes_selecionado_num]

    # --- Cálculo Vendas Semana Atual --- #
    hoje = datetime.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday()) # Segunda-feira
    fim_semana = inicio_semana + timedelta(days=6) # Domingo

    # Filtrar df_all para a semana atual (considerando apenas a data, sem hora)
    df_semana_atual = df_all[
        (df_all['Data'].dt.date >= inicio_semana) &
        (df_all['Data'].dt.date <= hoje) # Considera até o dia atual
    ]
    total_semana_atual = df_semana_atual["Total"].sum()

    # --- Layout do Dashboard --- #

    # KPI Vendas Semana Atual (em destaque)
    st.metric(label="💰 Vendas Semana Atual (até hoje)", value=format_brl(total_semana_atual))

    # KPIs do Mês Selecionado
    st.header(f"📊 Resumo de {mes_selecionado_nome} / {ano_selecionado}")
    if not df_filtered_month.empty:
        total_month = df_filtered_month["Total"].sum()
        avg_daily_month = df_filtered_month["Total"].mean()
        days_in_data = df_filtered_month["Dia"].nunique()
    else:
        total_month = 0
        avg_daily_month = 0
        days_in_data = 0

    kpi_cols = st.columns(2)
    with kpi_cols[0]:
        st.metric(label="Faturamento no Mês", value=format_brl(total_month))
    with kpi_cols[1]:
        st.metric(label="Média Diária no Mês", value=format_brl(avg_daily_month), help=f"Baseado em {days_in_data} dias com vendas no mês.")

    # --- Resumo Mensal do Ano Selecionado ---
    st.header(f"🗓️ Faturamento Mensal ({ano_selecionado})")
    if not df_filtered_year.empty:
        monthly_revenue = df_filtered_year.groupby("Mês")["Total"].sum().reset_index()
        monthly_revenue["MêsNome"] = monthly_revenue["Mês"].apply(lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido")
        monthly_revenue = monthly_revenue.set_index('Mês').reindex(range(1, 13)).reset_index()
        monthly_revenue['MêsNome'] = monthly_revenue['Mês'].apply(lambda x: meses_ordem[x-1])
        monthly_revenue['Total'] = monthly_revenue['Total'].fillna(0)

        with st.container(border=False):
             if not monthly_revenue.empty:
                 for _, row in monthly_revenue.iterrows():
                     st.markdown(f"""
                     <div class="monthly-summary-item">
                         <span class="monthly-summary-month">{row['MêsNome']}</span>
                         <span class="monthly-summary-value">{format_brl(row['Total'])}</span>
                     </div>
                     """, unsafe_allow_html=True)
             else:
                 st.markdown('<div class="monthly-summary-item"><span>Nenhum dado para o ano.</span><span></span></div>', unsafe_allow_html=True)
    else:
        st.info(f"Sem dados de vendas registrados para o ano de {ano_selecionado}.")

    # Tabela de Vendas Diárias do Mês Selecionado
    st.header(f"📋 Vendas Diárias - {mes_selecionado_nome} / {ano_selecionado}")
    if not df_filtered_month.empty:
        df_daily_table = df_filtered_month[['Data', 'Total']].copy()
        df_daily_table['Data'] = df_daily_table['Data'].dt.strftime('%d/%m/%Y')
        df_daily_table['Total'] = df_daily_table['Total'].apply(format_brl)
        df_daily_table = df_daily_table.rename(columns={'Data': 'Dia', 'Total': 'Venda Total'})
        st.dataframe(df_daily_table, use_container_width=True, hide_index=True)
    else:
        st.info(f"Sem dados de vendas diárias para {mes_selecionado_nome} de {ano_selecionado}.")

    # Gráficos do Mês Selecionado
    st.header(f"📈 Gráficos - {mes_selecionado_nome} / {ano_selecionado}")
    if not df_filtered_month.empty:
        # Heatmap estilo GitHub (NOVO)
        heatmap_chart = create_github_heatmap(df_filtered_month, mes_selecionado_nome, ano_selecionado)
        if heatmap_chart:
            st.altair_chart(heatmap_chart, use_container_width=True)
        
        cumulative_chart = create_cumulative_chart_mobile(df_filtered_month)
        if cumulative_chart:
            st.altair_chart(cumulative_chart, use_container_width=True)
        else:
            st.info("Gráfico acumulado indisponível.")

        daily_chart = create_daily_sales_chart_mobile(df_filtered_month)
        if daily_chart:
            st.altair_chart(daily_chart, use_container_width=True)
        else:
            st.info("Gráfico de vendas diárias indisponível.")
    else:
        st.info(f"Sem dados de vendas registrados para {mes_selecionado_nome} de {ano_selecionado}.")

# --- Ponto de Entrada --- #
if __name__ == "__main__":
    main()
