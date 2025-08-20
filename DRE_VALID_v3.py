class DRE_Validator:
    """Classe para validar cálculos do DRE (Demonstrativo de Resultados do Exercício)"""

    def __init__(self, df_dre, column_account='id conta original', column_value='valor conta original', margem_tolerancia=2.0):
        self.df_dre = df_dre
        self.column_account = column_account
        self.column_value = column_value
        self.margem_tolerancia = margem_tolerancia

    def get_value(self, df, nm_account, column_values):
        """Obtém o valor de uma conta específica ou múltiplas contas"""
        mask = df[self.column_account].isin(nm_account)
        return df.loc[mask, column_values].sum() if mask.any() else 0

    def exist_account(self, df, nm_account):
        """Verifica se uma conta existe ou se alguma das contas existe"""
        return df[self.column_account].isin(nm_account).any()

    def check_accounts(self, df, nm_account_main, nm_account_dep_pri, nm_account_dep_sec, column_values=None):
        """
             1: Cálculo CORRETO
             0: Cálculo NÃO APLICAVEL
            -1: Cálculo INCORRETO
        """
        if column_values is None:
            column_values = self.column_value
        # Lógica de verificação
        if self.exist_account(df, nm_account_main):
            if self.exist_account(df, nm_account_dep_pri) or self.exist_account(df, nm_account_dep_sec):
                # Caso 1: HÁ CONTAS DEPENDENTES | cálculo BATE com a conta principal
                if abs(self.get_value(df, nm_account_main, column_values) -
                       (self.get_value(df, nm_account_dep_pri, column_values) +
                        self.get_value(df, nm_account_dep_sec, column_values))) <= self.margem_tolerancia:
                    return 1
                # Caso 2: HÁ CONTAS DEPENDENTES | cálculo NÃO BATE com a conta principal
                else:
                    return -1
            else:
                # Caso 3: NÃO HÁ CONTAS DEPENDENTES
                return -99
        else:
            # Caso 4: NÃO HÁ CONTA PRINCIPAL
            return 0

    def solver_sinais_balanco(self, df, id_resultado, id_parcela1, id_parcela2):
        # Separar valores por ID
        valores_id_pri = df[df[self.column_account] == id_parcela1][self.column_value].values if any(df[self.column_account] == id_parcela1) else np.array([])
        valores_id_sec = df[df[self.column_account] == id_parcela2][self.column_value].values if any(df[self.column_account] == id_parcela2) else np.array([])
        valor_id_main = df[df[self.column_account] == id_resultado][self.column_value].iloc[0]
        
        # Combinar todos os valores que precisam ter sinais determinados
        todos_valores = np.concatenate([valores_id_pri, valores_id_sec])
        todos_ids = ([id_parcela1] * len(valores_id_pri)) + ([id_parcela2] * len(valores_id_sec))
        
        solucoes_validas = []
        # Usando força bruta para encontrar combinações dentro da margem de tolerância
        for sinais in product([1, -1], repeat=len(todos_valores)):
            soma_calculada = sum(valor * sinal for valor, sinal in zip(todos_valores, sinais))
            diferenca = abs(soma_calculada - valor_id_main)
            
            if diferenca <= self.margem_tolerancia:
                solucoes_validas.append((sinais, soma_calculada, diferenca))
        
        if solucoes_validas:
            solucoes_validas.sort(key=lambda x: x[2])
            melhor_solucao = solucoes_validas[0]
            sinais, soma_calculada, diferenca = melhor_solucao

            # Criar DataFrame resultado
            df_resultado = df.copy()
            df_resultado['sinal'] = 1  # Inicializar todos com +1
            
            # Aplicar sinais encontrados
            # Para ID primário
            if len(valores_id_pri) > 0:
                indices_id_pri = df[df[self.column_account] == id_parcela1].index
                for i, idx in enumerate(indices_id_pri):
                    df_resultado.loc[idx, 'sinal'] = sinais[i]
            
            # Para ID secundário
            if len(valores_id_sec) > 0:
                indices_id_sec = df[df[self.column_account] == id_parcela2].index
                offset = len(valores_id_pri)
                for i, idx in enumerate(indices_id_sec):
                    df_resultado.loc[idx, 'sinal'] = sinais[offset + i]
            
            # Calcular valores com sinal
            df_resultado['valor conta ajust'] = df_resultado[self.column_value] * df_resultado['sinal']
            
            return df_resultado
        else:
            return

    def identify_ids_remove(self, df, id_resultado, id_parcela1, id_parcela2, max_remocoes=4):
        # Função para testar combinações de remoção
        def testar_remocao(indices_remover):
            df_temp = df.drop(indices_remover)
            temp_parcela1 = df_temp[df_temp[self.column_account] == str(id_parcela1)][self.column_value].values
            temp_parcela2 = df_temp[df_temp[self.column_account] == str(id_parcela2)][self.column_value].values
            temp_resultado = df_temp[df_temp[self.column_account] == str(id_resultado)][self.column_value].values
            
            return sum(temp_parcela1) + sum(temp_parcela2) == sum(temp_resultado)
        
        # Tentar remoção de uma linha por vez
        solucoes_individuais = []
        for idx in df.index:
            if testar_remocao([idx]):
                linha_info = df.loc[idx]
                solucoes_individuais.append({'indices': [idx]})
        
        # Se não encontrou soluções individuais, tentar combinações
        if not solucoes_individuais:
            max_combinacoes = min(len(df) // 2, max_remocoes)
            for tamanho in range(2, max_combinacoes + 1):
                for combo in itertools.combinations(df.index, tamanho):
                    if testar_remocao(list(combo)):
                        linhas_info = df.loc[list(combo)]
                        solucoes_individuais.append({'indices': list(combo)})
                        break

                if solucoes_individuais:
                    break
        
        # Análise detalhada das soluções    
        melhor_solucao = None
        if solucoes_individuais:
            # Priorizar soluções que removem menos linhas
            melhor_solucao = min(solucoes_individuais, key=lambda x: len(x['indices']))

            return melhor_solucao
        else:
            print('Nenhuma solução encontrada.')

        return None

    def consolidate_results(self):
        '''
        Verificacao 01: Venda Líquida = Venda Bruta - Dedução Total
        Verificacao 02: Lucro Bruto = Venda Líquida - CMV
        Verificacao 03: Resultado Operacional = Lucro Bruto - (Despesas Operacionais - Receitas Operacionais)
        Verificacao 04: Resultado Financeiro = Resultado Operacional - (Despesas Financeiras - Receitas Financeiras)
        Verificacao 05: Resultado Antes Imposto = Resultado Financeiro - (Despesas Não Oper. - Receitas Não Oper.)
        Verificacao 06: Lucro Liquido = Resultado Antes Imposto - (Impostos)

        Consolida os resultados dos processos em um dicionário e indica linhas excedentes para remocão
        '''
        #consolidador de resultados
        results = 0
        # 1ª passo - Vendas Líquidas
        print( '\nIniciando verificacao 01: vendas liq.)
        vendas_liq_check_account = self.check_accounts(self.df_dre, ['3'], ['1'], ['2'])
        if vendas_liq_check_account == 1:
            print('----Verificacao 01: OK|sem correçoes')
            df_vendas_liquidas = self.df_dre[self.df_dre[self.column_account].isin(['3', '1', '2'])]
            df_vendas_liquidas['sinal'] = 1
            df_vendas_liquidas['valor conta ajust'] = df_vendas_liquidas[self.column_value] * df_vendas_liquidas['sinal']
            results['Verificacao 01 (vendas liq.)'] = vendas_liq_check_account
        elif vendas_liq_check_account = -99:
            print('----Verificacao 01: NA')
            df_vendas_liquidas = pd.DataFrame()
            results['Verificacao 01 (vendas liq.)'] = vendas_liq_check_account
        elif vendas_liq_check_account = 0:
            print('----Verificacao 01: NA)
            # Passando p/proxima validação
            df_vendas_liq_valid2 = self.df_dre[self.df_dre[self.column_account].isin(['3', '1', '2'])]
            df_vendas_liq_valid2[self.column_account] = '4'
            self.df_dre = pd.concat([df_vendas_liq_valid2, self.df_dre], ignore_index-True)
            df_vendas_liquidas = pd.DataFrame()
            results[ 'Verificacao 01 (vendas liq.)'] = vendas_liq_check_account
        elif vendas_liq_check_account == -1:
            print('----Verificacao 01: NÃO OK')
            # Testando ajuste de sinal
            df_vendas_liq_nok = self.df_dre[self.df_dre[self.column_account].isin(['3', '1', '2'])]
            df_resultado = self.solver_sinais_balanco(df_vendas_liq_nok, '3', '1', '2')
            if isinstance(df_resultado, pd.DataFrame) and self.check_accounts(df_resultado, ['3'], ['l'], ['2'], 'valor conta ajust') == 1:
                print('--------Verificacao 01: OK|Ajuste de sinais')
                df_vendas_liquidas = df_resultado
                results['Verificacao 01 (vendas liq.)'] = 1

            else:
                print('--------Verificacao 01: NÃO OK|Ajuste de sinais')
                ids_line_remove - self.identify_ids_remove(df_vendas_liq_nok, '3', '1', '2')
                if isinstance(ids_line_remove, dict):
                    df_resultado = df_vendas_liq_nok.drop(ids_line_remove['indices'])
                else:
                    df_resultado = df_vendas_liq_nok
                if self.check_accounts(df_resultado, ['3'], ['l'], ['2'], 'valor conta ajust') == 1:
                    print('--------Verificacao 01: OK|Ajuste linhas excedentes')
                    df_resultado['sinal'] = 1
                    df_resultado['valor conta ajust'] = df_resultado[self.column_value] * df_resultado['sinal']
                    df_vendas_liquidas = df_resultado
                    results['Verificacao 01 (vendas liq.)'] = 1
                else:
                    print('--------Verificacao 01: NÃO 0K )
                    results['Verificacao 01 (vendas liq.)'] = vendas_liq_check_account
                    df_vendas_liquidas = df_vendas_liq_nok





    {
  "nome conta original": {
    "0": "Venda Liquida",
    "1": "CMV",
    "2": "Lucro Bruto",
    "3": "Despesa Administrativa",
    "4": "Despesa de Venda",
    "5": "Outra Despesa Operacional",
    "6": "Resultado Operacional Antes do Financeiro",
    "7": "Receita Financeira",
    "8": "Despesa Financeira",
    "9": "Resultado Após Rec/Desp Financeiras",
    "10": "Resultado Antes IR/CSLL",
    "11": "Imposto de Renda",
    "12": "Imposto de Renda",
    "13": "Lucros Liquidos"},
  "nome conta conteudo": {
    "0": "receita operacional liquida",
    "1": "custos de vendas e serviços prestados",
    "2": "lucro bruto",
    "3": "despesas gerais e administrativas",
    "4": "despesa comerciais",
    "5": "outras receitas (despesas) operacional liquidas",
    "6": "lucro operacional",
    "7": "despesas financeiras",
    "8": "receitas financeiras",
    "9": "resultado financeiro liquido",
    "10": "lucro antes do imposto de renda e contribuição social",
    "11": "imposto de renda e contribuição social correntes",
    "12": "imposto de renda e contribuição social diferidos",
    "13": "lucro liquido do exercicio"},
  "valor conta original": {
    "0": 267943.0,
    "1": -229413.0,
    "2": 38530.0,
    "3": -20917.0,
    "4": -2354.0,
    "5": -2924.0,
    "6": 12335.0,
    "7": 1800.0,
    "8": -4088.0,
    "9": -2288.0,
    "10": 10047.0,
    "11": -3047.0,
    "12": -26.0,
    "13": 6974.0},
  "id conta original": {
    "0": "3",
    "1": "4",
    "2": "5",
    "3": "6",
    "4": "6",
    "5": "6",
    "6": "7",
    "7": "8",
    "8": "8",
    "9": "9",
    "10": "11",
    "11": "12",
    "12": "12",
    "13": "13"}
}