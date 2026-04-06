import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, roc_curve

def executar_pipeline_fraude_com_roc():
    print("🚀 Iniciando Processamento de Dados e Avaliação ROC...")

    # 1. CARGA
    try:
        path_raw = 'data/raw/'
        v = pd.read_csv(f'{path_raw}veiculos.csv')
        a = pd.read_csv(f'{path_raw}apolices.csv', parse_dates=['data_inicio_vigencia'])
        s = pd.read_csv(f'{path_raw}sinistros.csv', parse_dates=['data_ocorrencia'])
        f = pd.read_csv(f'{path_raw}fraudes_confirmadas.csv')
    except FileNotFoundError:
        print("❌ Erro: Arquivos não encontrados. Rode o 'gerador_dados.py' primeiro.")
        return

    # 2. JOINS
    df = s.merge(a, on='id_apolice').merge(v, on='id_veiculo').merge(f, on='id_sinistro')

    # 3. FEATURE ENGINEERING
    df['dias_vigencia_ate_sinistro'] = (df['data_ocorrencia'] - df['data_inicio_vigencia']).dt.days
    df['reincidencia_cpf'] = df.groupby('cpf_segurado')['id_sinistro'].transform('count')
    df['alerta_fipe'] = (df['valor_reclamado'] / df['valor_fipe']).round(4)

    # 4. PREPARAÇÃO PARA O MODELO
    features = ['valor_fipe', 'grande_monta', 'dias_vigencia_ate_sinistro', 'reincidencia_cpf', 'alerta_fipe']
    X = pd.get_dummies(df[features + ['tipo_sinistro', 'cobertura']])
    y = df['flag_fraude_confirmada']

    # 5. DIVISÃO TREINO E TESTE (80% / 20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 6. TREINAMENTO
    modelo = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    modelo.fit(X_train, y_train)

    # 7. AVALIAÇÃO COM CURVA ROC
    # Pegamos as probabilidades apenas para a base de teste (quem o modelo não viu)
    y_probs_test = modelo.predict_proba(X_test)[:, 1]
    auc_score = roc_auc_score(y_test, y_probs_test)
    
    print(f"\n📊 PERFORMANCE DO MODELO:")
    print(f"⭐ AUC-ROC: {auc_score:.4f}")

    # Gerando o gráfico da Curva ROC
    fpr, tpr, thresholds = roc_curve(y_test, y_probs_test)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'Curva ROC (área = {auc_score:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--') # Linha aleatória
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Taxa de Falsos Positivos (Clientes Honestos)')
    plt.ylabel('Taxa de Verdadeiros Positivos (Fraudes Detectadas)')
    plt.title('Validação do Modelo de Fraude - Curva ROC')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    
    # Salva o gráfico para usar no GitHub ou Portfólio
    os.makedirs('data/processed', exist_ok=True)
    plt.savefig('data/processed/validacao_curva_roc.png')
    print("📈 Gráfico da Curva ROC salvo em: data/processed/validacao_curva_roc.png")

    # 8. GERAÇÃO DO SCORE FINAL (0-100 Inteiro) PARA A BASE TODA
    df['score_fraude'] = (modelo.predict_proba(X)[:, 1] * 100).astype(int)

    # 9. EXPORTAÇÃO FINAL PARA POWER BI
    df.to_csv('data/processed/base_final_priorizacao.csv', index=False)
    print("✅ Base final gerada com sucesso!")

if __name__ == "__main__":
    executar_pipeline_fraude_com_roc()