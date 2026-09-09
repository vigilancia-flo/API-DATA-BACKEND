import os
from api.models import PacienteDengue
from dbfread import DBF

MAPEA_ENDEMIAS = {
    'dengon': PacienteDengue,  # Pega os arquivos tipo DENGON2812249_00.dbf
    'sifilis': PacienteSifilis, # mudar conforme o nome do arquivo original
}


def processar_arquivo_dbf(caminho_arquivo):
    nome_arquivo = os.path.basename(caminho_arquivo).lower()
    modelo_alvo = None

    # 1. identificar qual é a endemia baseada no nome do arquivo
    for chave, modelo in MAPEA_ENDEMIAS.items():
        if chave in nome_arquivo:
            modelo_alvo = modelo
            break

    if not modelo_alvo:
        return {"status": "erro", "mensagem": "Endemia não reconhecida pelo nome do arquivo."}

    # 2. le o arquivo DBF e preparar os dados
    registros_para_salvar = []
    tabela_dbf = DBF(caminho_arquivo, encoding='latin1')

    for registro in tabela_dbf:
        nova_linha = modelo_alvo(**registro)
        registros_para_salvar.append(nova_linha)

    # 3. salvar no banco de dados em lote (muito mais rápido que salvar um por um)
    modelo_alvo.objects.bulk_create(registros_para_salvar, ignore_conflicts=True)

    return {"status": "sucesso", "registros_inseridos": len(registros_para_salvar)}