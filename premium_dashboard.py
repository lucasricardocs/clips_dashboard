import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import json

# Registrar componentes customizados
_animated_chart = components.declare_component(
    "animated_chart",
    path="./components/animated_charts/frontend/build"
)

_kpi_cards = components.declare_component(
    "kpi_cards", 
    path="./components/kpi_cards/frontend/build"
)

def animated_chart(data, chart_type="line", theme="dark", key=None):
    """Componente de gráfico animado"""
    return _animated_chart(
        data=data,
        chartType=chart_type,
        theme=theme,
        key=key
    )

def kpi_cards(data, theme="dark", key=None):
    """Componente de cards KPI animados"""
    return _kpi_cards(
        data=data,
        theme=theme,
        key=key
    )

def create_premium_dashboard(df_filtered):
    """Cria dashboard premium com componentes animados"""
    
    # CSS para tema escuro
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    .dashboard-header {
        background: linear-gradient(135deg, #ff6b35, #f7931e);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 20px 40px rgba(255, 107, 53, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header animado
    st.markdown("""
    <div class="dashboard-header">
        <h1 style="margin: 0; font-size: 3rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            🍔 CLIPS BURGER ANALYTICS PREMIUM
        </h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
            Dashboard Executivo com Animações Interativas
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_filtered.empty:
        # Preparar dados para KPIs
        total_vendas = df_filtered['Total'].sum()
        media_diaria = df_filtered['Total'].mean()
        crescimento = 15.5  # Calcular baseado nos dados reais
        
        kpi_data = [
            {
                "title": "Faturamento Total",
                "value": f"R$ {total_vendas:,.0f}".replace(",", "."),
                "change": crescimento,
                "icon": "💰",
                "color": "#64ffda"
            },
            {
                "title": "Média Diária", 
                "value": f"R$ {media_diaria:,.0f}".replace(",", "."),
                "change": 8.2,
                "icon": "📊",
                "color": "#ff9800"
            },
            {
                "title": "Melhor Dia",
                "value": df_filtered.loc[df_filtered['Total'].idxmax(), 'DataFormatada'] if not df_filtered.empty else "N/A",
                "change": 12.1,
                "icon": "🏆", 
                "color": "#4caf50"
            },
            {
                "title": "Tendência",
                "value": f"+{crescimento:.1f}%",
                "change": crescimento,
                "icon": "📈",
                "color": "#e91e63"
            }
        ]
        
        # Renderizar KPIs animados
        kpi_cards(kpi_data, theme="dark", key="kpi_dashboard")
        
        st.markdown("---")
        
        # Preparar dados para gráfico animado
        chart_data = []
        for _, row in df_filtered.iterrows():
            chart_data.append({
                "date": row['DataFormatada'],
                "cartao": float(row['Cartão']),
                "dinheiro": float(row['Dinheiro']),
                "pix": float(row['Pix']),
                "total": float(row['Total'])
            })
        
        # Controles do gráfico
        col1, col2 = st.columns([3, 1])
        
        with col2:
            chart_type = st.selectbox(
                "Tipo de Gráfico",
                ["line", "area", "bar"],
                format_func=lambda x: {"line": "📈 Linha", "area": "📊 Área", "bar": "📊 Barras"}[x]
            )
        
        with col1:
            # Renderizar gráfico animado
            animated_chart(
                chart_data, 
                chart_type=chart_type, 
                theme="dark",
                key="main_chart"
            )
    
    else:
        st.error("Não há dados para exibir o dashboard premium.")

# Função para integrar no app principal
def integrate_premium_dashboard(df_filtered):
    """Integra o dashboard premium no app principal"""
    
    # Adicionar tab premium
    tab_premium = st.container()
    
    with tab_premium:
        create_premium_dashboard(df_filtered)
