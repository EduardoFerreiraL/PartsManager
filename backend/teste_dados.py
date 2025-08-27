#!/usr/bin/env python3
"""
Script para testar a estrutura dos dados retornados pela API
"""

import requests
import json

def test_api_data():
    """Testa a estrutura dos dados da API"""
    base_url = "http://localhost:8000"
    
    try:
        print("🔍 Testando estrutura dos dados da API...")
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
        
        # 2. Testar busca de peças
        print("2. Testando busca de peças...")
        response = requests.get(f"{base_url}/api/pecas?limit=5")
        if response.status_code == 200:
            data = response.json()
            print("✅ Busca de peças funcionando")
            print(f"   Total encontrado: {data.get('total_encontrado', 'N/A')}")
            
            if data.get('pecas') and len(data['pecas']) > 0:
                primeira_peca = data['pecas'][0]
                print(f"   Primeira peça: {primeira_peca}")
                print(f"   Colunas disponíveis: {list(primeira_peca.keys())}")
                
                # Verificar se tem ID
                if 'id' in primeira_peca:
                    print(f"   ✅ ID encontrado: {primeira_peca['id']}")
                else:
                    print("   ❌ ID não encontrado!")
                    
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
            
            if peca_id:
                print("3. Testando endpoint de atualização...")
                update_data = {"description": "TESTE - " + str(primeira_peca.get('description', ''))}
                
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
                print("3. ⚠️  Não é possível testar atualização sem ID")
        
        print()
        print("🎯 Teste concluído!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: Servidor não está rodando")
        print("   Execute: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    test_api_data()

