import os
import re
import requests
import pandas as pd
from typing import Optional, List, Dict

from dcaf_tools.transform_col_names import aid_to_dcaf

# ==============================================================================
# FUNÇÕES PRINCIPAIS
# ==============================================================================

def extract_base_aid(
    repo_aid: Optional[str] = None, base_dcaf: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """Busca as bases de repositórios da AID, extraindo-as e transformando-as em DataFrame nos mesmos padrões de nomes de colunas e fórmulas da DCAF."""
    repos_validos = ["dados-armazem-siafi-2026", "dados-armazem-siafi-2025"]

    if repo_aid is not None and base_dcaf is not None:
        if repo_aid not in repos_validos:
            raise ValueError(
                "Erro: O repositório especificado não é válido. "
                "Escolha entre 'dados-armazem-siafi-2026' ou 'dados-armazem-siafi-2025'."
            )
        if base_dcaf not in MAPEAMENTO_AID_DCAF:
            raise ValueError("Erro: A base especificada não é válida.")

    elif repo_aid is None and base_dcaf is None:
        # Perguntar qual repositório
        for i, repo in enumerate(repos_validos, start=1):
            print(f"{i} . {repo}")
        idx_repo = int(input("Digite o número do repositório desejado: ")) - 1
        repo_aid = repos_validos[idx_repo]

        # Listar bases do repositório selecionado e perguntar qual base deseja extrair
        bases_dcaf = list(MAPEAMENTO_AID_DCAF.keys())
        for i, b in enumerate(bases_dcaf, start=1):
            print(f"{i} . {b}")
        idx_base = int(input("Digite o número da base que deseja extrair: ")) - 1
        base_dcaf = bases_dcaf[idx_base]

    # Extrair a base selecionada
    resource = MAPEAMENTO_AID_DCAF[base_dcaf]
    token = os.getenv("GITHUB_SPLOR_PAT", "")

    try:
        base = get_resource(repo_aid, resource, token=token)
    except Exception as e:
        print(f"\n[Erro]: {e}")
        return None

    # Transformar a base
    base = aid_to_dcaf(base)
    base = filtrar_colunas(base, nome_base=base_dcaf)
    base = agrupar_colunas(base, nome_base=base_dcaf)
    base = gerar_elemento_item(base)

    # Colunas exec_rp com fórmulas: VL_OLP_RPNP, VL_PAGO_RPP_DEMAIS, VL_CANCELADO_RPP_DEMAIS
    if base_dcaf == "exec_rp":
        base["VL_OLP_RPNP"] = base["VL_DESP_LIQ_PAGAR"] - base["VL_OLP_RPP_DEMAIS"]

        base["VL_PAGO_RPP_DEMAIS"] = (
            base["VL_PAGO_RPP"]
            - base["VL_ANULACAO_PAGAMENTO_RPP"]
            + base["VL_RETENCAO_RPP"]
            - base["VL_ANULACAO_RETENCAO_RPP"]
        )

        base["VL_CANCELADO_RPP_DEMAIS"] = (
            base["VL_CANCELADO_RPP"]
            + base["VL_DESCONTO_RPP"]
            - base["VL_RESTABELECIDO_RPP"]
        )

        colunas_finais_rp = [
            "ANO", "MES_COD", "ANO_ORIGEM_RP", "UO_COD", "FUNCAO_COD", "ACAO_COD", "GRUPO_COD",
            "MODALIDADE_COD", "IAG_COD", "FONTE_COD", "IPU_COD", "ELEMENTO_COD", "ITEM_COD", "ELEMENTO_ITEM_COD",
            "VL_INSCRITO_RPNP", "VL_LIQ_RPNP", "VL_PAGO_RPNP", "VL_CANCELADO_RPNP", "VL_OLP_RPNP", "VL_SALDO_RPNP",
            "VL_INSCRITO_RPP_DEMAIS", "VL_PAGO_RPP_DEMAIS", "VL_CANCELADO_RPP_DEMAIS", "VL_OLP_RPP_DEMAIS",
        ]
        base = base[colunas_finais_rp]

    return base


def list_resources_aid() -> List[str]:
    """Lista os recursos (.csv.gz) disponíveis nos repositórios da AID."""
    repos = ["dados-armazem-siafi-2026", "dados-armazem-siafi-2025"]

    for i, repo in enumerate(repos, start=1):
        print(f"{i} . {repo}")
    idx_repo = int(input("Digite o número do repositório desejado: ")) - 1
    repo = repos[idx_repo]

    token = os.getenv("GITHUB_SPLOR_PAT", "")
    url = f"https://api.github.com/repos/splor-mg/{repo}/contents/data"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    files = resp.json()
    return [
        re.sub(r"\.csv\.gz$", "", f["name"])
        for f in files
        if f["name"].endswith(".csv.gz")
    ]

# ==============================================================================
# FUNÇÕES AUXILIARES PARA EXTRAÇÃO DAS BASES
# ==============================================================================

def get_resource(repo: str, resource: str, token: str) -> pd.DataFrame:
    """Baixa o arquivo .csv.gz do repositório privado/público no GitHub e lê como DataFrame."""
    url = f"https://api.github.com/repos/splor-mg/{repo}/contents/data/{resource}.csv.gz"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    download_url = resp.json()["download_url"]
    # O pandas detecta automaticamente a compressão gzip pela extensão .gz na URL
    return pd.read_csv(download_url)


# ==============================================================================
# FUNÇÕES AUXILIARES PARA TRANSFORMAÇÃO DAS BASES DA AID PARA O FORMATO DCAF
# ==============================================================================

def filtrar_colunas(
    base: pd.DataFrame,
    nome_base: str,
    dicionario: Optional[Dict[str, List[str]]] = None,
) -> pd.DataFrame:
    """Seleciona apenas as colunas especificadas para a base."""
    if dicionario is None:
        dicionario = DICIONARIO_FILTER
    if nome_base not in dicionario:
        raise ValueError(f"Erro: O nome_base '{nome_base}' não foi encontrado no dicionário.")

    colunas_desejadas = dicionario[nome_base]
    return base[colunas_desejadas].copy()


def agrupar_colunas(
    base: pd.DataFrame,
    nome_base: str,
    dicionario: Optional[Dict[str, List[str]]] = None,
) -> pd.DataFrame:
    """Agrupa pelas colunas-chave e soma todas as colunas numéricas."""
    if dicionario is None:
        dicionario = DICIONARIO_GROUPBY
    if nome_base not in dicionario:
        raise ValueError(f"Erro: O nome_base '{nome_base}' não foi encontrado no dicionário.")

    colunas_grupo = dicionario[nome_base]
    colunas_nao_presentes = [col for col in colunas_grupo if col not in base.columns]

    if colunas_nao_presentes:
        colunas_faltantes_str = ", ".join(colunas_nao_presentes)
        print(
            "Aviso: Algumas colunas não foram encontradas na base. "
            "Não foi possível realizar o agrupamento correto. Retornando a base sem alterações.\n"
            f"Colunas ausentes: {colunas_faltantes_str}"
        )
        return base

    # Identifica colunas numéricas que não fazem parte do agrupamento
    colunas_numericas = [
        col for col in base.select_dtypes(include="number").columns if col not in colunas_grupo
    ]

    # dropna=False garante comportamento idêntico ao dplyr::group_by (não descarta NAs nas chaves)
    base_agrupada = (
        base.groupby(colunas_grupo, as_index=False, dropna=False)[colunas_numericas]
        .sum()
    )
    return base_agrupada


def gerar_elemento_item(base: pd.DataFrame) -> pd.DataFrame:
    """Extrai ELEMENTO_COD e ITEM_COD a partir de ELEMENTO_ITEM_COD caso não existam."""
    colunas = ["ELEMENTO_COD", "ITEM_COD"]

    if any(col not in base.columns for col in colunas) and ("ELEMENTO_ITEM_COD" in base.columns):
        # Converte para string garantindo preservação de zeros à esquerda, se aplicável
        elem_item_str = base["ELEMENTO_ITEM_COD"].astype(str)
        base["ELEMENTO_COD"] = elem_item_str.str[:-2]
        base["ITEM_COD"] = elem_item_str.str[-2:]

    return base


# ==============================================================================
# DICIONÁRIOS E MAPEAMENTOS
# ==============================================================================

MAPEAMENTO_AID_DCAF: Dict[str, str] = {
    "exec_alem_credito": "execucao_alem_credito",
    "exec_cota": "cota",
    "exec_cred_aut_desp": "credito",
    "exec_desp": "execucao",
    "exec_rec": "receita",
    "exec_rp": "restos_pagar",
    "exec_rp_folha": "restos_pagar_folha",
    "exec_suplementacao": "alteracoes_orcamentarias",
    "exec_pago_orc": "execucao",
}

DICIONARIO_FILTER: Dict[str, List[str]] = {
    "exec_alem_credito": [
        "ANO", "MES_COD", "MES_REGULARIZACAO", "MES_REGISTRO", "UO_COD", "GRUPO_COD",
        "IAG_COD", "FONTE_COD", "IPU_COD", "MODALIDADE_COD", "FUNCAO_COD",
        "ACAO_COD", "ELEMENTO_ITEM_COD", "ALEM_CRED", "REGULARIZADO", "ANULADO",
    ],
    "exec_cota": [
        "ANO", "UO_COD", "ACAO_COD", "GRUPO_COD", "IAG_COD", "FONTE_COD",
        "IPU_COD", "VL_COTA_APROVADA",
    ],
    "exec_cred_aut_desp": [
        "ANO", "UO_COD", "ACAO_COD", "FUNCAO_COD", "GRUPO_COD",
        "IAG_COD", "FONTE_COD", "IPU_COD", "MODALIDADE_COD", "VL_CRED_AUT", "VL_COTA_DESCENTRALIZADA",
    ],
    "exec_desp": [
        "ANO", "MES_COD", "UO_COD", "UO_FIN_COD", "FUNCAO_COD", "SUBFUNCAO_COD",
        "PROGRAMA_COD", "ACAO_COD", "GRUPO_COD", "MODALIDADE_COD",
        "ELEMENTO_ITEM_COD", "IAG_COD", "FONTE_COD", "IPU_COD", "VL_EMP", "VL_LIQ", "VL_PAGO_FIN",
    ],
    "exec_pago_orc": [
        "ANO", "UO_COD", "UO_FIN_COD", "FUNCAO_COD", "SUBFUNCAO_COD", "PROGRAMA_COD", "ACAO_COD",
        "GRUPO_COD", "MODALIDADE_COD", "ELEMENTO_ITEM_COD", "IAG_COD", "FONTE_COD", "IPU_COD", "VL_PAGO_ORC",
    ],
    "exec_rec": [
        "ANO", "MES_COD", "UO_COD", "FONTE_COD", "RECEITA_COD", "VL_EFET_AJUST",
    ],
    "exec_rp": [
        "ANO", "MES_COD", "ANO_ORIGEM_RP", "UO_COD", "FUNCAO_COD", "ACAO_COD",
        "GRUPO_COD", "MODALIDADE_COD", "IAG_COD", "FONTE_COD", "IPU_COD", "ELEMENTO_ITEM_COD",
        "VL_INSCRITO_RPNP", "VL_LIQ_RPNP", "VL_PAGO_RPNP", "VL_CANCELADO_RPNP", "VL_SALDO_RPNP",
        "VL_INSCRITO_RPP_DEMAIS", "VL_DESP_LIQ_PAGAR", "VL_OLP_RPP_DEMAIS", "VL_PAGO_RPP",
        "VL_ANULACAO_PAGAMENTO_RPP", "VL_RETENCAO_RPP", "VL_ANULACAO_RETENCAO_RPP", "VL_CANCELADO_RPP",
        "VL_DESCONTO_RPP", "VL_RESTABELECIDO_RPP",
    ],
    "exec_rp_folha": [
        "ANO", "MES_COD", "ANO_ORIGEM_RP", "UO_COD", "GRUPO_COD", "MODALIDADE_COD",
        "IAG_COD", "FONTE_COD", "IPU_COD", "VL_INSCRITO_RPP_FOLHA", "VL_PAGO_RPP_FOLHA",
        "VL_CANCELADO_RPP_FOLHA", "VL_OLP_RPP_FOLHA",
    ],
    "exec_suplementacao": [
        "ANO", "MES_COD", "UO_COD", "FUNCAO_COD", "ACAO_COD", "GRUPO_COD",
        "MODALIDADE_COD", "IAG_COD", "FONTE_COD", "IPU_COD", "DECRETO", "PUBLICACAO_DECRETO",
        "CRED_ADIC_COD", "CRED_ADIC_DESC", "VL_CRED_INICIAL", "VL_SUPLEMENTACAO", "VL_ANULACAO",
    ],
}

DICIONARIO_GROUPBY: Dict[str, List[str]] = {
    "exec_alem_credito": [
        "ANO", "MES_COD", "MES_REGULARIZACAO", "MES_REGISTRO", "UO_COD", "GRUPO_COD",
        "IAG_COD", "FONTE_COD", "IPU_COD", "MODALIDADE_COD", "FUNCAO_COD",
        "ACAO_COD", "ELEMENTO_ITEM_COD",
    ],
    "exec_cota": [
        "ANO", "UO_COD", "ACAO_COD", "GRUPO_COD", "IAG_COD", "FONTE_COD", "IPU_COD",
    ],
    "exec_cred_aut_desp": [
        "ANO", "UO_COD", "ACAO_COD", "FUNCAO_COD", "GRUPO_COD",
        "IAG_COD", "FONTE_COD", "IPU_COD", "MODALIDADE_COD",
    ],
    "exec_desp": [
        "ANO", "MES_COD", "UO_COD", "UO_FIN_COD", "FUNCAO_COD", "SUBFUNCAO_COD",
        "PROGRAMA_COD", "ACAO_COD", "GRUPO_COD", "MODALIDADE_COD",
        "ELEMENTO_ITEM_COD", "IAG_COD", "FONTE_COD", "IPU_COD",
    ],
    "exec_pago_orc": [
        "ANO", "UO_COD", "UO_FIN_COD", "FUNCAO_COD", "SUBFUNCAO_COD", "PROGRAMA_COD", "ACAO_COD",
        "GRUPO_COD", "MODALIDADE_COD", "ELEMENTO_ITEM_COD", "IAG_COD", "FONTE_COD", "IPU_COD",
    ],
    "exec_rec": [
        "ANO", "MES_COD", "UO_COD", "FONTE_COD", "RECEITA_COD",
    ],
    "exec_rp": [
        "ANO", "MES_COD", "ANO_ORIGEM_RP", "UO_COD", "FUNCAO_COD", "ACAO_COD",
        "GRUPO_COD", "MODALIDADE_COD", "IAG_COD", "FONTE_COD", "IPU_COD", "ELEMENTO_ITEM_COD",
    ],
    "exec_rp_folha": [
        "ANO", "MES_COD", "ANO_ORIGEM_RP", "UO_COD", "GRUPO_COD", "MODALIDADE_COD",
        "IAG_COD", "FONTE_COD", "IPU_COD",
    ],
    "exec_suplementacao": [
        "ANO", "MES_COD", "UO_COD", "FUNCAO_COD", "ACAO_COD", "GRUPO_COD",
        "MODALIDADE_COD", "IAG_COD", "FONTE_COD", "IPU_COD", "DECRETO", "PUBLICACAO_DECRETO",
        "CRED_ADIC_COD", "CRED_ADIC_DESC",
    ],
}
