from datetime import date
import json
from ..models.models import Parametro 

def calcular_status(data_validade):
    """
    Calcula o status do documento (VIGENTE, A_VENCER, VENCIDO, SEM_VALIDADE)
    com base na data de validade e no maior período de alerta configurado.
    """
    # SEM_VALIDADE 
    if data_validade is None:
        return 'SEM_VALIDADE'

    hoje = date.today()
    diferenca = data_validade - hoje

    # 1. Obter período de alerta 
    N = 30 # Valor padrão 

    try:
        # Tenta buscar o maior valor de alerta configurado
        config = Parametro.query.first() 
        if config and config.dias_alerta_json:
            alerta_list = json.loads(config.dias_alerta_json)
            # N é o maior valor configurado para definir o horizonte 'A_VENCER'
            if isinstance(alerta_list, list) and alerta_list:
                N = max(alerta_list)
        
    except Exception:
        pass 

    if diferenca.days < 0:
        # VENCIDO (validade < hoje)
        return 'VENCIDO'
    elif diferenca.days <= N:
        # A_VENCER (validade em <= N dias)
        return 'A_VENCER'
    else:
        # VIGENTE (validade futura distante)
        return 'VIGENTE'