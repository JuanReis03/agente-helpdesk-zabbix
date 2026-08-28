from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_health_check():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "Agente Online e Operante"}


def test_webhook_sem_token_configurado_nao_exige_header(monkeypatch):
    monkeypatch.setattr(main, "WEBHOOK_TOKEN", None)
    monkeypatch.setattr(main, "carregar_catalogo_scripts", dict)

    resposta = client.post(
        "/webhook/zabbix",
        json={"hostname": "PC01", "trigger_name": "Algo qualquer", "severity": "high"},
    )

    assert resposta.status_code == 500  # catálogo vazio, não erro de auth


def test_webhook_token_invalido_e_recusado(monkeypatch):
    monkeypatch.setattr(main, "WEBHOOK_TOKEN", "segredo")

    resposta = client.post(
        "/webhook/zabbix",
        json={"hostname": "PC01", "trigger_name": "Disk space low", "severity": "high"},
    )

    assert resposta.status_code == 401


def test_webhook_token_valido_e_aceito(monkeypatch):
    monkeypatch.setattr(main, "WEBHOOK_TOKEN", "segredo")
    monkeypatch.setattr(
        main,
        "carregar_catalogo_scripts",
        lambda: {"esvaziar_lixeira": {"nome": "Esvaziar Lixeira", "comando": "exit 0"}},
    )
    monkeypatch.setattr(
        main,
        "executar_limpeza",
        lambda nome, comando: {"tarefa": nome, "sucesso": True, "mb_liberados": 1.0},
    )

    resposta = client.post(
        "/webhook/zabbix",
        json={"hostname": "PC01", "trigger_name": "Disk space low", "severity": "high"},
        headers={"x-webhook-token": "segredo"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "Ação de mitigação executada"


def test_webhook_acao_mapeada_executa(monkeypatch):
    monkeypatch.setattr(main, "WEBHOOK_TOKEN", None)
    monkeypatch.setattr(
        main,
        "carregar_catalogo_scripts",
        lambda: {"esvaziar_lixeira": {"nome": "Esvaziar Lixeira", "comando": "exit 0"}},
    )
    monkeypatch.setattr(
        main,
        "executar_limpeza",
        lambda nome, comando: {"tarefa": nome, "sucesso": True, "mb_liberados": 5.0},
    )

    resposta = client.post(
        "/webhook/zabbix",
        json={"hostname": "PC01", "trigger_name": "Disk space low", "severity": "high"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["detalhes_execucao"]["mb_liberados"] == 5.0


def test_webhook_sem_acao_mapeada(monkeypatch):
    monkeypatch.setattr(main, "WEBHOOK_TOKEN", None)
    monkeypatch.setattr(
        main, "carregar_catalogo_scripts", lambda: {"esvaziar_lixeira": {}}
    )

    resposta = client.post(
        "/webhook/zabbix",
        json={"hostname": "PC01", "trigger_name": "CPU alta", "severity": "high"},
    )

    assert resposta.status_code == 200
    assert "não há ações automáticas mapeadas" in resposta.json()["status"]


def test_webhook_catalogo_vazio_retorna_500(monkeypatch):
    monkeypatch.setattr(main, "WEBHOOK_TOKEN", None)
    monkeypatch.setattr(main, "carregar_catalogo_scripts", dict)

    resposta = client.post(
        "/webhook/zabbix",
        json={"hostname": "PC01", "trigger_name": "Disk space low", "severity": "high"},
    )

    assert resposta.status_code == 500


def test_webhook_entrada_de_catalogo_incompleta_retorna_500(monkeypatch):
    monkeypatch.setattr(main, "WEBHOOK_TOKEN", None)
    monkeypatch.setattr(
        main, "carregar_catalogo_scripts", lambda: {"esvaziar_lixeira": {"nome": "Sem comando"}}
    )

    resposta = client.post(
        "/webhook/zabbix",
        json={"hostname": "PC01", "trigger_name": "Disk space low", "severity": "high"},
    )

    assert resposta.status_code == 500
