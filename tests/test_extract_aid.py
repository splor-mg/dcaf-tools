from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests

from dcaf_tools import extract_aid
from dcaf_tools.extract_aid import (
    agrupar_colunas,
    extract_base_aid,
    filtrar_colunas,
    gerar_elemento_item,
    get_resource,
    list_resources_aid,
)

_REPOS = (
    'dados-armazem-siafi-2026',
    'dados-armazem-siafi-2025',
)


def _entradas(monkeypatch, *valores: str) -> None:
    fila = iter(valores)

    def responder(_prompt: str) -> str:
        return next(fila)

    monkeypatch.setattr('builtins.input', responder)


def _recusa_entrada(_prompt: str) -> str:
    pytest.fail('não deveria solicitar entrada')


def _substitui_download(monkeypatch, df: pd.DataFrame) -> list:
    chamadas = []

    def fake_get(repo, resource, token):
        chamadas.append((repo, resource, token))
        return df.copy()

    monkeypatch.setattr(extract_aid, 'get_resource', fake_get)
    return chamadas


def _quadro_cota() -> pd.DataFrame:
    return pd.DataFrame({
        'ano': [2026, 2026],
        'uo_cod': [1, 1],
        'acao_cod': [10, 10],
        'grupo_cod': [3, 3],
        'iag_cod': [1, 1],
        'fonte_cod': [100, 100],
        'ipu_cod': [0, 0],
        'vlr_cota_aprovada_liquida': [5.0, 2.5],
        'extra': ['a', 'b'],
    })


def _esperado_cota() -> pd.DataFrame:
    return pd.DataFrame({
        'ANO': [2026],
        'UO_COD': [1],
        'ACAO_COD': [10],
        'GRUPO_COD': [3],
        'IAG_COD': [1],
        'FONTE_COD': [100],
        'IPU_COD': [0],
        'VL_COTA_APROVADA': [7.5],
    })


def _quadro_exec_desp() -> pd.DataFrame:
    comum = {
        'ano': 2026,
        'mes_cod': 4,
        'uo_fin_cod': 101,
        'funcao_cod': 10,
        'subfuncao_cod': 122,
        'programa_cod': 200,
        'acao_cod': 3000,
        'grupo_cod': 3,
        'modalidade_cod': 90,
        'elemento_item_cod': '339014',
        'iag_cod': 1,
        'fonte_cod': 1500,
        'ipu_cod': 0,
        'coluna_extra': 'ignorar',
    }
    return pd.DataFrame([
        {
            **comum,
            'uo_cod': 101,
            'vlr_empenhado': 10,
            'vlr_liquidado': 4,
            'vlr_pago_financeiro': 2,
        },
        {
            **comum,
            'uo_cod': 50,
            'vlr_empenhado': 3,
            'vlr_liquidado': 1,
            'vlr_pago_financeiro': 1,
        },
        {
            **comum,
            'uo_cod': 101,
            'vlr_empenhado': 5,
            'vlr_liquidado': 1,
            'vlr_pago_financeiro': 2,
        },
    ])


def _esperado_exec_desp() -> pd.DataFrame:
    colunas = [
        'ANO',
        'MES_COD',
        'UO_COD',
        'UO_FIN_COD',
        'FUNCAO_COD',
        'SUBFUNCAO_COD',
        'PROGRAMA_COD',
        'ACAO_COD',
        'GRUPO_COD',
        'MODALIDADE_COD',
        'ELEMENTO_ITEM_COD',
        'IAG_COD',
        'FONTE_COD',
        'IPU_COD',
        'VL_EMP',
        'VL_LIQ',
        'VL_PAGO_FIN',
        'ELEMENTO_COD',
        'ITEM_COD',
    ]
    linhas = [
        [
            2026,
            4,
            50,
            101,
            10,
            122,
            200,
            3000,
            3,
            90,
            '339014',
            1,
            1500,
            0,
            3,
            1,
            1,
            '3390',
            '14',
        ],
        [
            2026,
            4,
            101,
            101,
            10,
            122,
            200,
            3000,
            3,
            90,
            '339014',
            1,
            1500,
            0,
            15,
            5,
            4,
            '3390',
            '14',
        ],
    ]
    return pd.DataFrame(linhas, columns=colunas)


def _quadro_exec_rp() -> pd.DataFrame:
    chaves = {
        'ano': 2026,
        'mes_cod': 3,
        'ano_rp': 2024,
        'uo_cod': 1234,
        'funcao_cod': 10,
        'acao_cod': 2000,
        'grupo_cod': 3,
        'modalidade_cod': 90,
        'iag_cod': 1,
        'fonte_cod': 1500,
        'ipu_cod': 0,
        'elemento_item_cod': '339014',
    }
    valores_a = {
        'vlr_inscrito_rpnp': 10,
        'vlr_despesa_liquidada_rpnp': 8,
        'vlr_pago_rpnp': 5,
        'vlr_cancelado_rpnp': 1,
        'vlr_saldo_rpnp': 4,
        'vlr_inscrito_rpp': 7,
        'vlr_despesa_liquidada_pagar': 10,
        'vlr_saldo_rpp': 3,
        'vlr_pago_rpp': 20,
        'vlr_anulacao_pagamento_rpp': 2,
        'vlr_retencao_rpp': 4,
        'vlr_anulacao_retencao_rpp': 1,
        'vlr_cancelado_rpp': 8,
        'vlr_desconto_rpp': 1,
        'vlr_restabelecido_rpp': 3,
    }
    valores_b = {
        'vlr_inscrito_rpnp': 1,
        'vlr_despesa_liquidada_rpnp': 2,
        'vlr_pago_rpnp': 1,
        'vlr_cancelado_rpnp': 1,
        'vlr_saldo_rpnp': 0,
        'vlr_inscrito_rpp': 3,
        'vlr_despesa_liquidada_pagar': 5,
        'vlr_saldo_rpp': 1,
        'vlr_pago_rpp': 4,
        'vlr_anulacao_pagamento_rpp': 1,
        'vlr_retencao_rpp': 1,
        'vlr_anulacao_retencao_rpp': 0,
        'vlr_cancelado_rpp': 2,
        'vlr_desconto_rpp': 1,
        'vlr_restabelecido_rpp': 1,
    }
    return pd.DataFrame([{**chaves, **valores_a}, {**chaves, **valores_b}])


def _esperado_exec_rp() -> pd.DataFrame:
    # Somas das duas linhas e, depois, as fórmulas de restos a pagar:
    # VL_OLP_RPNP = 15 - 4
    # VL_PAGO_RPP_DEMAIS = 24 - 3 + 5 - 1
    # VL_CANCELADO_RPP_DEMAIS = 10 + 2 - 4
    colunas = [
        'ANO',
        'MES_COD',
        'ANO_ORIGEM_RP',
        'UO_COD',
        'FUNCAO_COD',
        'ACAO_COD',
        'GRUPO_COD',
        'MODALIDADE_COD',
        'IAG_COD',
        'FONTE_COD',
        'IPU_COD',
        'ELEMENTO_COD',
        'ITEM_COD',
        'ELEMENTO_ITEM_COD',
        'VL_INSCRITO_RPNP',
        'VL_LIQ_RPNP',
        'VL_PAGO_RPNP',
        'VL_CANCELADO_RPNP',
        'VL_OLP_RPNP',
        'VL_SALDO_RPNP',
        'VL_INSCRITO_RPP_DEMAIS',
        'VL_PAGO_RPP_DEMAIS',
        'VL_CANCELADO_RPP_DEMAIS',
        'VL_OLP_RPP_DEMAIS',
    ]
    valores = [
        2026,
        3,
        2024,
        1234,
        10,
        2000,
        3,
        90,
        1,
        1500,
        0,
        '3390',
        '14',
        '339014',
        11,
        10,
        6,
        2,
        11,
        4,
        10,
        25,
        8,
        4,
    ]
    return pd.DataFrame([valores], columns=colunas)


def _resposta_github(payload) -> MagicMock:
    resposta = MagicMock()
    resposta.raise_for_status.return_value = None
    resposta.json.return_value = payload
    return resposta


def test_filtrar_colunas_seleciona_copia():
    base = pd.DataFrame({
        'ANO': [2026],
        'UO_COD': [1],
        'ACAO_COD': [10],
        'GRUPO_COD': [3],
        'IAG_COD': [1],
        'FONTE_COD': [100],
        'IPU_COD': [0],
        'VL_COTA_APROVADA': [5],
        'EXTRA': [9],
    })

    ano_original = base['ANO'].copy()
    resultado = filtrar_colunas(base, 'exec_cota')
    resultado.loc[0, 'ANO'] = 0

    assert list(resultado.columns) == [
        'ANO',
        'UO_COD',
        'ACAO_COD',
        'GRUPO_COD',
        'IAG_COD',
        'FONTE_COD',
        'IPU_COD',
        'VL_COTA_APROVADA',
    ]
    pd.testing.assert_series_equal(base['ANO'], ano_original)
    assert 'EXTRA' not in resultado.columns


def test_filtrar_colunas_usa_dicionario_informado():
    base = pd.DataFrame({'A': [1], 'B': [2]})

    resultado = filtrar_colunas(base, 'parcial', dicionario={'parcial': ['B']})

    pd.testing.assert_frame_equal(resultado, base[['B']])


def test_filtrar_colunas_exige_colunas_do_dicionario():
    base = pd.DataFrame({'ANO': [2026]})

    with pytest.raises(KeyError, match='UO_COD'):
        filtrar_colunas(base, 'exec_cota')


@pytest.mark.parametrize('funcao', [filtrar_colunas, agrupar_colunas])
def test_transformacao_rejeita_base_desconhecida(funcao):
    base = pd.DataFrame({'ANO': [2026]})

    with pytest.raises(ValueError, match='desconhecida'):
        funcao(base, 'desconhecida')


def test_agrupar_colunas_soma_e_descarta_texto():
    base = pd.DataFrame({
        'ANO': [2026, 2026, 2025],
        'UO_COD': [2, 2, 1],
        'ACAO_COD': [10, 10, 10],
        'GRUPO_COD': [3, 3, 3],
        'IAG_COD': [1, 1, 1],
        'FONTE_COD': [100, 100, 100],
        'IPU_COD': [0, 0, 0],
        'VL_COTA_APROVADA': [5, 7, 4],
        'OBS': ['a', 'b', 'c'],
    })
    esperado = pd.DataFrame({
        'ANO': [2025, 2026],
        'UO_COD': [1, 2],
        'ACAO_COD': [10, 10],
        'GRUPO_COD': [3, 3],
        'IAG_COD': [1, 1],
        'FONTE_COD': [100, 100],
        'IPU_COD': [0, 0],
        'VL_COTA_APROVADA': [4, 12],
    })

    resultado = agrupar_colunas(base, 'exec_cota')

    pd.testing.assert_frame_equal(resultado, esperado)


def test_agrupar_colunas_mantem_na_na_chave():
    base = pd.DataFrame({
        'ANO': [2026, 2026, 2026],
        'MES_COD': [1, 1, 2],
        'UO_COD': [float('nan'), float('nan'), 5.0],
        'FONTE_COD': [10, 10, 10],
        'RECEITA_COD': [100, 100, 100],
        'VL_EFET_AJUST': [1.5, 2.5, 4.0],
    })

    esperado = pd.DataFrame({
        'ANO': [2026, 2026],
        'MES_COD': [1, 2],
        'UO_COD': [float('nan'), 5.0],
        'FONTE_COD': [10, 10],
        'RECEITA_COD': [100, 100],
        'VL_EFET_AJUST': [4.0, 4.0],
    })

    resultado = agrupar_colunas(base, 'exec_rec')

    pd.testing.assert_frame_equal(resultado, esperado)


def test_agrupar_colunas_ausentes_devolve_a_base(capsys):
    base = pd.DataFrame({
        'ANO': [2026, 2026],
        'VL_COTA_APROVADA': [1.0, 2.0],
    })

    esperado = base.copy()

    resultado = agrupar_colunas(base, 'exec_cota')

    assert resultado is base
    pd.testing.assert_frame_equal(resultado, esperado)
    saida = capsys.readouterr().out
    assert 'UO_COD' in saida
    assert 'sem alterações' in saida


def test_agrupar_colunas_usa_dicionario_informado():
    base = pd.DataFrame({'K': ['a', 'a'], 'V': [1, 2], 'OBS': ['x', 'y']})
    esperado = pd.DataFrame({'K': ['a'], 'V': [3]})

    resultado = agrupar_colunas(base, 'x', dicionario={'x': ['K']})

    pd.testing.assert_frame_equal(resultado, esperado)


def test_gerar_elemento_item_separa_codigo():
    base = pd.DataFrame({'ELEMENTO_ITEM_COD': ['339014', '010014', 449052]})

    resultado = gerar_elemento_item(base)

    assert resultado is base
    assert resultado['ELEMENTO_COD'].tolist() == ['3390', '0100', '4490']
    assert resultado['ITEM_COD'].tolist() == ['14', '14', '52']


def test_gerar_elemento_item_preserva_colunas_existentes():
    base = pd.DataFrame({
        'ELEMENTO_ITEM_COD': ['339014'],
        'ELEMENTO_COD': ['1111'],
        'ITEM_COD': ['22'],
    })

    gerar_elemento_item(base)

    assert base['ELEMENTO_COD'].tolist() == ['1111']
    assert base['ITEM_COD'].tolist() == ['22']


def test_gerar_elemento_item_recria_se_faltar_uma_coluna():
    base = pd.DataFrame({
        'ELEMENTO_ITEM_COD': ['339014'],
        'ELEMENTO_COD': ['1111'],
    })

    gerar_elemento_item(base)

    assert base['ELEMENTO_COD'].tolist() == ['3390']
    assert base['ITEM_COD'].tolist() == ['14']


def test_gerar_elemento_item_sem_coluna_de_origem():
    base = pd.DataFrame({'ANO': [2026]})

    resultado = gerar_elemento_item(base)

    assert resultado is base
    assert list(base.columns) == ['ANO']


@pytest.mark.parametrize(
    ('token', 'headers'),
    [
        ('', {}),
        ('abc', {'Authorization': 'Bearer abc'}),
    ],
)
def test_get_resource_le_csv_da_url_de_download(monkeypatch, token, headers):
    df = pd.DataFrame({'ano': [2026]})
    resposta = _resposta_github({
        'download_url': 'https://exemplo/execucao.csv.gz'
    })
    get = MagicMock(return_value=resposta)
    read_csv = MagicMock(return_value=df)
    monkeypatch.setattr(extract_aid.requests, 'get', get)
    monkeypatch.setattr(extract_aid.pd, 'read_csv', read_csv)

    resultado = get_resource(_REPOS[0], 'execucao', token)

    pd.testing.assert_frame_equal(resultado, df)
    get.assert_called_once_with(
        'https://api.github.com/repos/splor-mg/'
        'dados-armazem-siafi-2026/contents/data/execucao.csv.gz',
        headers=headers,
    )
    read_csv.assert_called_once_with('https://exemplo/execucao.csv.gz')


def test_get_resource_propaga_erro_http(monkeypatch):
    resposta = MagicMock()
    resposta.raise_for_status.side_effect = requests.HTTPError('403')
    monkeypatch.setattr(
        extract_aid.requests, 'get', MagicMock(return_value=resposta)
    )
    read_csv = MagicMock()
    monkeypatch.setattr(extract_aid.pd, 'read_csv', read_csv)

    with pytest.raises(requests.HTTPError, match='403'):
        get_resource(_REPOS[0], 'execucao', token='')

    read_csv.assert_not_called()


@pytest.mark.parametrize(
    ('escolha', 'repo', 'token', 'headers'),
    [
        (
            '1',
            _REPOS[0],
            'segredo',
            {'Authorization': 'Bearer segredo'},
        ),
        ('2', _REPOS[1], None, {}),
    ],
)
def test_list_resources_aid_lista_apenas_csv_gz(
    monkeypatch, escolha, repo, token, headers
):
    if token is None:
        monkeypatch.delenv('GITHUB_SPLOR_PAT', raising=False)
    else:
        monkeypatch.setenv('GITHUB_SPLOR_PAT', token)
    _entradas(monkeypatch, escolha)
    resposta = _resposta_github([
        {'name': 'receita.csv.gz'},
        {'name': 'leia-me.txt'},
        {'name': 'nota.csv.gz.txt'},
        {'name': 'execucao.csv.gz'},
    ])
    get = MagicMock(return_value=resposta)
    monkeypatch.setattr(extract_aid.requests, 'get', get)

    recursos = list_resources_aid()

    assert recursos == ['receita', 'execucao']
    get.assert_called_once_with(
        f'https://api.github.com/repos/splor-mg/{repo}/contents/data',
        headers=headers,
    )


def test_list_resources_aid_propaga_erro_http(monkeypatch):
    _entradas(monkeypatch, '1')
    resposta = MagicMock()
    resposta.raise_for_status.side_effect = requests.HTTPError('401')
    monkeypatch.setattr(
        extract_aid.requests, 'get', MagicMock(return_value=resposta)
    )

    with pytest.raises(requests.HTTPError, match='401'):
        list_resources_aid()


@pytest.mark.parametrize(
    ('entrada', 'erro', 'mensagem'),
    [
        ('abc', ValueError, 'invalid literal'),
        ('3', IndexError, 'out of range'),
    ],
)
def test_list_resources_aid_rejeita_entrada_invalida(
    monkeypatch, entrada, erro, mensagem
):
    _entradas(monkeypatch, entrada)

    with pytest.raises(erro, match=mensagem):
        list_resources_aid()


@pytest.mark.parametrize(
    ('repo', 'base', 'mensagem'),
    [
        ('outro-repo', 'exec_desp', 'repositório especificado não é válido'),
        (
            _REPOS[1],
            'inexistente',
            'base especificada não é válida',
        ),
    ],
)
def test_extract_base_aid_rejeita_argumentos_invalidos(repo, base, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        extract_base_aid(repo, base)


def test_extract_base_aid_prioriza_erro_de_repositorio():
    with pytest.raises(ValueError, match='repositório'):
        extract_base_aid('outro-repo', 'tambem-invalida')


@pytest.mark.parametrize('repo', _REPOS)
def test_extract_base_aid_transforma_exec_desp(monkeypatch, repo):
    monkeypatch.setenv('GITHUB_SPLOR_PAT', 'pat-teste')
    monkeypatch.setattr('builtins.input', _recusa_entrada)
    chamadas = _substitui_download(monkeypatch, _quadro_exec_desp())

    resultado = extract_base_aid(repo, 'exec_desp')

    assert chamadas == [(repo, 'execucao', 'pat-teste')]
    pd.testing.assert_frame_equal(resultado, _esperado_exec_desp())


def test_extract_base_aid_calcula_formulas_de_restos(monkeypatch):
    monkeypatch.delenv('GITHUB_SPLOR_PAT', raising=False)
    chamadas = _substitui_download(monkeypatch, _quadro_exec_rp())

    resultado = extract_base_aid(_REPOS[0], 'exec_rp')

    assert chamadas == [(_REPOS[0], 'restos_pagar', '')]
    pd.testing.assert_frame_equal(resultado, _esperado_exec_rp())
    assert 'VL_DESP_LIQ_PAGAR' not in resultado.columns
    assert 'VL_PAGO_RPP' not in resultado.columns


def test_extract_base_aid_modo_interativo(monkeypatch):
    monkeypatch.delenv('GITHUB_SPLOR_PAT', raising=False)
    bases = list(extract_aid.MAPEAMENTO_AID_DCAF)
    _entradas(monkeypatch, '1', str(bases.index('exec_cota') + 1))
    chamadas = _substitui_download(monkeypatch, _quadro_cota())

    resultado = extract_base_aid()

    assert chamadas == [(_REPOS[0], 'cota', '')]
    pd.testing.assert_frame_equal(resultado, _esperado_cota())


def test_extract_base_aid_retorna_none_quando_download_falha(
    monkeypatch, capsys
):
    chamadas = []

    def falha(repo, resource, token):
        chamadas.append((repo, resource, token))
        raise ConnectionError('sem rede')

    monkeypatch.delenv('GITHUB_SPLOR_PAT', raising=False)
    monkeypatch.setattr(extract_aid, 'get_resource', falha)

    resultado = extract_base_aid(_REPOS[1], 'exec_rec')

    assert resultado is None
    assert chamadas == [(_REPOS[1], 'receita', '')]
    assert '[Erro]: sem rede' in capsys.readouterr().out


@pytest.mark.parametrize(
    ('entradas', 'erro', 'mensagem'),
    [
        (('abc',), ValueError, 'invalid literal'),
        (('3',), IndexError, 'out of range'),
        (('1', '99'), IndexError, 'out of range'),
    ],
)
def test_extract_base_aid_rejeita_entrada_invalida(
    monkeypatch, entradas, erro, mensagem
):
    _entradas(monkeypatch, *entradas)

    with pytest.raises(erro, match=mensagem):
        extract_base_aid()
