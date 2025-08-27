#!/usr/bin/env python3
"""
Script para debugar a estrutura dos dados da API
"""

import requests
import json

def debug_api_data():
    """Debuga a estrutura dos dados da API"""
    base_url = "http://localhost:8000"
    
    try:
        print("🔍 Debugando estrutura dos dados da API...")
        print()
        
        # 1. Testar endpoint de saúde
        print("1. Testando endpoint de saúde...")
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ API está funcionando")
            print(f"   Resposta: {response.json()}")
        else:
            print(f"❌ API não está funcionando: {response.status_code}")
            return
        
        print()
        
        # 2. Testar busca de peças com debug detalhado
        print("2. Debugando busca de peças...")
        response = requests.get(f"{base_url}/api/pecas?limit=3")
        if response.status_code == 200:
            data = response.json()
            print("✅ Busca de peças funcionando")
            print(f"   Total encontrado: {data.get('total_encontrado', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            
            if data.get('pecas') and len(data['pecas']) > 0:
                print(f"\n   📊 ESTRUTURA DOS DADOS:")
                print(f"   Quantidade de peças retornadas: {len(data['pecas'])}")
                
                for i, peca in enumerate(data['pecas']):
                    print(f"\n   Peça {i+1}:")
                    print(f"     Tipo: {type(peca)}")
                    print(f"     Chaves: {list(peca.keys())}")
                    print(f"     Valores: {peca}")
                    
                    # Verificar ID especificamente
                    if 'id' in peca:
                        print(f"     ✅ ID encontrado: {peca['id']} (tipo: {type(peca['id'])})")
                    else:
                        print(f"     ❌ ID NÃO encontrado!")
                        
                    # Verificar outras colunas importantes
                    important_cols = ['part_number', 'description', 'ncm']
                    for col in important_cols:
                        if col in peca:
                            print(f"     ✅ {col}: {peca[col]} (tipo: {type(peca[col])})")
                        else:
                            print(f"     ❌ {col}: NÃO encontrado")
                
                # Verificar se há problemas com tipos
                print(f"\n   🔍 ANÁLISE DE TIPOS:")
                primeira_peca = data['pecas'][0]
                for key, value in primeira_peca.items():
                    print(f"     {key}: {type(value).__name__} = {value}")
                    
            else:
                print("   ⚠️  Nenhuma peça encontrada")
                
        else:
            print(f"❌ Erro na busca: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return
        
        print()
        
        # 3. Testar endpoint de atualização (se houver peças)
        if data.get('pecas') and len(data['pecas']) > 0:
            primeira_peca = data['pecas'][0]
            peca_id = primeira_peca.get('id')
            
            if peca_id and peca_id != 'undefined':
                print("3. Testando endpoint de atualização...")
                update_data = {"description": "DEBUG TESTE - " + str(primeira_peca.get('description', ''))}
                
                print(f"   Tentando atualizar peça ID: {peca_id}")
                print(f"   Dados de atualização: {update_data}")
                
                response = requests.put(
                    f"{base_url}/api/pecas/{peca_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Atualização funcionando")
                    print(f"   Resposta: {result}")
                else:
                    print(f"❌ Erro na atualização: {response.status_code}")
                    print(f"   Resposta: {response.text}")
            else:
                print("3. ⚠️  Não é possível testar atualização - ID inválido")
                print(f"   ID encontrado: '{peca_id}' (tipo: {type(peca_id)})")
        
        print()
        print("🎯 Debug concluído!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: Servidor não está rodando")
        print("   Execute: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_data()

