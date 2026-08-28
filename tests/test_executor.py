import subprocess

from core.executor import executar_limpeza


class ResultadoFake:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_executar_limpeza_sucesso(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: ResultadoFake(returncode=0, stdout="ok")
    )

    resultado = executar_limpeza("Tarefa Teste", "Write-Output ok")

    assert resultado["tarefa"] == "Tarefa Teste"
    assert resultado["sucesso"] is True
    assert resultado["erros"] == "ok"
    assert "tempo_segundos" in resultado


def test_executar_limpeza_falha(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: ResultadoFake(returncode=1, stderr="deu ruim")
    )

    resultado = executar_limpeza("Tarefa Teste", "exit 1")

    assert resultado["sucesso"] is False
    assert resultado["erros"] == "deu ruim"


def test_executar_limpeza_timeout(monkeypatch):
    def _run(*a, **k):
        raise subprocess.TimeoutExpired(cmd="powershell", timeout=1)

    monkeypatch.setattr(subprocess, "run", _run)

    resultado = executar_limpeza("Tarefa Teste", "Start-Sleep -Seconds 999", timeout=1)

    assert resultado["sucesso"] is False
    assert "tempo limite" in resultado["erros"]


def test_executar_limpeza_powershell_ausente(monkeypatch):
    def _run(*a, **k):
        raise FileNotFoundError("powershell não encontrado")

    monkeypatch.setattr(subprocess, "run", _run)

    resultado = executar_limpeza("Tarefa Teste", "Write-Output ok")

    assert resultado["sucesso"] is False
    assert "Falha ao iniciar o PowerShell" in resultado["erros"]
