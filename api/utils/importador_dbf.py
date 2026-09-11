import os
from api.models import PacienteDengue, PacienteTuberculose, PacienteSifilis
from dbfread import DBF
from datetime import datetime

# Dicionário mapeando a chave no nome do arquivo para o Model
MAPEA_ENDEMIAS = {
    'dengon': PacienteDengue,
    'tubercu': PacienteTuberculose,
    'sifi': PacienteSifilis,
}


def processar_arquivo_dbf(caminho_arquivo):
    nome_arquivo = os.path.basename(caminho_arquivo).lower()
    modelo_alvo = None

    for chave, modelo in MAPEA_ENDEMIAS.items():
        if chave in nome_arquivo:
            modelo_alvo = modelo
            break

    if not modelo_alvo:
        return {"status": "erro", "mensagem": "Endemia não reconhecida pelo nome do arquivo."}

    def formatar_data(valor_data):
        if not valor_data:
            return None
        try:
            data_limpa = str(valor_data).strip().split(" ")[0]
            if data_limpa == "30/12/1899":
                return None
            data_obj = datetime.strptime(data_limpa, "%d/%m/%Y")
            return data_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError, AttributeError):
            return None

    registros_para_salvar = []
    tabela_dbf = DBF(caminho_arquivo, encoding='iso-8859-1', load=True, ignore_missing_memofile=True)

    for record in tabela_dbf:

        # LÓGICA PARA DENGUE
        if modelo_alvo == PacienteDengue:
            partes_endereco = [
                record.get('NM_LOGRADO'),
                record.get('NM_NUMERO'),
                record.get('NM_COMPLEM'),
                record.get('NM_BAIRRO'),
                record.get('NU_CEP'),
            ]
            partes_validadas = [str(p).strip() for p in partes_endereco if p and str(p).strip()]
            endereco_formatado = ", ".join(partes_validadas)

            nova_linha = PacienteDengue(
                numero_notificacao=record.get('NU_NOTIFIC'),
                nome_paciente=record.get('NM_PACIENT'),
                data_notificacao=formatar_data(record.get('DT_NOTIFIC')),
                data_pri_sintoma=formatar_data(record.get('DT_SIN_PRI')),
                data_nascimento=formatar_data(record.get('DT_NASC')),
                endereco=endereco_formatado,
                id_agravo=record.get('ID_AGRAVO'),
                id_unidade=record.get('ID_UNIDADE'),
                hospital=record.get('HOSPITAL'),
                cs_sexo=record.get('CS_SEXO'),
                classi_fin=record.get('CLASSI_FIN'),
            )
            registros_para_salvar.append(nova_linha)

        # LÓGICA PARA TUBERCULOSE
        elif modelo_alvo == PacienteTuberculose:
            # OBS: Aqui você precisa garantir que os nomes dentro de record.get()
            # são exatamente os nomes das colunas no arquivo .dbf de Tuberculose.
            # Baseado no seu Model, coloquei alguns chutes comuns do SINAN:
            nova_linha = PacienteTuberculose(
                id_unidade=record.get('ID_UNIDADE') or record.get('ID_UNID'),
                nm_ubs=record.get('NM_UBS') or record.get('ID_UNIDADE'),  # Ajuste conforme a coluna no seu DBF
                nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
            )
            registros_para_salvar.append(nova_linha)

    # 4. Salvar no banco de dados em lote
    modelo_alvo.objects.bulk_create(registros_para_salvar, ignore_conflicts=True)

    return {"status": "sucesso", "registros_inseridos": len(registros_para_salvar)}