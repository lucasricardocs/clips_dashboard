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
SPREADSHEET_ID = "1NTScbiIna-iE7roQ9XBdjUOssRihTFFby4INAAQNXTg"
WORKSHEET_NAME = "Vendas"
LOGO_URL = "https://raw.githubusercontent.com/lucasricardocs/clips_dashboard/main/logo.png"

# Configuração da página Streamlit
st.set_page_config(
    page_title="Clips Burger - Mobile",
    layout="centered",
    page_icon=LOGO_URL,
    initial_sidebar_state="collapsed"
)

# Configuração de tema para gráficos - CORRIGIDO
alt.data_transformers.enable("json")
alt.data_transformers.disable_max_rows()

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
            background: #0f172a !important;
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Main content padding */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }

        /* Títulos H2 */
        h2 {
            color: #cbd5e1;
            font-size: 1.2rem;
            border-bottom: 1px solid #334155;
            padding-bottom: 0.5rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }

        /* Metric card styling */
        .stMetric {
            background-color: #1e293b;
            padding: 1rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            border: 1px solid #334155;
        }
        .stMetric > label {
            color: #94a3b8;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }
        .stMetric > div[data-testid="stMetricValue"] {
            color: #f1f5f9;
            font-size: 1.8rem;
            font-weight: 600;
            line-height: 1.2;
        }
        .stMetric > div[data-testid="stMetricDelta"] {
            font-size: 0.8rem;
            color: #64748b;
        }

        /* Monthly summary styling */
        .monthly-summary-item {
            display: flex;
            justify-content: space-between;
            padding: 0.4rem 0;
            border-bottom: 1px solid #334155;
        }
        .monthly-summary-item:last-child {
            border-bottom: none;
        }
        .monthly-summary-month {
            color: #cbd5e1;
            font-weight: 500;
        }
        .monthly-summary-value {
            color: #f1f5f9;
            font-weight: 600;
        }

        /* Chart container styling */
        .stAltairChart {
             background-color: #1e293b;
             padding: 1rem;
             border-radius: 0.75rem;
             margin-top: 1rem;
             border: 1px solid #334155;
        }

        /* Tabela de Vendas Diárias */
        .stDataFrame {
            background-color: #1e293b;
            border-radius: 0.75rem;
            border: 1px solid #334155;
            margin-top: 1rem;
        }
        .stDataFrame thead th {
            background-color: #334155;
            color: #e2e8f0;
        }
        .stDataFrame tbody tr:nth-child(even) {
            background-color: #1e293b;
        }
        .stDataFrame tbody tr:nth-child(odd) {
            background-color: #283447;
        }
        .stDataFrame tbody td {
            color: #e2e8f0;
        }

        /* Logo centralizada com animação */
        .centered-logo {
            display: block;
            margin-left: auto;
            margin-right: auto;
            max-width: 200px;
            width: 100%;
            height: auto;
            animation: logoEntrance 2s ease-out forwards;
            opacity: 0;
            transform: translateY(-20px) scale(0.8);
        }
        
        @keyframes logoEntrance {
            0% {
                opacity: 0;
                transform: translateY(-30px) scale(0.8) rotate(-5deg);
            }
            50% {
                opacity: 0.7;
                transform: translateY(-10px) scale(0.95) rotate(2deg);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1) rotate(0deg);
            }
        }
        
        .centered-logo:hover {
            transform: scale(1.05) rotate(2deg);
            transition: transform 0.3s ease-in-out;
            filter: brightness(1.1);
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

@st.cache_data(ttl=600)
def read_sales_data(_gc):
    """Lê e processa os dados da planilha."""
    if not _gc:
        return pd.DataFrame()
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
        df["DiaSemana"] = df["Data"].dt.dayofweek

        return df.sort_values("Data")

    except SpreadsheetNotFound:
        st.error(f"Planilha com ID '{SPREADSHEET_ID}' não encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler ou processar dados da planilha: {e}")
        return pd.DataFrame()

# --- Função para criar heatmap mensal estilo GitHub com cores CINZA/VERDE --- #
def create_monthly_activity_heatmap(df_month, mes_nome, ano):
    """Cria um heatmap estilo GitHub para o mês selecionado - CORES CINZA/VERDE."""
    if df_month.empty or 'Data' not in df_month.columns or 'Total' not in df_month.columns:
        return None
    
    try:
        # Obter o primeiro e último dia do mês
        primeiro_dia = datetime(ano, df_month['Mês'].iloc[0], 1)
        if df_month['Mês'].iloc[0] == 12:
            ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(ano, df_month['Mês'].iloc[0] + 1, 1) - timedelta(days=1)
        
        # Obter o dia da semana do primeiro dia do mês (0=segunda, 6=domingo)
        first_day_weekday = primeiro_dia.weekday()
        
        # Calcular quantos dias antes do primeiro dia precisamos para começar na segunda-feira
        days_before = first_day_weekday
        
        # Criar range de datas começando na segunda-feira da semana do primeiro dia
        start_date = primeiro_dia - pd.Timedelta(days=days_before)
        
        # Garantir que terminamos no domingo da última semana
        days_after = 6 - ultimo_dia.weekday()
        if days_after < 6:
            end_date = ultimo_dia + pd.Timedelta(days=days_after)
        else:
            end_date = ultimo_dia
        
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # DataFrame com todas as datas
        full_df = pd.DataFrame({'Data': all_dates})
        
        # Marcar quais datas são do mês atual
        full_df['is_current_month'] = (
            (full_df['Data'].dt.year == ano) & 
            (full_df['Data'].dt.month == df_month['Mês'].iloc[0])
        )
        
        # Merge com dados de vendas
        cols_to_merge = ['Data', 'Total']
        if 'Cartão' in df_month.columns:
            cols_to_merge.append('Cartão')
        if 'Dinheiro' in df_month.columns:
            cols_to_merge.append('Dinheiro')
        if 'Pix' in df_month.columns:
            cols_to_merge.append('Pix')
        
        cols_present = [col for col in cols_to_merge if col in df_month.columns]
        full_df = full_df.merge(df_month[cols_present], on='Data', how='left')
        
        # Preencher NaNs
        for col in ['Total', 'Cartão', 'Dinheiro', 'Pix']:
            if col in full_df.columns:
                full_df[col] = full_df[col].fillna(0)
            else:
                full_df[col] = 0
        
        # Para dias que não são do mês atual, definir como None
        full_df['display_total'] = full_df['Total'].copy()
        mask_not_current_month = ~full_df['is_current_month']
        full_df.loc[mask_not_current_month, 'display_total'] = None

        # Mapear os nomes dos dias
        full_df['day_of_week'] = full_df['Data'].dt.weekday
        day_name_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        full_df['day_display_name'] = full_df['day_of_week'].map(day_name_map)
        
        # Ordem fixa dos dias
        day_display_names = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        
        # Calcular semana
        full_df['week_corrected'] = ((full_df['Data'] - start_date).dt.days // 7)

        # Tooltip
        tooltip_fields = [
            alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
            alt.Tooltip('day_display_name:N', title='Dia'),
            alt.Tooltip('Total:Q', title='Total Vendas (R$)', format=',.2f')
        ]
        
        if full_df['Cartão'].sum() > 0:
            tooltip_fields.append(alt.Tooltip('Cartão:Q', title='Cartão (R$)', format=',.2f'))
        if full_df['Dinheiro'].sum() > 0:
            tooltip_fields.append(alt.Tooltip('Dinheiro:Q', title='Dinheiro (R$)', format=',.2f'))
        if full_df['Pix'].sum() > 0:
            tooltip_fields.append(alt.Tooltip('Pix:Q', title='Pix (R$)', format=',.2f'))

        # Domínio da escala baseado nos dados do mês
        max_value = full_df[full_df['is_current_month']]['Total'].max()
        if pd.isna(max_value) or max_value == 0:
            domain_values = [0.01, 500, 1000, 1500]
        else:
            domain_values = [0.01, max_value * 0.25, max_value * 0.5, max_value * 0.75]

        # Heatmap principal - CORES CINZA/VERDE E STROKE 2
        heatmap = alt.Chart(full_df).mark_rect(
            stroke='#334155',  # Cor da borda
            strokeWidth=2,     # Largura da borda = 2
            cornerRadius=2
        ).encode(
            x=alt.X('week_corrected:O', axis=None),
            y=alt.Y('day_display_name:N', 
                    sort=day_display_names,
                    axis=None),
            color=alt.Color('display_total:Q',
                scale=alt.Scale(
                    # NOVA PALETA: Cinza claro -> Verde claro -> Verde escuro
                    range=['#e5e7eb', '#bbf7d0', '#86efac', '#4ade80', '#22c55e', '#16a34a', '#15803d'],
                    type='threshold',
                    domain=domain_values
                ),
                legend=None),
            tooltip=tooltip_fields
        ).properties(
            height=180,
            width=350
        ).configure_view(
            stroke=None
        ).configure(
            background='transparent'
        )

        return heatmap
        
    except Exception as e:
        st.error(f"Erro ao criar heatmap mensal: {e}")
        return None

# --- Funções de Gráficos SEM TEXTOS --- #
def create_cumulative_chart_mobile(df_month):
    """Gráfico de área acumulado para o mês selecionado - SEM TEXTOS."""
    try:
        if df_month.empty:
            return None
        
        df_month = df_month.copy().sort_values("Dia")
        df_month["Total_Acumulado"] = df_month["Total"].cumsum()
        
        chart = alt.Chart(df_month).mark_area(
            interpolate="monotone",
            line={"color": CORES_MODO_ESCURO[0], "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color=CORES_MODO_ESCURO[0], offset=0), 
                    alt.GradientStop(color="#1e293b", offset=1)
                ],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X("Dia:O", axis=None),  # Remove todo o eixo X
            y=alt.Y("Total_Acumulado:Q", axis=None),  # Remove todo o eixo Y
            tooltip=[
                alt.Tooltip("Data:T", title="Data", format="%d/%m/%Y"),
                alt.Tooltip("Total:Q", title="Venda Dia (R$)", format=",.2f"),
                alt.Tooltip("Total_Acumulado:Q", title="Acumulado (R$)", format=",.2f")
            ]
        ).properties(
            height=300
        ).configure_view(
            stroke=None  # Remove borda
        ).configure(
            background="transparent"
        )
        return chart
    except Exception as e:
        st.error(f"Erro ao criar gráfico acumulado: {e}")
        return None

def create_daily_sales_chart_mobile(df_month):
    """Gráfico de barras de vendas diárias para o mês selecionado - SEM TEXTOS."""
    try:
        if df_month.empty:
            return None
        
        chart = alt.Chart(df_month).mark_bar(
            color=CORES_MODO_ESCURO[1], 
            size=15
        ).encode(
            x=alt.X("Dia:O", axis=None),  # Remove todo o eixo X
            y=alt.Y("Total:Q", axis=None),  # Remove todo o eixo Y
            tooltip=[
                alt.Tooltip("Data:T", title="Data", format="%d/%m/%Y"),
                alt.Tooltip("Total:Q", title="Venda (R$)", format=",.2f")
            ]
        ).properties(
            height=300
        ).configure_view(
            stroke=None  # Remove borda
        ).configure(
            background="transparent"
        )
        return chart
    except Exception as e:
        st.error(f"Erro ao criar gráfico de vendas diárias: {e}")
        return None

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

    # --- Logo Centralizada com Efeito --- #
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f'<img src="{LOGO_URL}" class="centered-logo">', unsafe_allow_html=True)

    # --- Filtros de Mês e Ano --- #
    anos_disponiveis = sorted(df_all["Ano"].unique(), reverse=True)
    meses_disponiveis = meses_ordem

    # Valores padrão: mês e ano atuais
    ano_atual = datetime.now().year
    mes_atual_nome = meses_ordem[datetime.now().month - 1]

    try:
        default_year_index = anos_disponiveis.index(ano_atual)
    except ValueError:
        default_year_index = 0

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
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    df_semana_atual = df_all[
        (df_all['Data'].dt.date >= inicio_semana) &
        (df_all['Data'].dt.date <= hoje)
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
        st.metric(label="Média Diária no Mês", value=format_brl(avg_daily_month), 
                 help=f"Baseado em {days_in_data} dias com vendas no mês.")

    # --- Resumo Mensal do Ano Selecionado ---
    st.header(f"🗓️ Faturamento Mensal ({ano_selecionado})")
    if not df_filtered_year.empty:
        monthly_revenue = df_filtered_year.groupby("Mês")["Total"].sum().reset_index()
        monthly_revenue["MêsNome"] = monthly_revenue["Mês"].apply(
            lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido"
        )
        monthly_revenue = monthly_revenue.set_index('Mês').reindex(range(1, 13)).reset_index()
        monthly_revenue['MêsNome'] = monthly_revenue['Mês'].apply(lambda x: meses_ordem[x-1])
        monthly_revenue['Total'] = monthly_revenue['Total'].fillna(0)

        with st.container():
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
        # Verificar se há dados suficientes para gráficos
        if len(df_filtered_month) > 0:
            # Heatmap estilo GitHub mensal (CORES CINZA/VERDE)
            heatmap_chart = create_monthly_activity_heatmap(df_filtered_month, mes_selecionado_nome, ano_selecionado)
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
            st.info("Dados insuficientes para gerar gráficos.")
    else:
        st.info(f"Sem dados de vendas registrados para {mes_selecionado_nome} de {ano_selecionado}.")

# --- Ponto de Entrada --- #
if __name__ == "__main__":
    main()
