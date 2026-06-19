"""
SoilCarbon Planner
Sistema Inteligente de Coberturas Vegetais e Incremento de Matéria Orgânica do Solo
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import requests
import io
import base64

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="SoilCarbon Planner",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ESTILO CSS PERSONALIZADO
# ============================================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1b5e20 0%, #388e3c 50%, #4caf50 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #c8e6c9;
        margin: 5px 0 0 0;
        font-size: 1.1rem;
    }
    .stButton > button {
        background-color: #2e7d32;
        color: white;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #1b5e20;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# BANCO DE DADOS DE ESPÉCIES
# ============================================================================

BANCO_ESPECIES = {
    "Milheto": {
        "biomassa_min": 8, "biomassa_max": 12,
        "persistencia": "90-120 dias",
        "carbono_incremento": "1.8-2.4",
        "relacao_cn": 60,
        "lignina": 8.5,
        "adaptacao": ["Cerrado", "Caatinga", "Pantanal"],
        "objetivos": ["Palhada", "Carbono", "Descompactação"],
        "decomp_k": 0.035
    },
    "Crotalária": {
        "biomassa_min": 6, "biomassa_max": 10,
        "persistencia": "60-90 dias",
        "carbono_incremento": "1.2-1.8",
        "relacao_cn": 25,
        "lignina": 5.2,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia", "Caatinga", "Pantanal"],
        "objetivos": ["Nitrogênio", "Palhada", "Nematoides"],
        "decomp_k": 0.045
    },
    "Braquiária brizantha": {
        "biomassa_min": 10, "biomassa_max": 18,
        "persistencia": "120-180 dias",
        "carbono_incremento": "2.5-3.5",
        "relacao_cn": 70,
        "lignina": 10.2,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia", "Pantanal"],
        "objetivos": ["Carbono", "Palhada", "Pastagem"],
        "decomp_k": 0.025
    },
    "Braquiária ruziziensis": {
        "biomassa_min": 8, "biomassa_max": 14,
        "persistencia": "90-150 dias",
        "carbono_incremento": "2.0-3.0",
        "relacao_cn": 65,
        "lignina": 9.1,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia"],
        "objetivos": ["Palhada", "Carbono"],
        "decomp_k": 0.030
    },
    "Feijão-guandu": {
        "biomassa_min": 5, "biomassa_max": 9,
        "persistencia": "60-90 dias",
        "carbono_incremento": "1.0-1.5",
        "relacao_cn": 20,
        "lignina": 4.8,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia", "Caatinga", "Pantanal"],
        "objetivos": ["Nitrogênio", "Palhada", "Reciclagem"],
        "decomp_k": 0.040
    },
    "Capim mombaça": {
        "biomassa_min": 12, "biomassa_max": 20,
        "persistencia": "150-210 dias",
        "carbono_incremento": "3.0-4.0",
        "relacao_cn": 75,
        "lignina": 11.5,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia"],
        "objetivos": ["Carbono", "Palhada"],
        "decomp_k": 0.020
    },
    "Aveia-preta": {
        "biomassa_min": 4, "biomassa_max": 7,
        "persistencia": "60-90 dias",
        "carbono_incremento": "0.8-1.2",
        "relacao_cn": 40,
        "lignina": 6.3,
        "adaptacao": ["Pampa", "Mata Atlântica"],
        "objetivos": ["Palhada", "Reciclagem"],
        "decomp_k": 0.042
    },
    "Ervilhaca": {
        "biomassa_min": 3, "biomassa_max": 6,
        "persistencia": "45-75 dias",
        "carbono_incremento": "0.6-1.0",
        "relacao_cn": 15,
        "lignina": 3.8,
        "adaptacao": ["Pampa", "Mata Atlântica"],
        "objetivos": ["Nitrogênio", "Palhada"],
        "decomp_k": 0.045
    },
    "Nabo-forrageiro": {
        "biomassa_min": 4, "biomassa_max": 8,
        "persistencia": "45-60 dias",
        "carbono_incremento": "0.8-1.2",
        "relacao_cn": 30,
        "lignina": 4.2,
        "adaptacao": ["Cerrado", "Pampa", "Mata Atlântica"],
        "objetivos": ["Descompactação", "Reciclagem"],
        "decomp_k": 0.048
    },
    "Sorgo": {
        "biomassa_min": 8, "biomassa_max": 15,
        "persistencia": "90-120 dias",
        "carbono_incremento": "1.8-2.8",
        "relacao_cn": 55,
        "lignina": 7.8,
        "adaptacao": ["Cerrado", "Caatinga", "Pantanal"],
        "objetivos": ["Palhada", "Carbono"],
        "decomp_k": 0.032
    },
    "Soja": {
        "biomassa_min": 3, "biomassa_max": 5,
        "persistencia": "30-60 dias",
        "carbono_incremento": "0.5-0.8",
        "relacao_cn": 12,
        "lignina": 3.2,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Pampa"],
        "objetivos": ["Nitrogênio", "Reciclagem"],
        "decomp_k": 0.050
    },
    "Puerária": {
        "biomassa_min": 6, "biomassa_max": 10,
        "persistencia": "90-150 dias",
        "carbono_incremento": "1.5-2.2",
        "relacao_cn": 50,
        "lignina": 7.5,
        "adaptacao": ["Amazônia", "Mata Atlântica"],
        "objetivos": ["Palhada", "Carbono", "Nitrogênio"],
        "decomp_k": 0.028
    }
}

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

def init_session_state():
    """Inicializa todas as variáveis do session_state"""
    
    if "cadastro" not in st.session_state:
        st.session_state["cadastro"] = {
            "nome": "",
            "email": "",
            "telefone": "",
            "fazenda": "",
            "municipio": "",
            "estado": "",
            "area_total": 0.0,
            "latitude": -15.0,
            "longitude": -50.0,
        }
    
    if "manejo" not in st.session_state:
        st.session_state["manejo"] = {
            "tipo": "Plantio Direto Consolidado",
            "anos": 5,
            "culturas": [],
            "materia_organica": 2.5,
            "argila": 30.0,
            "ph": 6.0,
            "ctc": 8.0,
            "temperatura_media": 25.0,
            "precipitacao": 1500.0,
        }
    
    if "cobertura" not in st.session_state:
        st.session_state["cobertura"] = {
            "objetivo": "Produzir palhada",
            "bioma": "",
            "clima": "",
            "recomendacoes": [],
            "periodo_seco": 90,
            "regiao": "Centro-Oeste",
        }
    
    if "consorcio" not in st.session_state:
        st.session_state["consorcio"] = {
            "cultura_principal": "Soja",
            "consorcios": [],
        }
    
    if "decomposicao" not in st.session_state:
        st.session_state["decomposicao"] = {
            "cobertura": "Braquiária brizantha",
            "massa_seca": 8.0,
            "dados_simulacao": None,
        }
    
    if "relatorio" not in st.session_state:
        st.session_state["relatorio"] = {
            "gerado": False,
            "conteudo": "",
        }


def calcular_qualidade_manejo(mo, argila, ph, ctc, anos_pd):
    """Calcula a qualidade do manejo baseado nos indicadores (argila agora é usada)"""
    pontuacao = 0
    
    # Matéria orgânica (0-10%)
    if mo >= 4.0:
        pontuacao += 25
    elif mo >= 3.0:
        pontuacao += 20
    elif mo >= 2.0:
        pontuacao += 15
    elif mo >= 1.0:
        pontuacao += 10
    else:
        pontuacao += 5
    
    # pH (5.5-6.5 ideal)
    if 5.5 <= ph <= 6.5:
        pontuacao += 25
    elif 5.0 <= ph <= 7.0:
        pontuacao += 20
    else:
        pontuacao += 10
    
    # CTC (meq/100g)
    if ctc >= 10:
        pontuacao += 25
    elif ctc >= 6:
        pontuacao += 20
    else:
        pontuacao += 10
    
    # Anos em plantio direto
    if anos_pd >= 10:
        pontuacao += 25
    elif anos_pd >= 5:
        pontuacao += 20
    elif anos_pd >= 3:
        pontuacao += 15
    else:
        pontuacao += 5
    
    # Argila (%) - AGORA USADA!
    if argila >= 60:
        pontuacao += 10
    elif argila >= 35:
        pontuacao += 7
    else:
        pontuacao += 3
    
    if pontuacao >= 95:
        return "Excelente"
    elif pontuacao >= 80:
        return "Boa"
    elif pontuacao >= 65:
        return "Média"
    elif pontuacao >= 45:
        return "Baixa"
    else:
        return "Muito baixa"


def recomendar_coberturas_inteligentes(objetivo, bioma, periodo_seco, regiao):
    """
    Recomenda coberturas baseadas em objetivo, bioma, período seco e região
    Usa o banco de dados de espécies
    """
    recomendacoes = []
    
    for especie, dados in BANCO_ESPECIES.items():
        # Verifica adaptação ao bioma
        if bioma in dados["adaptacao"]:
            # Verifica se atende ao objetivo
            if objetivo in dados["objetivos"]:
                # Verifica período seco
                persistencia_dias = int(dados["persistencia"].split("-")[0])
                if persistencia_dias >= periodo_seco * 0.7:
                    recomendacoes.append({
                        "especie": especie,
                        "biomassa": f"{dados['biomassa_min']}-{dados['biomassa_max']}",
                        "persistencia": dados["persistencia"],
                        "carbono": dados["carbono_incremento"],
                        "relacao_cn": dados["relacao_cn"],
                        "score": (dados["biomassa_max"] / 20) * 100 + (dados["relacao_cn"] / 80) * 100
                    })
    
    # Ordena por score
    recomendacoes.sort(key=lambda x: x["score"], reverse=True)
    
    # Retorna as 3 melhores
    return recomendacoes[:3]


def recomendar_consorcios(cultura_principal):
    """Recomenda consórcios baseado na cultura principal"""
    consorcios = {
        "Soja": [
            {"nome": "Soja + Braquiária", "beneficios": ["↑ Matéria orgânica", "↑ Infiltração", "↑ CTC"], "impacto": "0 a -5%"},
            {"nome": "Soja + Crotalária (safrinha)", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"], "impacto": "0 a -3%"},
            {"nome": "Soja + Milheto (safrinha)", "beneficios": ["↑ Palhada", "↑ Matéria orgânica"], "impacto": "0 a -4%"}
        ],
        "Milho": [
            {"nome": "Milho + Braquiária", "beneficios": ["↑ Matéria orgânica", "↑ Infiltração", "Pastagem"], "impacto": "0 a -8%"},
            {"nome": "Milho + Crotalária", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"], "impacto": "0 a -10%"},
            {"nome": "Milho + Feijão-guandu", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Reciclagem nutrientes"], "impacto": "0 a -7%"}
        ],
        "Algodão": [
            {"nome": "Algodão + Crotalária (safrinha)", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"], "impacto": "0 a -5%"},
            {"nome": "Algodão + Milheto (safrinha)", "beneficios": ["↑ Palhada", "↑ Matéria orgânica"], "impacto": "0 a -6%"}
        ],
        "Feijão": [
            {"nome": "Feijão + Braquiária", "beneficios": ["↑ Matéria orgânica", "↑ Infiltração"], "impacto": "0 a -5%"},
            {"nome": "Feijão + Crotalária", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica"], "impacto": "0 a -4%"}
        ]
    }
    
    return consorcios.get(cultura_principal, [
        {"nome": "Recomendação padrão", "beneficios": ["↑ Matéria orgânica", "↑ Infiltração"], "impacto": "0 a -5%"}
    ])


def simular_decomposicao(cobertura, massa_seca, temperatura=25, precipitacao=1500, argila=30):
    """
    Simula a decomposição com fatores de correção
    Agora corrigido: MO = Carbono * 1.724
    """
    
    # Coeficiente base
    coef_decomp = {
        "Crotalária": 0.045,
        "Feijão-guandu": 0.040,
        "Milheto": 0.035,
        "Braquiária ruziziensis": 0.030,
        "Braquiária brizantha": 0.025,
        "Capim mombaça": 0.020,
        "Aveia-preta": 0.042,
        "Ervilhaca": 0.045,
        "Nabo-forrageiro": 0.048,
        "Sorgo": 0.032,
        "Soja": 0.050,
        "Puerária": 0.028,
    }
    
    k_base = coef_decomp.get(cobertura, 0.030)
    
    # Fatores de correção
    # Temperatura (ótimo: 25-30°C)
    if 25 <= temperatura <= 30:
        f_temp = 1.0
    elif temperatura > 30:
        f_temp = 0.8
    else:
        f_temp = 0.6 + (temperatura - 10) / 50
    
    # Precipitação (ótimo: 1200-1800 mm)
    if 1200 <= precipitacao <= 1800:
        f_prec = 1.0
    elif precipitacao > 1800:
        f_prec = 0.9
    else:
        f_prec = 0.5 + (precipitacao / 2400)
    
    # Argila (textura)
    if argila >= 60:  # Argiloso
        f_argila = 0.7
    elif argila >= 35:  # Média
        f_argila = 0.9
    else:  # Arenoso
        f_argila = 1.2
    
    # Coeficiente ajustado
    k = k_base * f_temp * f_prec * f_argila
    
    dias = [0, 30, 60, 90, 120, 150, 180]
    
    dados = []
    
    for t in dias:
        massa_restante = massa_seca * np.exp(-k * t)
        decomposicao = ((massa_seca - massa_restante) / massa_seca) * 100
        carbono = massa_restante * 0.45  # 45% de carbono
        mo = carbono * 1.724  # CORRIGIDO: carbono * 1.724
        
        dados.append({
            "Dias": t,
            "Massa Restante (t/ha)": round(massa_restante, 2),
            "Decomposição (%)": round(decomposicao, 1),
            "Carbono (t/ha)": round(carbono, 2),
            "Matéria Orgânica (t/ha)": round(mo, 2)
        })
    
    return pd.DataFrame(dados)


def criar_grafico_decomposicao(df):
    """Cria gráfico de decomposição usando Matplotlib com sintaxe mais robusta"""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Decomposição
    axes[0, 0].plot(df["Dias"], df["Decomposição (%)"], 
                    marker='o', color='blue', linewidth=2, markersize=8)
    axes[0, 0].set_title('Decomposição (%)', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Dias')
    axes[0, 0].set_ylabel('Decomposição (%)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Massa Restante
    axes[0, 1].plot(df["Dias"], df["Massa Restante (t/ha)"], 
                    marker='o', color='green', linewidth=2, markersize=8)
    axes[0, 1].set_title('Massa Restante (t/ha)', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Dias')
    axes[0, 1].set_ylabel('Massa Restante (t/ha)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Carbono
    axes[1, 0].plot(df["Dias"], df["Carbono (t/ha)"], 
                    marker='o', color='orange', linewidth=2, markersize=8)
    axes[1, 0].set_title('Carbono Residual (t/ha)', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Dias')
    axes[1, 0].set_ylabel('Carbono (t/ha)')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Matéria Orgânica
    axes[1, 1].plot(df["Dias"], df["Matéria Orgânica (t/ha)"], 
                    marker='o', color='red', linewidth=2, markersize=8)
    axes[1, 1].set_title('Matéria Orgânica Adicionada (t/ha)', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Dias')
    axes[1, 1].set_ylabel('Matéria Orgânica (t/ha)')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def identificar_bioma_manual(lat, lon):
    """Identifica bioma com fallback para seleção manual"""
    
    # Tenta API, mas não para a aplicação se falhar
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "SoilCarbonPlanner/1.0"}
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            estado = address.get("state", "")
            
            # Mapeamento simplificado
            if "Mato Grosso" in estado or "Goiás" in estado or "Distrito Federal" in estado:
                return "Cerrado", "Aw"
            elif "Amazonas" in estado or "Pará" in estado or "Rondônia" in estado:
                return "Amazônia", "Af"
            elif "Rio Grande do Sul" in estado or "Santa Catarina" in estado:
                return "Pampa", "Cfa"
            elif "Pernambuco" in estado or "Ceará" in estado or "Bahia" in estado:
                return "Caatinga", "Aw"
            elif "Mato Grosso do Sul" in estado:
                return "Pantanal", "Aw"
            else:
                return "Mata Atlântica", "Af"
    except:
        pass
    
    # Fallback baseado em coordenadas
    if lat < -15 and lat > -33 and lon < -50 and lon > -60:
        return "Pampa", "Cfa"
    elif lat < -5 and lat > -15:
        return "Cerrado", "Aw"
    elif lat < -5 and lon < -60:
        return "Amazônia", "Af"
    elif lat > -5 and lon > -45:
        return "Mata Atlântica", "Af"
    else:
        return "Cerrado", "Aw"


def download_excel(df):
    """Cria um arquivo Excel para download"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Simulação')
    return output.getvalue()

# ============================================================================
# FUNÇÕES DE RENDERIZAÇÃO DE CADA ABA
# ============================================================================

def render_cadastro():
    """Renderiza a página de cadastro"""
    
    st.title("📋 Cadastro do Usuário e Propriedade")
    st.markdown("---")
    
    init_session_state()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Dados do Usuário")
        
        nome = st.text_input(
            "Nome Completo",
            value=st.session_state["cadastro"]["nome"],
            key="cad_nome"
        )
        
        email = st.text_input(
            "E-mail",
            value=st.session_state["cadastro"]["email"],
            key="cad_email"
        )
        
        telefone = st.text_input(
            "Telefone",
            value=st.session_state["cadastro"]["telefone"],
            key="cad_telefone"
        )
    
    with col2:
        st.subheader("🏢 Dados da Propriedade")
        
        fazenda = st.text_input(
            "Nome da Fazenda",
            value=st.session_state["cadastro"]["fazenda"],
            key="cad_fazenda"
        )
        
        municipio = st.text_input(
            "Município",
            value=st.session_state["cadastro"]["municipio"],
            key="cad_municipio"
        )
        
        estado = st.text_input(
            "Estado (UF)",
            value=st.session_state["cadastro"]["estado"],
            key="cad_estado"
        )
        
        area_total = st.number_input(
            "Área Total (ha)",
            min_value=0.0,
            value=st.session_state["cadastro"]["area_total"],
            key="cad_area"
        )
    
    st.markdown("---")
    
    st.subheader("📍 Localização")
    
    col3, col4 = st.columns(2)
    
    with col3:
        latitude = st.number_input(
            "Latitude",
            min_value=-33.75,
            max_value=5.27,
            value=st.session_state["cadastro"]["latitude"],
            format="%.4f",
            key="cad_lat"
        )
    
    with col4:
        longitude = st.number_input(
            "Longitude",
            min_value=-73.98,
            max_value=-34.79,
            value=st.session_state["cadastro"]["longitude"],
            format="%.4f",
            key="cad_lon"
        )
    
    st.markdown("---")
    
    if st.button("💾 SALVAR CADASTRO", use_container_width=True, type="primary"):
        st.session_state["cadastro"]["nome"] = nome
        st.session_state["cadastro"]["email"] = email
        st.session_state["cadastro"]["telefone"] = telefone
        st.session_state["cadastro"]["fazenda"] = fazenda
        st.session_state["cadastro"]["municipio"] = municipio
        st.session_state["cadastro"]["estado"] = estado
        st.session_state["cadastro"]["area_total"] = area_total
        st.session_state["cadastro"]["latitude"] = latitude
        st.session_state["cadastro"]["longitude"] = longitude
        
        st.success("✅ Cadastro salvo com sucesso!")
        st.balloons()
    
    with st.expander("📊 Dados Salvos", expanded=False):
        st.json(st.session_state["cadastro"])


def render_manejo():
    """Renderiza a página de manejo"""
    
    st.title("🔬 Diagnóstico do Sistema de Manejo")
    st.markdown("---")
    
    init_session_state()
    
    st.subheader("🌾 Tipo de Manejo Atual")
    
    tipos_manejo = [
        "Convencional",
        "Semi Convencional",
        "Plantio Direto em Transição",
        "Plantio Direto Consolidado"
    ]
    
    tipo = st.selectbox(
        "Selecione o manejo atual",
        tipos_manejo,
        index=tipos_manejo.index(st.session_state["manejo"]["tipo"]) 
        if st.session_state["manejo"]["tipo"] in tipos_manejo else 0,
        key="man_tipo"
    )
    
    st.markdown("---")
    
    st.subheader("📅 Histórico da Área")
    
    anos_pd = st.number_input(
        "Anos em Plantio Direto",
        min_value=0,
        max_value=50,
        value=st.session_state["manejo"]["anos"],
        key="man_anos"
    )
    
    st.markdown("---")
    
    st.subheader("🔄 Rotação de Culturas")
    
    culturas_opcoes = [
        "Soja", "Milho", "Algodão", "Feijão", 
        "Sorgo", "Trigo", "Braquiária", "Outros"
    ]
    
    culturas_selecionadas = st.multiselect(
        "Culturas utilizadas na rotação",
        culturas_opcoes,
        default=st.session_state["manejo"]["culturas"],
        key="man_culturas"
    )
    
    st.markdown("---")
    
    st.subheader("📊 Indicadores do Solo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mo = st.number_input(
            "Teor de Matéria Orgânica (%)",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state["manejo"]["materia_organica"],
            step=0.1,
            format="%.1f",
            key="man_mo"
        )
        
        argila = st.number_input(
            "Argila (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state["manejo"]["argila"],
            step=1.0,
            key="man_argila"
        )
    
    with col2:
        ph = st.number_input(
            "pH do Solo",
            min_value=3.0,
            max_value=9.0,
            value=st.session_state["manejo"]["ph"],
            step=0.1,
            format="%.1f",
            key="man_ph"
        )
        
        ctc = st.number_input(
            "CTC (meq/100g)",
            min_value=0.0,
            max_value=50.0,
            value=st.session_state["manejo"]["ctc"],
            step=0.5,
            key="man_ctc"
        )
    
    st.markdown("---")
    
    st.subheader("🌡️ Fatores Climáticos")
    
    col3, col4 = st.columns(2)
    
    with col3:
        temperatura = st.number_input(
            "Temperatura Média (°C)",
            min_value=10.0,
            max_value=35.0,
            value=st.session_state["manejo"].get("temperatura_media", 25.0),
            step=0.5,
            key="man_temp"
        )
    
    with col4:
        precipitacao = st.number_input(
            "Precipitação Anual (mm)",
            min_value=200.0,
            max_value=4000.0,
            value=st.session_state["manejo"].get("precipitacao", 1500.0),
            step=50.0,
            key="man_prec"
        )
    
    st.markdown("---")
    
    st.session_state["manejo"]["tipo"] = tipo
    st.session_state["manejo"]["anos"] = anos_pd
    st.session_state["manejo"]["culturas"] = culturas_selecionadas
    st.session_state["manejo"]["materia_organica"] = mo
    st.session_state["manejo"]["argila"] = argila
    st.session_state["manejo"]["ph"] = ph
    st.session_state["manejo"]["ctc"] = ctc
    st.session_state["manejo"]["temperatura_media"] = temperatura
    st.session_state["manejo"]["precipitacao"] = precipitacao
    
    st.subheader("⭐ Qualidade do Manejo")
    
    qualidade = calcular_qualidade_manejo(mo, argila, ph, ctc, anos_pd)
    
    cores = {
        "Excelente": "🟢",
        "Boa": "🔵",
        "Média": "🟡",
        "Baixa": "🟠",
        "Muito baixa": "🔴"
    }
    
    st.markdown(f"""
    <div style='
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    '>
        <h2>{cores.get(qualidade, '')} {qualidade}</h2>
        <p style='font-size: 14px; color: #666;'>
            Baseado nos indicadores de matéria orgânica, pH, CTC, argila e anos em plantio direto
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📊 Salvar Diagnóstico", use_container_width=True, type="primary"):
        st.success("✅ Diagnóstico salvo com sucesso!")


def render_cobertura():
    """Renderiza a página de coberturas vegetais"""
    
    st.title("🌿 Planejamento de Coberturas Vegetais")
    st.markdown("---")
    
    init_session_state()
    
    st.subheader("📍 Localização e Bioma")
    
    lat = st.session_state["cadastro"]["latitude"]
    lon = st.session_state["cadastro"]["longitude"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Latitude", f"{lat:.4f}")
    
    with col2:
        st.metric("Longitude", f"{lon:.4f}")
    
    # Identificação automática (com fallback)
    if not st.session_state["cobertura"]["bioma"]:
        bioma, clima = identificar_bioma_manual(lat, lon)
        st.session_state["cobertura"]["bioma"] = bioma
        st.session_state["cobertura"]["clima"] = clima
    
    # Seleção manual (MAIS ROBUSTO)
    biomas = ["Cerrado", "Mata Atlântica", "Amazônia", "Caatinga", "Pantanal", "Pampa"]
    
    bioma_selecionado = st.selectbox(
        "Bioma da propriedade (selecione manualmente se o automático falhar)",
        biomas,
        index=biomas.index(st.session_state["cobertura"]["bioma"]) 
        if st.session_state["cobertura"]["bioma"] in biomas else 0,
        key="cov_bioma"
    )
    
    st.session_state["cobertura"]["bioma"] = bioma_selecionado
    
    col3, col4 = st.columns(2)
    
    with col3:
        periodo_seco = st.number_input(
            "Período seco (dias)",
            min_value=0,
            max_value=300,
            value=st.session_state["cobertura"].get("periodo_seco", 90),
            key="cov_periodo"
        )
        st.session_state["cobertura"]["periodo_seco"] = periodo_seco
    
    with col4:
        regioes = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
        regiao = st.selectbox(
            "Região",
            regioes,
            index=regioes.index(st.session_state["cobertura"].get("regiao", "Centro-Oeste")) 
            if st.session_state["cobertura"].get("regiao") in regioes else 2,
            key="cov_regiao"
        )
        st.session_state["cobertura"]["regiao"] = regiao
    
    if st.session_state["cobertura"]["bioma"]:
        st.info(f"""
        **🌍 Bioma:** {st.session_state['cobertura']['bioma']}
        **☀️ Clima:** {st.session_state['cobertura']['clima']}
        **🗺️ Região:** {regiao}
        **🌵 Período seco:** {periodo_seco} dias
        """)
    
    st.markdown("---")
    
    st.subheader("🎯 Objetivo da Cobertura Vegetal")
    
    objetivos = [
        "Produzir palhada",
        "Produzir matéria orgânica",
        "Descompactação",
        "Reciclagem de nutrientes",
        "Fixação biológica de nitrogênio",
        "Controle de nematoides"
    ]
    
    objetivo = st.selectbox(
        "Selecione o principal objetivo",
        objetivos,
        index=objetivos.index(st.session_state["cobertura"]["objetivo"]) 
        if st.session_state["cobertura"]["objetivo"] in objetivos else 0,
        key="cov_objetivo"
    )
    
    st.session_state["cobertura"]["objetivo"] = objetivo
    
    st.markdown("---")
    
    st.subheader("📋 Recomendações Inteligentes de Coberturas")
    
    bioma = st.session_state["cobertura"]["bioma"]
    
    if bioma:
        recomendacoes = recomendar_coberturas_inteligentes(
            objetivo, bioma, periodo_seco, regiao
        )
        
        st.success(f"✅ {len(recomendacoes)} recomendações baseadas no bioma **{bioma}**")
        
        for i, rec in enumerate(recomendacoes):
            st.markdown(f"""
            <div style='
                background-color: {"#e8f5e9" if i==0 else "#f5f5f5"};
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
                border-left: 5px solid {"#2e7d32" if i==0 else "#999"};
            '>
                <h3>{'⭐ ' if i==0 else ''}🌱 {rec['especie']}</h3>
                <p><b>Biomassa:</b> {rec['biomassa']} t/ha</p>
                <p><b>Persistência:</b> {rec['persistencia']}</p>
                <p><b>Carbono:</b> {rec['carbono']} t/ha</p>
                <p><b>Relação C/N:</b> {rec['relacao_cn']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.session_state["cobertura"]["recomendacoes"] = [rec["especie"] for rec in recomendacoes]
        
        with st.expander("📖 Detalhes das espécies recomendadas"):
            for rec in recomendacoes:
                especie = rec["especie"]
                if especie in BANCO_ESPECIES:
                    dados = BANCO_ESPECIES[especie]
                    st.markdown(f"""
                    **{especie}**
                    - Produção de biomassa: {dados['biomassa_min']}-{dados['biomassa_max']} t/ha
                    - Persistência: {dados['persistencia']}
                    - Incremento de carbono: {dados['carbono_incremento']} t/ha
                    - Relação C/N: {dados['relacao_cn']}
                    - Lignina: {dados['lignina']}%
                    - Adaptação: {', '.join(dados['adaptacao'])}
                    """)
    else:
        st.warning("⚠️ Selecione um bioma para obter recomendações")


def render_consorcio():
    """Renderiza a página de consórcios inteligentes"""
    
    st.title("🌾 Consórcios Inteligentes")
    st.markdown("---")
    
    init_session_state()
    
    st.subheader("🤝 Escolha a Cultura Principal")
    
    culturas = ["Soja", "Milho", "Algodão", "Feijão"]
    
    cultura_principal = st.selectbox(
        "Selecione a cultura principal",
        culturas,
        index=culturas.index(st.session_state["consorcio"]["cultura_principal"]) 
        if st.session_state["consorcio"]["cultura_principal"] in culturas else 0,
        key="con_cultura"
    )
    
    st.session_state["consorcio"]["cultura_principal"] = cultura_principal
    
    st.markdown("---")
    
    st.subheader("📋 Consórcios Recomendados")
    
    consorcios = recomendar_consorcios(cultura_principal)
    st.session_state["consorcio"]["consorcios"] = consorcios
    
    for i, consorcio in enumerate(consorcios, 1):
        with st.expander(f"Consórcio {i}: {consorcio['nome']}", expanded=i==1):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Benefícios:**")
                for beneficio in consorcio["beneficios"]:
                    st.markdown(f"✅ {beneficio}")
            
            with col2:
                st.metric(
                    label="Impacto produtivo estimado",
                    value=consorcio["impacto"],
                    delta="Perda estimada" if "-" in consorcio["impacto"] else "Ganho estimado"
                )
                st.caption("Valor estimado: 4 ± 3% depende do clima, fertilidade e manejo")
    
    st.markdown("---")
    
    with st.expander("💡 Dicas para consórcios bem-sucedidos"):
        st.markdown("""
        **1. Escolha da espécie de cobertura:**
        - Considere o ciclo da cultura principal
        - Avalie a competição por água e nutrientes
        - Escolha espécies com sistema radicular complementar
        
        **2. Época de semeadura:**
        - Antecedência de 10-15 dias antes da cultura principal
        - Ou semeadura simultânea em áreas com boa umidade
        
        **3. Manejo da cobertura:**
        - Manejo químico (dessecação) 7-14 dias antes do plantio
        - Roçada mecânica em áreas com alta biomassa
        
        **4. Nutrição:**
        - Ajustar adubação para suprir ambas as culturas
        - Fósforo e potássio são especialmente importantes
        """)


def render_decomposicao():
    """Renderiza a página de simulador de decomposição"""
    
    st.title("📊 Simulador de Decomposição")
    st.markdown("---")
    
    init_session_state()
    
    st.subheader("⚙️ Parâmetros da Simulação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        coberturas = list(BANCO_ESPECIES.keys())
        
        cobertura = st.selectbox(
            "Tipo de Cobertura",
            coberturas,
            index=coberturas.index(st.session_state["decomposicao"]["cobertura"]) 
            if st.session_state["decomposicao"]["cobertura"] in coberturas else 0,
            key="dec_cobertura"
        )
        
        st.session_state["decomposicao"]["cobertura"] = cobertura
    
    with col2:
        massa_seca = st.number_input(
            "Quantidade de Massa Seca (t/ha)",
            min_value=1.0,
            max_value=30.0,
            value=st.session_state["decomposicao"]["massa_seca"],
            step=0.5,
            key="dec_massa"
        )
        
        st.session_state["decomposicao"]["massa_seca"] = massa_seca
    
    st.markdown("---")
    
    if st.button("📈 SIMULAR DECOMPOSIÇÃO", use_container_width=True, type="primary"):
        with st.spinner("Simulando decomposição..."):
            # Obtém fatores climáticos do manejo
            temp = st.session_state["manejo"].get("temperatura_media", 25.0)
            prec = st.session_state["manejo"].get("precipitacao", 1500.0)
            argila = st.session_state["manejo"].get("argila", 30.0)
            
            df = simular_decomposicao(cobertura, massa_seca, temp, prec, argila)
            st.session_state["decomposicao"]["dados_simulacao"] = df
            st.success("✅ Simulação concluída!")
    
    if st.session_state["decomposicao"]["dados_simulacao"] is not None:
        df = st.session_state["decomposicao"]["dados_simulacao"]
        
        st.subheader("📋 Dados da Simulação")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.subheader("📈 Evolução da Decomposição")
        
        fig = criar_grafico_decomposicao(df)
        st.pyplot(fig)
        plt.close(fig)
        
        st.subheader("📊 Resumo da Simulação")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Decomposição em 90 dias",
                f"{df[df['Dias'] == 90]['Decomposição (%)'].iloc[0]:.1f}%"
            )
        
        with col2:
            st.metric(
                "Carbono residual em 180 dias",
                f"{df[df['Dias'] == 180]['Carbono (t/ha)'].iloc[0]:.2f} t/ha"
            )
        
        with col3:
            st.metric(
                "MO adicionada em 180 dias",
                f"{df[df['Dias'] == 180]['Matéria Orgânica (t/ha)'].iloc[0]:.2f} t/ha"
            )
        
        # Botão de exportar Excel
        st.markdown("---")
        excel_data = download_excel(df)
        st.download_button(
            label="📊 Exportar para Excel",
            data=excel_data,
            file_name=f"decomposicao_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="secondary"
        )


def render_relatorio():
    """Renderiza a página de relatório"""
    
    st.title("📄 Relatório Técnico")
    st.markdown("---")
    
    init_session_state()
    
    if st.button("🔄 GERAR RELATÓRIO", use_container_width=True, type="primary"):
        st.session_state["relatorio"]["gerado"] = True
        st.success("✅ Relatório gerado com sucesso!")
    
    if st.session_state["relatorio"]["gerado"]:
        st.markdown("---")
        
        st.markdown(f"""
        <div style='
            background-color: #1f4b3a;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        '>
            <h1 style='color: white;'>🌱 SoilCarbon Planner</h1>
            <h3 style='color: white;'>Sistema Inteligente de Coberturas Vegetais</h3>
            <p style='color: #c8e6c9;'>Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🏢 Resumo da Propriedade", expanded=True):
            cad = st.session_state["cadastro"]
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Fazenda:** {cad['fazenda']}")
                st.markdown(f"**Município:** {cad['municipio']}")
                st.markdown(f"**Estado:** {cad['estado']}")
            
            with col2:
                st.markdown(f"**Área Total:** {cad['area_total']:.1f} ha")
                st.markdown(f"**Latitude:** {cad['latitude']:.4f}")
                st.markdown(f"**Longitude:** {cad['longitude']:.4f}")
        
        with st.expander("🔬 Diagnóstico de Manejo", expanded=True):
            man = st.session_state["manejo"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Tipo de Manejo:** {man['tipo']}")
                st.markdown(f"**Anos em Plantio Direto:** {man['anos']}")
                st.markdown(f"**Culturas:** {', '.join(man['culturas'])}")
            
            with col2:
                st.markdown(f"**Matéria Orgânica:** {man['materia_organica']:.1f}%")
                st.markdown(f"**Argila:** {man['argila']:.1f}%")
                st.markdown(f"**pH:** {man['ph']:.1f}")
                st.markdown(f"**CTC:** {man['ctc']:.1f} meq/100g")
                st.markdown(f"**Temperatura:** {man.get('temperatura_media', 25):.1f}°C")
                st.markdown(f"**Precipitação:** {man.get('precipitacao', 1500):.0f} mm")
        
        with st.expander("🌿 Coberturas Recomendadas", expanded=True):
            cov = st.session_state["cobertura"]
            
            st.markdown(f"**Objetivo:** {cov['objetivo']}")
            st.markdown(f"**Bioma:** {cov['bioma']}")
            st.markdown(f"**Período seco:** {cov.get('periodo_seco', 90)} dias")
            
            if cov['recomendacoes']:
                st.markdown("**Recomendações:**")
                for rec in cov['recomendacoes']:
                    st.markdown(f"✅ {rec}")
        
        with st.expander("🌾 Consórcios Recomendados", expanded=True):
            con = st.session_state["consorcio"]
            
            st.markdown(f"**Cultura Principal:** {con['cultura_principal']}")
            
            if con['consorcios']:
                for i, consorcio in enumerate(con['consorcios'], 1):
                    st.markdown(f"**{i}. {consorcio['nome']}**")
                    st.markdown(f"   Benefícios: {', '.join(consorcio['beneficios'])}")
                    st.markdown(f"   Impacto: {consorcio['impacto']}")
        
        with st.expander("📊 Simulação de Decomposição", expanded=True):
            dec = st.session_state["decomposicao"]
            
            if dec['dados_simulacao'] is not None:
                df = dec['dados_simulacao']
                
                st.markdown(f"**Cobertura:** {dec['cobertura']}")
                st.markdown(f"**Massa Seca Inicial:** {dec['massa_seca']:.1f} t/ha")
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhuma simulação realizada")
        
        st.markdown("---")
        
        st.info("✅ Relatório completo gerado com sucesso!")
    else:
        st.info("📌 Clique em 'GERAR RELATÓRIO' para visualizar o relatório completo")


# ============================================================================
# MAIN - APLICAÇÃO PRINCIPAL
# ============================================================================

# Cabeçalho
st.markdown("""
<div class="main-header">
    <h1>🌱 SoilCarbon Planner</h1>
    <p>Sistema Inteligente de Coberturas Vegetais e Incremento de Matéria Orgânica do Solo</p>
</div>
""", unsafe_allow_html=True)

# Inicializa session_state
init_session_state()

# Barra lateral
st.sidebar.title("📋 Navegação")

aba = st.sidebar.radio(
    "Selecione uma seção:",
    [
        "📝 Cadastro",
        "🔬 Manejo",
        "🌿 Coberturas",
        "🌾 Consórcios",
        "📊 Decomposição",
        "📄 Relatório"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Desenvolvido para Agronomia**

Este sistema auxilia no planejamento de 
coberturas vegetais e manejo da matéria 
orgânica do solo.
""")

st.sidebar.markdown("---")

if st.session_state["cadastro"]["nome"]:
    st.sidebar.success(f"👤 {st.session_state['cadastro']['nome']}")
    st.sidebar.caption(f"🏢 {st.session_state['cadastro']['fazenda']}")

# Roteamento das abas
if aba == "📝 Cadastro":
    render_cadastro()
elif aba == "🔬 Manejo":
    render_manejo()
elif aba == "🌿 Coberturas":
    render_cobertura()
elif aba == "🌾 Consórcios":
    render_consorcio()
elif aba == "📊 Decomposição":
    render_decomposicao()
elif aba == "📄 Relatório":
    render_relatorio()

# Rodapé
st.markdown("---")
st.caption("🌱 SoilCarbon Planner v1.0 | Desenvolvido para Disciplina de Agronomia")
