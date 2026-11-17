import pandas as pd
import pytest

from nat import nat

@pytest.fixture
def codigos_exemplo():
  return pd.Series(
      ["339014", "339030", "449052", "319011", None],
      index=[10, 20, 30, 40, 50],  # Índice customizado para garantir preservação
  )


def test_apenas_inclusao(codigos_exemplo):
  resultado = nat(codigos_exemplo, [3390, 4490])
  esperado = pd.Series(
      [True, True, True, False, False],
      index=codigos_exemplo.index,
  )
  pd.testing.assert_series_equal(resultado, esperado)


def test_inclusao_com_exclusao(codigos_exemplo):
  # Inclui 3390 e 4490, mas barra especificamente o 339030
  resultado = nat(codigos_exemplo, [3390, 4490, -339030])
  esperado = pd.Series(
      [True, False, True, False, False],
      index=codigos_exemplo.index,
  )
  pd.testing.assert_series_equal(resultado, esperado)


def test_lista_vazia_ou_so_exclusao(codigos_exemplo):
  esperado_falso = pd.Series(False, index=codigos_exemplo.index)

  pd.testing.assert_series_equal(nat(codigos_exemplo, []), esperado_falso)
  pd.testing.assert_series_equal(
      nat(codigos_exemplo, [-3390]), esperado_falso
  )