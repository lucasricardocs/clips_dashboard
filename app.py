import streamlit as st
import gspread
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound
import warnings

# Suprimir warnings específicos do pandas
warnings.filterwarnings("ignore", category=FutureWarning, message=".*observed=False.*")

# --- Configurações Globais e Constantes ---
SPREADSHEET_ID = "1NTScbiIna-iE7roQ9XBdjUOssRihTFFby4INAAQNXTg" # Use o ID da sua planilha
WORKSHEET_NAME = "Vendas" # Nome da aba na planilha
LOGO_URL = "https://raw.githubusercontent.com/lucasricardocs/clipsburger/refs/heads/main/logo.png"

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

        /* Título */
        h1 {
            color: #f8fafc; /* Tailwind Slate 50 */
            font-size: 1.5rem; /* Tamanho adequado para mobile */
            text-align: center;
            margin-bottom: 1.5rem;
        }
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
            font-size: 2rem; /* Valor destacado */
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

    </style>
    """, unsafe_allow_html=True)

inject_mobile_dark_css()

# --- Funções de Cache e Acesso ao Google Sheets --- #
@st.cache_resource
def get_google_auth():
    """Autoriza o acesso ao Google Sheets."""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    try:
        # Tenta carregar do st.secrets primeiro
        if "google_credentials" in st.secrets:
            credentials_dict = st.secrets["google_credentials"]
            if credentials_dict:
                creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
                return gspread.authorize(creds)
            else:
                st.warning("Credenciais do Google em st.secrets estão vazias. Tentando carregar de 'credentials.json'.")

        # Fallback para arquivo local
        try:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
            # st.info("Credenciais carregadas de 'credentials.json'.")
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
            # Tenta formato brasileiro primeiro
            df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
            # Se falhar, tenta formato padrão
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

        return df.sort_values("Data") # Ordena por data

    except SpreadsheetNotFound:
        st.error(f"Planilha com ID '{SPREADSHEET_ID}' não encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler ou processar dados da planilha: {e}")
        return pd.DataFrame()

# --- Funções de Gráficos (Otimizadas para Mobile) --- #
def create_cumulative_chart_mobile(df_month):
    """Gráfico de área acumulado para o mês atual."""
    if df_month.empty:
        return None

    df_month = df_month.copy()
    df_month["Total_Acumulado"] = df_month["Total"].cumsum()

    chart = alt.Chart(df_month).mark_area(
        interpolate="monotone",
        line={"color": CORES_MODO_ESCURO[0], "strokeWidth": 2},
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color=CORES_MODO_ESCURO[0], offset=0), alt.GradientStop(color="#1e293b", offset=1)], # Gradiente para fundo escuro
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
    ).properties(
        height=350, # Altura menor para mobile
        # title=alt.TitleParams("Evolução Acumulada no Mês", anchor="start", color="#e2e8f0", dy=-15)
    ).configure_view(stroke=None).configure(background="transparent") # Fundo transparente

    return chart

def create_daily_sales_chart_mobile(df_month):
    """Gráfico de barras de vendas diárias para o mês atual."""
    if df_month.empty:
        return None

    chart = alt.Chart(df_month).mark_bar(
        color=CORES_MODO_ESCURO[1], # Cor verde
        size=12 # Barras mais finas
    ).encode(
        x=alt.X("Dia:O", axis=alt.Axis(title="Dia do Mês", labelAngle=0, labelColor="#94a3b8", titleColor="#94a3b8", gridColor="#334155")),
        y=alt.Y("Total:Q", axis=alt.Axis(title="Venda Diária (R$)", labelColor="#94a3b8", titleColor="#94a3b8", gridColor="#334155")),
        tooltip=[
            alt.Tooltip("Data:T", title="Data", format="%d/%m/%Y"),
            alt.Tooltip("Total:Q", title="Venda (R$)", format=",.2f")
        ]
    ).properties(
        height=350, # Altura menor para mobile
        # title=alt.TitleParams("Vendas Diárias no Mês", anchor="start", color="#e2e8f0", dy=-15)
    ).configure_view(stroke=None).configure(background="transparent")

    return chart

# --- Função para formatar moeda --- #
def format_brl(value):
    if value is None or not isinstance(value, (int, float)):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

# --- Aplicação Principal --- #
def main():
    # Autenticação e Leitura de Dados
    gc = get_google_auth()
    df_all = read_sales_data(gc)

    if df_all.empty:
        st.warning("Não foi possível carregar os dados da planilha ou ela está vazia.")
        return # Para a execução se não houver dados

    # Determinar ano e mês atuais
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_month_name = meses_ordem[current_month-1]

    # Filtrar dados para o ano e mês atuais
    df_current_year = df_all[df_all["Ano"] == current_year]
    df_current_month = df_current_year[df_current_year["Mês"] == current_month]

    # --- Layout do Dashboard --- #
    st.title(f"Dashboard Clips Burger")

    # KPIs do Mês Atual
    st.header(f"📊 Resumo de {current_month_name} / {current_year}")
    if not df_current_month.empty:
        total_month = df_current_month["Total"].sum()
        avg_daily_month = df_current_month["Total"].mean()
        days_in_data = df_current_month["Dia"].nunique()
    else:
        total_month = 0
        avg_daily_month = 0
        days_in_data = 0

    kpi_cols = st.columns(2)
    with kpi_cols[0]:
        st.metric(label="Faturamento no Mês", value=format_brl(total_month))
    with kpi_cols[1]:
        st.metric(label="Média Diária no Mês", value=format_brl(avg_daily_month), help=f"Baseado em {days_in_data} dias com vendas no mês.")

    # Resumo Mensal do Ano Vigente
    st.header(f"🗓️ Faturamento Mensal ({current_year})")
    if not df_current_year.empty:
        monthly_revenue = df_current_year.groupby("Mês")["Total"].sum().reset_index()
        # Adicionar nome do mês e ordenar
        monthly_revenue["MêsNome"] = monthly_revenue["Mês"].apply(lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido")
        monthly_revenue = monthly_revenue.sort_values("Mês")

        with st.container(border=False):
             st.markdown('<div class="monthly-summary-container">', unsafe_allow_html=True)
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
             st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info(f"Sem dados de vendas registrados para o ano de {current_year}.")

    # Gráficos do Mês Atual
    st.header(f"📈 Gráficos de {current_month_name}")
    if not df_current_month.empty:
        # Gráfico Acumulado
        cumulative_chart = create_cumulative_chart_mobile(df_current_month)
        if cumulative_chart:
            st.altair_chart(cumulative_chart, use_container_width=True)
        else:
            st.info("Gráfico acumulado indisponível.")

        # Gráfico Diário
        daily_chart = create_daily_sales_chart_mobile(df_current_month)
        if daily_chart:
            st.altair_chart(daily_chart, use_container_width=True)
        else:
            st.info("Gráfico de vendas diárias indisponível.")
    else:
        st.info(f"Sem dados de vendas registrados para {current_month_name} de {current_year}.")

# --- Ponto de Entrada --- #
if __name__ == "__main__":
    main()
