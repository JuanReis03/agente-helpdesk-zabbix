import subprocess
import time
import shutil

from core.logging_config import get_logger

logger = get_logger(__name__)


def executar_limpeza(nome_tarefa: str, comando_ps: str) -> dict:
    """
    Executa um comando PowerShell e retorna um dicionário estruturado com as métricas.
    """
    logger.info(f"[{nome_tarefa}] Iniciando execução...")
    
    espaco_antes = shutil.disk_usage("C:\\").free
    inicio = time.time()
    
    resultado = subprocess.run(
        ["powershell", "-Command", comando_ps],
        capture_output=True,
        text=True
    )
    
    fim = time.time()
    espaco_depois = shutil.disk_usage("C:\\").free
    
    sucesso = (resultado.returncode == 0)
    bytes_liberados = espaco_depois - espaco_antes
    mb_liberados = max(0.0, bytes_liberados / (1024 * 1024))
    
    dados = {
        "tarefa": nome_tarefa,
        "sucesso": sucesso,
        "tempo_segundos": round(fim - inicio, 2),
        "mb_liberados": round(mb_liberados, 2),
        "erros": resultado.stderr.strip() if not sucesso else resultado.stdout.strip()
    }
    
    logger.info(f"[{nome_tarefa}] Status: {'Sucesso' if sucesso else 'Falha'}")
    if not sucesso:
        logger.error(f"[{nome_tarefa}] Erro: {dados['erros']}")
    return dados