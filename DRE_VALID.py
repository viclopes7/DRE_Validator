import pandas as pd


class DREValidator:
    """Classe para validar cálculos do DRE (Demonstrativo de Resultados do Exercício)"""
    
    def __init__(self, df_dre, column_account='nome conta original', column_value='valor conta original', margem_tolerancia=2.0):
        self.df_dre = df_dre
        self.column_account = column_account
        self.column_value = column_value
        self.margem_tolerancia = margem_tolerancia
    
    def get_value(self, df, nm_account, column_values):
        """Obtém o valor de uma conta específica ou múltiplas contas"""
        # Caso: múltiplas contas
        mask = df[self.column_account].isin(nm_account)
        return df[mask, self.column_values].sum() if mask.any() else 0
    
    def exist_account(self, df, nm_account):
        """Verifica se uma conta existe ou se alguma das contas existe"""
        # Caso: múltiplas contas
        return df[self.column_account].isin(nm_account).any()
    
    def check_accounts(self, df, nm_account_main, nm_account_dep_pri, nm_account_dep_sec, column_values=None):
        """
            1: Cálculo correto
            -1: Cálculo incorreto
            0: Não há contas dependentes
        """
        # Lógica de verificação
        if self.exist_account(df, nm_account_main):
            # Caso 1: tem contas dependentes (primária e secundária)
            if self.exist_account(nm_account_dep_sec):
                # Caso 1a: HÁ CONTAS DEPENDENTES | cálculo BATE com a conta principal
                if self.get_value(nm_account_main) == (self.get_value(nm_account_dep_pri) - abs(self.get_value(nm_account_dep_sec))):
                    return 1
                # Caso 1b: HÁ CONTAS DEPENDENTES | cálculo NÃO BATE com a conta principal
                else:
                    return -1
            # Caso 2: somente conta dependente primária
            else:
                # Caso 2a: HÁ SÓ CONTA DEPENDENTE PRIMÁRIA | cálculo BATE com a conta principal
                if self.get_value(nm_account_dep_pri) == self.get_value(nm_account_main):
                    return 1
                # Caso 2b: HÁ SÓ CONTA DEPENDENTE PRIMÁRIA | cálculo NÃO BATE com a conta principal
                else:
                    return -1
        else:
            # Caso 3: HÁ SÓ CONTA DEPENDENTE SECUNDÁRIA (erro lógico)
            if self.exist_account(nm_account_dep_sec):
                return -1
            # Caso 4: NÃO HÁ CONTAS DEPENDENTES
            else:
                return 0
    
    def process_vendas_liquidas(self):
        """
        Verifica: Venda Líquida = Venda Bruta - Dedução Total
        
        Returns:
            tuple: (resultado_check, mensagem)
        """
        check_vendas_liquidas = self.check_accounts('Venda Líquida', 'Venda Bruta', 'Dedução Total')
        
        if check_vendas_liquidas == 1:
            if self.exist_account('Dedução Total'):
                mensagem = 'OK! "vendas líquidas" igual "vendas brutas" menos "deduções".'
            else:
                mensagem = 'OK! só há "vendas brutas", sem "deduções".'
        elif check_vendas_liquidas == -1:
            if self.exist_account('Dedução Total'):
                mensagem = 'ERRO! "vendas líquidas" diferente "vendas brutas" menos "deduções".'
            else:
                mensagem = 'ERRO! não há "deduções", porém "vendas brutas" diferentes de "vendas líquidas".'
        else:  # check_vendas_liquidas == 0
            mensagem = 'OK! não há "vendas brutas" nem "deduções".'
        
        print(mensagem)
        return check_vendas_liquidas, mensagem
    
    def process_lucro_bruto(self):
        """
        Verifica: Lucro Bruto = Venda Líquida - CMV
        
        Returns:
            tuple: (resultado_check, mensagem)
        """
        check_lucro_bruto = self.check_accounts('Lucro Bruto', 'Venda Líquida', 'CMV')
        
        if check_lucro_bruto == 1:
            if self.exist_account('CMV'):
                mensagem = 'OK! "lucro bruto" igual "vendas líquidas" menos "custos".'
            else:
                mensagem = 'OK! só há "vendas líquidas", sem "custos".'
        elif check_lucro_bruto == -1:
            if self.exist_account('CMV'):
                mensagem = 'ERRO! "lucro bruto" diferente "vendas líquidas" menos "custos".'
            else:
                mensagem = 'ERRO! não há "custos", porém "vendas líquidas" diferentes de "lucro bruto".'
        else:  # check_lucro_bruto == 0
            mensagem = 'OK! não há "vendas líquidas" nem "custos".'
        
        print(mensagem)
        return check_lucro_bruto, mensagem
    
    def process_result_oper(self):
        """
        Verifica: Resultado Operacional = Lucro Bruto - (Despesas Operacionais - Receitas Operacionais)
        
        Returns:
            tuple: (resultado_check, mensagem)
        """
        contas_secundarias = ['Despesa Administrativa', 'Despesa de Venda', 
                             'Outra Despesa Operacional', 'Outra Receita Operacional']
        
        check_result_oper = self.check_accounts('Resultado Operacional Antes do Financeiro', 
                                              'Lucro Bruto', 
                                              contas_secundarias)
        
        if check_result_oper == 1:
            if self.exist_account(contas_secundarias):
                mensagem = 'OK! "resultado operacional" igual "lucro bruto" menos "despesas operacionais".'
            else:
                mensagem = 'OK! só há "lucro bruto", sem "despesas operacionais".'
        elif check_result_oper == -1:
            if self.exist_account(contas_secundarias):
                mensagem = 'ERRO! "resultado operacional" diferente "lucro bruto" menos "despesas operacionais".'
            else:
                mensagem = 'ERRO! não há "despesas operacionais", porém "lucro bruto" diferentes de "resultado operacional".'
        else:  # check_result_oper == 0
            mensagem = 'OK! não há "lucro bruto" nem "despesas operacionais".'
        
        print(mensagem)
        return check_result_oper, mensagem


# Exemplo de uso
if __name__ == "__main__":
    # Dados de exemplo
    dados_exemplo = {
        'nome conta original': [
            'Venda Bruta', 'Dedução Total', 'Venda Líquida', 
            'CMV', 'Lucro Bruto', 'Despesa Administrativa', 'Despesa de Venda',
            'Resultado Operacional Antes do Financeiro'
        ],
        'valor conta original': [
            1000.0, -100.0, 900.0, 
            -300.0, 600.0, -150.0, -50.0,
            400.0
        ]
    }
    
    df_exemplo = pd.DataFrame(dados_exemplo)
    
    # Criar o validador
    validator = DREValidator(df_exemplo)
    
    # Executar verificações
    print("=== VERIFICAÇÃO VENDAS LÍQUIDAS ===")
    resultado_vendas, msg_vendas = validator.process_vendas_liquidas()
    
    print("\n=== VERIFICAÇÃO LUCRO BRUTO ===")
    resultado_lucro, msg_lucro = validator.process_lucro_bruto()
    
    print("\n=== VERIFICAÇÃO RESULTADO OPERACIONAL ===")
    resultado_oper, msg_oper = validator.process_result_oper()
    
    # Resultados
    print(f"\nResultado vendas líquidas: {resultado_vendas}")
    print(f"Resultado lucro bruto: {resultado_lucro}")
    print(f"Resultado operacional: {resultado_oper}")




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