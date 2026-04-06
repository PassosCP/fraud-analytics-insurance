import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Garantir que a pasta de dados exista
os.makedirs('data/raw', exist_ok=True)

def gerar_dados_seguros(n_linhas=55000):
    print(f"🎲 Gerando {n_linhas} linhas de dados sintéticos com padrões de fraude...")
    
    np.random.seed(42) # Para que os resultados sejam consistentes
    
    # 1. GERAR VEÍCULOS
    id_veiculos = range(1000, 1000 + n_linhas)
    valores_fipe = np.random.normal(50000, 15000, n_linhas).clip(15000, 150000)
    veiculos = pd.DataFrame({
        'id_veiculo': id_veiculos,
        'valor_fipe': valores_fipe.round(2),
        'tipo_veiculo': np.random.choice(['Passeio', 'Utilitário', 'Moto'], n_linhas)
    })

    # 2. GERAR APÓLICES
    id_apolices = range(2000, 2000 + n_linhas)
    data_hoje = datetime(2026, 4, 6)
    datas_inicio = [data_hoje - timedelta(days=np.random.randint(1, 365)) for _ in range(n_linhas)]
    
    apolices = pd.DataFrame({
        'id_apolice': id_apolices,
        'id_veiculo': id_veiculos,
        'cpf_segurado': np.random.choice([f'CPF_{i}' for i in range(1000)], n_linhas), # Estimula reincidência
        'data_inicio_vigencia': datas_inicio,
        'cobertura': np.random.choice(['Total', 'Terceiros', 'Roubo/Furto'], n_linhas)
    })

    # 3. GERAR SINISTROS
    id_sinistros = range(3000, 3000 + n_linhas)
    # Data do sinistro sempre após o início da vigência
    datas_sinistro = [d + timedelta(days=np.random.randint(0, 30)) for d in datas_inicio]
    
    sinistros = pd.DataFrame({
        'id_sinistro': id_sinistros,
        'id_apolice': id_apolices,
        'data_ocorrencia': datas_sinistro,
        'tipo_sinistro': np.random.choice(['Colisão', 'Roubo', 'Alagamento'], n_linhas),
        'valor_reclamado': (valores_fipe * np.random.uniform(0.1, 1.1)).round(2),
        'grande_monta': np.random.choice([0, 1], n_linhas, p=[0.9, 0.1])
    })

    # 4. CRIAR O "GABARITO" DE FRAUDE (Onde o modelo aprende!)
    # Vamos criar regras que o Random Forest consiga identificar
    temp_df = sinistros.merge(apolices, on='id_apolice').merge(veiculos, on='id_veiculo')
    temp_df['dias_vigencia'] = (temp_df['data_ocorrencia'] - temp_df['data_inicio_vigencia']).dt.days
    temp_df['alerta_fipe'] = temp_df['valor_reclamado'] / temp_df['valor_fipe']
    temp_df['reincidencia'] = temp_df.groupby('cpf_segurado')['id_sinistro'].transform('count')

    def logica_fraude(row):
        score_suspeita = 0
        # Regra 1: Sinistro nos primeiros 5 dias de seguro (Clássico de Pré-existência)
        if row['dias_vigencia'] < 5: score_suspeita += 45
        # Regra 2: Valor reclamado maior que a FIPE (Tentativa de lucro)
        if row['alerta_fipe'] > 1.0: score_suspeita += 35
        # Regra 3: Segurado com muitos sinistros no mesmo ano
        if row['reincidencia'] > 3: score_suspeita += 25
        
        # Define se é fraude confirmada (1) ou regular (0)
        # Adicionamos um pouco de "ruído" (random) para não ser óbvio demais
        limiar = 70
        return 1 if (score_suspeita + np.random.randint(0, 40)) > limiar else 0

    fraudes = pd.DataFrame({
        'id_sinistro': id_sinistros,
        'flag_fraude_confirmada': temp_df.apply(logica_fraude, axis=1)
    })

    # 5. SALVAR TUDO
    veiculos.to_csv('data/raw/veiculos.csv', index=False)
    apolices.to_csv('data/raw/apolices.csv', index=False)
    sinistros.to_csv('data/raw/sinistros.csv', index=False)
    fraudes.to_csv('data/raw/fraudes_confirmadas.csv', index=False)
    
    print("✅ Arquivos gerados com sucesso em data/raw/")
    print(f"📊 Total de Fraudes Geradas: {fraudes['flag_fraude_confirmada'].sum()}")

if __name__ == "__main__":
    gerar_dados_seguros()