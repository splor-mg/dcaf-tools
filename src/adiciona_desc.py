import pandas as pd


def trata_duplicados(df: pd.DataFrame):
    df = df.drop_duplicates().reset_index(drop=True)
    chaves = ['ano']
    chaves.extend([col for col in df.columns if col.endswith('_cod')])
    return df.groupby(chaves).first().reset_index()


def importa_descritivos(nomes: list[str] | str):
    """
    Importa tabelas de descritivos de classificadores orçamentários do repositório da AID.
    Baixa os CSVs correspondentes aos códigos informados (com colunas padrão de ano, código e descrição) e aplica filtros de padronização em `uo_cod` (retorna `uo_sigla`), `grupo_cod` e `categoria_cod` (deduplicado).

    Args:
        nomes (list[str] | str): Código ou lista de códigos classificadores válidos: 'acao_cod', 'elemento_cod', 'elemento_item_cod', 'fonte_cod', 'funcao_cod', 'grupo_cod', 'categoria_cod', 'iag_cod', 'ipu_cod', 'modalidade_cod', 'programa_cod', 'receita_cod', 'subfuncao_cod', 'uo_cod'.

    Returns:
        dicionário {nome: DataFrame}.

    Raises:
        ValueError: Se algum código informado não for válido (não há descritivo associado).
    """

    raw_urls = {
        'acao_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/acao.csv',
        'elemento_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/elemento.csv',
        'elemento_item_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/elemento_item.csv',
        'fonte_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/fonte.csv',
        'funcao_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/funcao.csv',
        'grupo_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/grupo_categoria.csv',
        'categoria_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/grupo_categoria.csv',
        'iag_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/iag.csv',
        'ipu_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/ipu.csv',
        'modalidade_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/modalidade.csv',
        'programa_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/programa.csv',
        'receita_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/receita.csv',
        'subfuncao_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/subfuncao.csv',
        'uo_cod': 'https://raw.githubusercontent.com/splor-mg/dados-classificadores/refs/heads/main/data/uo.csv',
    }


    invalidos = []
    for nome in (nomes if isinstance(nomes, list) else [nomes]):
        if nome not in raw_urls:
            invalidos.append(nome)
    if invalidos:
        raise ValueError(f"Os campos {', '.join(invalidos)} não possuem descritivos associados.")


    if isinstance(nomes, str):
        dado = pd.read_csv(raw_urls[nomes])
        if nomes == 'uo_cod':
            dado = dado[['ano','uo_cod', 'uo_sigla']]
        if nomes == 'grupo_cod':
            dado = dado[['ano','grupo_cod', 'grupo_desc']]
        if nomes == 'categoria_cod':
            dado = dado[['ano','categoria_cod', 'categoria_desc']]
        return {nomes: trata_duplicados(dado)}
    else:
        dados = {k: trata_duplicados(pd.read_csv(raw_urls[k])) for k in nomes}
        if 'grupo_cod' in dados:
            dados['grupo_cod'] = dados['grupo_cod'][['ano', 'grupo_cod', 'grupo_desc']]
        if 'categoria_cod' in dados:
            dados['categoria_cod'] = (trata_duplicados(dados['categoria_cod'][['ano', 'categoria_cod', 'categoria_desc']]))
        if 'uo_cod' in dados:
            dados['uo_cod'] = (trata_duplicados(dados['uo_cod'][['ano', 'uo_cod', 'uo_sigla']]))
        return dados




def adiciona_desc(
    base: pd.DataFrame,
    targets: str | list[str],
    overwrite: bool = True,
) -> pd.DataFrame:
    
    """
    Adiciona colunas de descrição aos códigos classificadores presentes na base.

    Cruza o DataFrame informado com as tabelas de descritivos correspondentes aos
    códigos em `targets` (utilizando `'ano'` e o código como chaves quando
    disponíveis). Não altera o DataFrame original (`inplace=False`).

    Args:
        base (pd.DataFrame): DataFrame contendo as colunas de códigos orçamentários.
        targets (str | list[str]): Nome ou lista de nomes das colunas de código
            a serem enriquecidas (ex: `'uo_cod'`, `['acao_cod', 'fonte_cod']`).
        overwrite (bool, optional): Se `True`, substitui colunas de descrição já
            existentes na `base`. Se `False`, ignora classificadores cujas
            descrições já estejam presentes. Padrão é `True`.

    Returns:
        pd.DataFrame: Novo DataFrame com as colunas de descrição adicionadas.

    Raises:
        ValueError: Se algum código em `targets` for inválido, não existir na `base`,
            ou se a coluna `'ano'` for exigida pelo descritivo e não existir na `base`.
    """

    if isinstance(targets, str):
        targets = [targets]

    ausentes = [c for c in targets if c not in base.columns]
    if ausentes:
        raise ValueError(f"Colunas de código não encontradas na base: {', '.join(ausentes)}")

    try:
        descritivos = importa_descritivos(targets)
    except ValueError as e:
        raise ValueError(f"Erro ao importar descritivos: {e}")
    
    
    resultado = base.copy()

    for nome, descritivo in descritivos.items():
        ano_descritivo = 'ano' in descritivo.columns
        ano_base = 'ano' in resultado.columns

        if ano_descritivo and not ano_base:
            raise ValueError(
                f"Erro ao adicionar descritivo '{nome}': coluna 'ano' não encontrada na base."
            )

        chaves_merge = ['ano', nome] if ano_descritivo else [nome]
        cols_descricao = [c for c in descritivo.columns if c not in chaves_merge]
        cols_existentes = [c for c in cols_descricao if c in resultado.columns]

        if cols_existentes:
            if overwrite:
                resultado = resultado.drop(columns=cols_existentes)
            else:
                continue

        resultado = pd.merge(
            resultado,
            descritivo,
            on=chaves_merge,
            how='left',
            validate='many_to_one',
        )

    return resultado