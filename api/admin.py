from django.contrib import admin
from dbfread import DBF
from .models import PacienteDengue, PacienteTuberculose, UploadDBF
from datetime import datetime


@admin.register(PacienteDengue)
class PacienteDengueAdmin(admin.ModelAdmin):
    # mostra essas colunas na listagem do admin
    list_display = ("numero_notificacao", "nome_paciente", "data_notificacao", "endereco", "data_nascimento", "data_pri_sintoma", "id_agravo", "id_unidade", "hospital", "cs_sexo", "classi_fin")
    # essas colunas podem ser usadas como mecanismo de pesquisa
    search_fields = ("numero_notificacao", "nome_paciente", "classi_fin", "endereco", "id_unidade")

@admin.register(PacienteTuberculose)
class PacienteTuberculoseAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "nu_notific")

@admin.register(UploadDBF)
class UploadDBFAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        table = DBF(obj.arquivo.path, encoding='iso-8859-1', load=True, ignore_missing_memofile=True)

        # 1. Coloque a função auxiliar AQUI DENTRO:
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

        # 2. O loop continua normalmente, mas agora aplicando a função:
        for record in table:
            partes_endereco = [
                record.get('NM_LOGRADO'),
                record.get('NM_NUMERO'),
                record.get('NM_COMPLEM'),
                record.get('NM_BAIRRO'),
                record.get('NU_CEP'),
            ]
            partes_validadas = [str(p).strip() for p in partes_endereco if p and str(p).strip()]
            endereco_formatado = ", ".join(partes_validadas)

            # 3. Aplique o formatar_data() nos campos de data!
            PacienteDengue.objects.create(
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