from pathlib import Path

import pandas as pd
import pytest

from adiciona_desc import adiciona_desc

DATA = Path(__file__).parent / 'data'


@pytest.fixture
def execucao():
    return pd.read_csv(DATA / 'execucao.csv.gz', nrows=200)

@pytest.fixture
def receita():
    return pd.read_csv(DATA / 'receita.csv.gz', nrows=200)


def test_add_funcao_desc(execucao):
    original_order = execucao.columns.tolist()
    sem_desc = execucao.drop(columns =['funcao_desc']).reset_index(drop=True)
    resultado = adiciona_desc(sem_desc, 'funcao_cod')
    pd.testing.assert_frame_equal(resultado[original_order], execucao)

def test_add_lista_desc(execucao):
    original_order = execucao.columns.tolist()
    sem_desc = execucao.drop(columns =['funcao_desc', 'grupo_desc']).reset_index(drop=True)
    resultado = adiciona_desc(sem_desc, ['funcao_cod', 'grupo_cod'])
    pd.testing.assert_frame_equal(resultado[original_order], execucao)


def test_add_receita_desc(receita):
    original_order = receita.columns.tolist()
    sem_desc = receita.drop(columns =['receita_desc']).reset_index(drop=True)
    resultado = adiciona_desc(sem_desc, 'receita_cod')
    pd.testing.assert_frame_equal(resultado[original_order], receita)


def test_add_uo_sigla(receita):
    original_order = receita.columns.tolist()
    sem_desc = receita.drop(columns =['uo_sigla']).reset_index(drop=True)
    resultado = adiciona_desc(sem_desc, 'uo_cod')
    pd.testing.assert_frame_equal(resultado[original_order], receita)


def test_add_lista_desc_overwrite(receita):
    original_order = receita.columns.tolist()
    resultado = adiciona_desc(receita, ['uo_cod', 'receita_cod'], overwrite=True)
    pd.testing.assert_frame_equal(resultado[original_order], receita)