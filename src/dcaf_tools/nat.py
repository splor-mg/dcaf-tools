import pandas as pd
import numpy as np

def nat_as_char(x: pd.Series | list | np.ndarray) -> pd.Series:
  """
    Converte códigos numéricos ou strings para string sem notação científica
    e sem espaços extras, preservando a quantidade original de dígitos.
    """
  s = pd.Series(x)

  num = pd.to_numeric(s, errors="coerce")

  return num.map(lambda v: f"{v:.0f}" if pd.notna(v) else np.nan)


def nat(
    receita_cod: pd.Series | list | np.ndarray, *naturezas: int | float | list | tuple
) -> pd.Series:
  """
    Retorna uma Série booleana indicando quais códigos em `receita_cod`
    começam com os prefixos positivos em `naturezas` e NÃO começam
    com os prefixos negativos.

    Utilizado para identificar se um código de receita é uma natureza específica.

    --------------------------------------------------------------
    Exemplo de uso:
    - Suponha Base_rec como um pd.DataFrame com a coluna RECEITA_COD.
    - Para encontrar todas as receitas que começam com 191 e são da fonte 82, use:
    >>> rec_funset = Base_rec[(Base_rec['FONTE_COD'] == 82) & (nat(Base_rec['RECEITA_COD'], 191))]['RECEITA_COD'].unique()
    - Para filtrar essas receitas, use:
    >>> Base_rec[Base_rec['RECEITA_COD'].isin(rec_funset)]

    - Outra forma de filtrar diretamente, sem precisar criar o conjunto rec_funset:
    >>> Base_rec[(Base_rec['FONTE_COD'] == 82) & (nat(Base_rec['RECEITA_COD'], 191))]
    """

  valores = []
  for item in naturezas:
    if isinstance(item, (list, tuple, set, np.ndarray)):
      valores.extend(item)
    else:
      valores.append(item)
    
  cod_str = nat_as_char(receita_cod)

  incluir = tuple(f"{abs(n):.0f}" for n in valores if n > 0)
  excluir = tuple(f"{abs(n):.0f}" for n in valores if n < 0)

  if not incluir:
    return pd.Series(False, index=cod_str.index)

  logico_incluir = cod_str.str.startswith(incluir, na=False)

  if not excluir:
    return logico_incluir

  logico_excluir = cod_str.str.startswith(excluir, na=False)
  
  return logico_incluir & ~logico_excluir