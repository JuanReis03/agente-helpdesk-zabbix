import shutil
import subprocess
import time

from core.logging_config import get_logger

logger = get_logger(__name__)

TIMEOUT_PADRAO_SEGUNDOS = 180


def executar_limpeza(nome_tarefa: str, comando_ps: str, timeout: int = TIMEOUT_PADRAO_SEGUNDOS) -> dict:
    """
    Executa um comando PowerShell e retorna um dicionário estruturado com as métricas.
    """
    logger.info(f"[{nome_tarefa}] Iniciando execução...")

    espaco_antes = shutil.disk_usage("C:\\").free
    inicio = time.time()

    try:
        resultado = subprocess.run(
            ["powershell", "-Command", comando_ps],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        sucesso = (resultado.returncode == 0)
        saida = resultado.stderr.strip() if not sucesso else resultado.stdout.strip()
    except subprocess.TimeoutExpired:
        sucesso = False
        saida = f"Comando excedeu o tempo limite de {timeout}s e foi interrompido."
    except OSError as exc:
        sucesso = False
        saida = f"Falha ao iniciar o PowerShell: {exc}"

    fim = time.time()
    espaco_depois = shutil.disk_usage("C:\\").free

    bytes_liberados = espaco_depois - espaco_antes
    mb_liberados = max(0.0, bytes_liberados / (1024 * 1024))

    dados = {
        "tarefa": nome_tarefa,
        "sucesso": sucesso,
        "tempo_segundos": round(fim - inicio, 2),
        "mb_liberados": round(mb_liberados, 2),
        "erros": saida,
    }

    logger.info(f"[{nome_tarefa}] Status: {'Sucesso' if sucesso else 'Falha'}")
    if not sucesso:
        logger.error(f"[{nome_tarefa}] Erro: {dados['erros']}")
    return dados