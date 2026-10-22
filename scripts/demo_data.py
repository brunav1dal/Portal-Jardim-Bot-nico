"""Entirely fictional records shared by the online and static demos."""
import pandas as pd


def demo_data():
    users = [{'id': 1, 'nome': 'Administrador exemplo', 'email': 'admin@example.invalid',
              'senha': 'unused', 'tipo': 'admin', 'economia_kw': 0, 'creditos': 0,
              'kw_recebidos': 0, 'investido': 0, 'cashback_orquideas': 0,
              'data_cadastro': '2025-01-01'}]
    homes, benefits = [], []
    for i in range(1, 11):
        uid, name = i + 1, f'Pessoa exemplo {i:02d}'
        users.append(dict(users[0], id=uid, nome=name, email=f'pessoa{i}@example.invalid', tipo='cliente'))
        homes.append({'id': i, 'usuario_id': uid, 'endereco': f'UC ficticia {i:02d}',
                      'em_dia_banco': 'sim', 'em_dia_concessionaria': 'sim',
                      'cashback_em_dia': 'sim', 'consumo_mensal_kwh': 100,
                      'economia_mensal_rs': 30, 'ultima_atualizacao': '2025-02-01'})
        for month in ['2025-01', '2025-02']:
            benefits.append({'mes': month, 'usuario_id': uid, 'nome': name,
                             'percentual_cota': 10, 'cota_kwh': 100, 'consumo_total_kwh': 100,
                             'tarifa_social': 'nao', 'energia_recebida_kwh': 100,
                             'valor_beneficio_rs': 40, 'valor_projeto_rs': 20,
                             'creditos_acumulados': 0, 'vencimento': month + '-20',
                             'valor_energisa_rs': 30, 'excedeu_cota_kwh': 0, 'cashback_rs': 10})
    plants = [{'id': 1, 'nome': 'Usina demonstrativa', 'localizacao': 'Local ficticio',
               'capacidade_kw': 10, 'geracao_mensal_kwh': 1000, 'status': 'ativa',
               'data_instalacao': '2025-01-01', 'eficiencia_percent': 90}]
    generation = [{'mes': month, 'usina_id': 1, 'geracao_kwh': 1000,
                   'co2_evitado_kg': 100, 'receita_rs': 200,
                   'energia_beneficiarios_kwh': 1000, 'fonte': 'planilha'}
                  for month in ['2025-01', '2025-02']]
    return {'usuarios.csv': pd.DataFrame(users), 'residencias.csv': pd.DataFrame(homes),
            'beneficios_mensais.csv': pd.DataFrame(benefits), 'usinas.csv': pd.DataFrame(plants),
            'geracao_mensal.csv': pd.DataFrame(generation),
            'boletos.csv': pd.DataFrame(columns=['id', 'usuario_id', 'nome_arquivo', 'data_envio', 'status'])}
