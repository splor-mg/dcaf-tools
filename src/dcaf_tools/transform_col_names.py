import pandas as pd

def aid_to_dcaf(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=DICIONARIO_NAMES_AID_DCAF)
    return df


def dcaf_to_aid(df: pd.DataFrame) -> pd.DataFrame:
    dict_inverso = {valor: chave for chave, valor in DICIONARIO_NAMES_AID_DCAF.items()}
    df = df.rename(columns=dict_inverso)
    return df


DICIONARIO_NAMES_AID_DCAF: dict[str, str] = {
    # Geral
    "ano": "ANO",
    "mes_cod": "MES_COD",
    "uo_cod": "UO_COD",
    "fonte_cod": "FONTE_COD",

    # Além crédito
    "mes_regularizacao": "MES_REGULARIZACAO",
    "mes_registro": "MES_REGISTRO",
    "vlr_alem_credito": "ALEM_CRED",
    "vlr_regularizado": "REGULARIZADO",
    "vlr_anulado": "ANULADO",

    # Despesa
    "uo_fin_cod": "UO_FIN_COD",
    "funcao_cod": "FUNCAO_COD",
    "subfuncao_cod": "SUBFUNCAO_COD",
    "programa_cod": "PROGRAMA_COD",
    "acao_cod": "ACAO_COD",
    "grupo_cod": "GRUPO_COD",
    "modalidade_cod": "MODALIDADE_COD",
    "elemento_item_cod": "ELEMENTO_ITEM_COD",
    "iag_cod": "IAG_COD",
    "ipu_cod": "IPU_COD",
    "vlr_cota_aprovada_liquida": "VL_COTA_APROVADA",
    "vlr_credito_autorizado": "VL_CRED_AUT",
    "vlr_cota_descentralizada": "VL_COTA_DESCENTRALIZADA",
    "vlr_empenhado": "VL_EMP",
    "vlr_liquidado": "VL_LIQ",
    "vlr_pago_financeiro": "VL_PAGO_FIN",
    "vlr_pago_orcamentario": "VL_PAGO_ORC",

    # Receita
    "receita_cod": "RECEITA_COD",
    "vlr_efetivado_ajustado": "VL_EFET_AJUST",

    # Restos a pagar
    "ano_rp": "ANO_ORIGEM_RP",
    "ano_rp_folha": "ANO_ORIGEM_RP",
    "vlr_inscrito_rpnp": "VL_INSCRITO_RPNP",
    "vlr_despesa_liquidada_rpnp": "VL_LIQ_RPNP",
    "vlr_saldo_rpnp": "VL_SALDO_RPNP",
    "vlr_inscrito_rpp": "VL_INSCRITO_RPP_DEMAIS",
    "vlr_inscrito_folha": "VL_INSCRITO_RPP_FOLHA",
    "vlr_anulado_folha": "VL_CANCELADO_RPP_FOLHA",
    "vlr_pago_folha": "VL_PAGO_RPP_FOLHA",
    "vlr_despesa_liquidada_pagar_folha": "VL_OLP_RPP_FOLHA",
    "vlr_pago_rpnp": "VL_PAGO_RPNP",
    "vlr_cancelado_rpnp": "VL_CANCELADO_RPNP",
    "vlr_despesa_liquidada_pagar": "VL_DESP_LIQ_PAGAR",
    "vlr_saldo_rpp": "VL_OLP_RPP_DEMAIS",
    "vlr_pago_rpp": "VL_PAGO_RPP",
    "vlr_anulacao_pagamento_rpp": "VL_ANULACAO_PAGAMENTO_RPP",
    "vlr_retencao_rpp": "VL_RETENCAO_RPP",
    "vlr_anulacao_retencao_rpp": "VL_ANULACAO_RETENCAO_RPP",
    "vlr_cancelado_rpp": "VL_CANCELADO_RPP",
    "vlr_desconto_rpp": "VL_DESCONTO_RPP",
    "vlr_restabelecido_rpp": "VL_RESTABELECIDO_RPP",

    # Suplementação
    "decreto_num": "DECRETO",
    "data_publicacao": "PUBLICACAO_DECRETO",
    "origem_credito_cod": "CRED_ADIC_COD",
    "origem_credito_desc": "CRED_ADIC_DESC",
    "vlr_credito_inicial": "VL_CRED_INICIAL",
    "vlr_suplementacao": "VL_SUPLEMENTACAO",
    "vlr_anulacao": "VL_ANULACAO",
}





