# AUTOMAÇÃO PRINCIPAL PARA RECEBIMENTO E ENVIO DE LAUDOS PARA A UNIDADE
# REQUISITANTE NO SISTEMA PERICIANET  (versão revisada)
#
# Instalação:  pip install -U pyautogui pillow opencv-python pyperclip plyer
#   (o opencv-python é obrigatório para usar o parâmetro `confidence`)
#
# Antes de rodar:
#   - navegador MAXIMIZADO, com o mesmo zoom e a mesma resolução usados ao
#     capturar as coordenadas e as imagens (.png);
#   - a 1ª guia do navegador deve ser a lista de laudos do PericiaNet;
#   - não use mouse/teclado enquanto a automação roda;
#   - EMERGÊNCIA: leve o mouse ao canto superior esquerdo da tela.

import time
import os

import pyautogui as pa
import pyperclip
from plyer import notification

# ================================ CONFIGURAÇÕES ================================
pa.FAILSAFE = True        # mouse no canto superior esquerdo (0, 0) aborta tudo
pa.PAUSE = 1              # pausa (s) depois de cada ação do pyautogui

MAX_LAUDOS = None            # TESTE: processa só 2 laudos. Use None para ir até o fim
CONFIANCA = 0.85          # 0.5 gera falsos positivos; se não achar suas imagens, tente 0.8
TIMEOUT = 45              # segundos esperando uma tela/ícone antes de abortar
ESPERA_LAUDO = 3          # segundos para o laudo abrir na nova guia
ESPERA_FILTRO = 2         # segundos para a pesquisa filtrar a tabela
ESPERA_ENCAMINHAR = 3     # segundos após encaminhar, antes de olhar a lista de novo

ARQUIVO_LOG = "log_laudos.txt"

# Coordenadas originais (ajuste se mudar resolução, zoom ou layout da página)
POS_PROTOCOLO = (382, 864)      # protocolo da 1ª linha da lista
POS_ICONE_VERDE = (1825, 861)   # ícone verde (receber)
POS_VISUALIZAR = (940, 990)     # botão para visualizar o laudo
POS_RECEBER = (1057, 992)       # botão "receber o laudo"
POS_BUSCA = (1733, 430)         # campo de pesquisa
POS_ICONE_AZUL = (1834, 555)    # ícone azul (encaminhar para a unidade requisitante)


def regiao_em_torno(pos, margem=50):
    """Região (left, top, width, height) centrada em `pos`.
    A imagem procurada precisa caber dentro da região."""
    x, y = pos
    return (x - margem, y - margem, margem * 2, margem * 2)


REGIAO_VERMELHO = (1781, 843, 44, 35)                # sua região original
REGIAO_VERDE = regiao_em_torno((1821, 861))          # ícone verde da 1ª linha
REGIAO_AZUL = regiao_em_torno(POS_ICONE_AZUL)        # só vale se estiver onde vamos clicar


# ============================== FUNÇÕES AUXILIARES ==============================
class ErroAutomacao(Exception):
    """Problema esperado (timeout, protocolo não copiado...): a automação para."""


def registrar(texto):
    """Mostra na tela e grava no arquivo de log, com data e hora."""
    linha = f"{time.strftime('%d/%m/%Y %H:%M:%S')} | {texto}"
    print(linha)
    with open(ARQUIVO_LOG, "a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def avisar(titulo, mensagem):
    """Registra e mostra uma notificação (falha na notificação nunca derruba o script)."""
    registrar(f"{titulo} - {mensagem}")
    try:
        notification.notify(
            title=titulo[:60],
            message=mensagem[:250],
            app_name="Automação PericiaNet",
            timeout=10,
        )
    except Exception as erro:
        print(f"(não foi possível exibir a notificação: {erro})")


def achar(imagem, regiao=None, confianca=None):
    """Procura a imagem na tela UMA vez. Retorna a posição ou None."""
    if confianca is None:
        confianca = CONFIANCA
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagens", imagem)
    try:
        return pa.locateOnScreen(caminho, region=regiao, confidence=confianca)
    except pa.ImageNotFoundException:
        return None


def aguardar(imagem, regiao=None, descricao=""):
    """Espera a imagem aparecer. Passou de TIMEOUT? Para com um erro claro."""
    inicio = time.time()
    while time.time() - inicio < TIMEOUT:
        pa.failSafeCheck()              # permite abortar com o mouse no canto da tela
        posicao = achar(imagem, regiao)
        if posicao is not None:
            return posicao
        time.sleep(0.5)
    raise ErroAutomacao(f"Tempo esgotado esperando: {descricao or imagem}.")


def tem_icone_verde():
    return achar("icone_verde.png", REGIAO_VERDE) is not None


def tem_icone_vermelho():
    return achar("icone_vermelho.png", REGIAO_VERMELHO, confianca=0.7) is not None


def aguardar_lista():
    """Espera a lista carregar: ícone verde (há laudo) OU vermelho (fim) na 1ª linha."""
    inicio = time.time()
    while time.time() - inicio < TIMEOUT:
        pa.failSafeCheck()
        if tem_icone_verde() or tem_icone_vermelho():
            return
        time.sleep(0.5)
    raise ErroAutomacao("A lista de laudos não carregou (sem ícone verde nem vermelho).")


# ================================== ETAPAS ====================================
def copiar_protocolo(ultimo_protocolo):
    """Copia o protocolo da 1ª linha e guarda numa variável (não só no Ctrl+C)."""
    pyperclip.copy("")                       # limpa: se a cópia falhar, a gente percebe
    pa.doubleClick(*POS_PROTOCOLO)           # se o protocolo tiver "/" ou "-", teste pa.tripleClick
    pa.hotkey("ctrl", "c")
    protocolo = pyperclip.paste().strip()

    if not protocolo:
        raise ErroAutomacao("Não consegui copiar o protocolo da 1ª linha.")
    if protocolo == ultimo_protocolo:
        raise ErroAutomacao(f"O protocolo {protocolo} apareceu de novo: a lista não avançou.")

    registrar(f"Protocolo copiado: {protocolo}")
    return protocolo


def receber_laudo(protocolo):
    """Clica no ícone verde, visualiza o laudo e confirma o recebimento."""
    pa.click(*POS_ICONE_VERDE)
    aguardar("recebimento_laudo.png", descricao="tela de recebimento do laudo")

    pa.press("end")                          # desce até o fim da página
    pa.click(*POS_VISUALIZAR)                # abre o laudo em uma nova guia
    time.sleep(ESPERA_LAUDO)
    pa.hotkey("ctrl", "1")                   # volta à 1ª guia (sem depender de coordenada)

    pa.click(*POS_RECEBER)
    aguardar_lista()
    registrar(f"Laudo recebido: {protocolo}")


def encaminhar_laudo(protocolo):
    """Pesquisa o protocolo e encaminha para a unidade requisitante (ícone azul)."""
    pyperclip.copy(protocolo)                # garante que o Ctrl+V cole ESTE protocolo
    pa.click(*POS_BUSCA)
    pa.hotkey("ctrl", "a")                   # limpa o que já estiver no campo
    pa.hotkey("ctrl", "v")

    # Confere se o campo de pesquisa realmente ficou com o protocolo
    pyperclip.copy("")
    pa.hotkey("ctrl", "a")
    pa.hotkey("ctrl", "c")
    if pyperclip.paste().strip() != protocolo:
        raise ErroAutomacao("O campo de pesquisa não ficou com o protocolo (clique no lugar errado?).")

    # pa.press("enter")                      # descomente se o site exigir Enter para pesquisar
    time.sleep(ESPERA_FILTRO)                # espera a tabela filtrar

    # O ícone azul só vale se estiver exatamente onde vamos clicar
    aguardar("icone_azul.png", REGIAO_AZUL, "ícone azul (encaminhar)")
    pa.click(*POS_ICONE_AZUL)
    time.sleep(ESPERA_ENCAMINHAR)
    aguardar_lista()
    registrar(f"Laudo encaminhado: {protocolo}")


def processar_laudo(ultimo_protocolo):
    """Recebe e encaminha UM laudo. Retorna o protocolo processado."""
    protocolo = copiar_protocolo(ultimo_protocolo)
    try:
        receber_laudo(protocolo)
        encaminhar_laudo(protocolo)
    except ErroAutomacao as erro:
        raise ErroAutomacao(f"{erro} [protocolo {protocolo}]") from erro
    return protocolo


# ============================== PROGRAMA PRINCIPAL ==============================
def main():
    processados = 0
    ultimo_protocolo = None
    registrar("=== Automação iniciada ===")
    try:
        while MAX_LAUDOS is None or processados < MAX_LAUDOS:
            pa.failSafeCheck()

            # PARADA: ícone vermelho na 1ª linha = acabaram os laudos
            if tem_icone_vermelho():
                avisar("Automação concluída",
                       f"Ícone vermelho encontrado. Laudos processados: {processados}.")
                return

            # SEGURANÇA: só prossegue se o ícone verde estiver onde vamos clicar
            if not tem_icone_verde():
                raise ErroAutomacao("Não vi o ícone verde nem o vermelho na 1ª linha "
                                    "(lista vazia ou tela inesperada).")

            ultimo_protocolo = processar_laudo(ultimo_protocolo)
            processados += 1

        avisar("Teste concluído",
               f"{processados} laudo(s) processado(s). Limite MAX_LAUDOS atingido.")

    except pa.FailSafeException:
        avisar("Automação interrompida", "Failsafe acionado (mouse no canto da tela).")
    except ErroAutomacao as erro:
        avisar("Automação parou",
               f"{erro} Laudos processados: {processados}. Veja {ARQUIVO_LOG}.")
    except KeyboardInterrupt:
        registrar("Interrompido pelo teclado (Ctrl+C).")
    finally:
        registrar("=== Automação finalizada ===")


if __name__ == "__main__":
    print("A automação começa em 5 segundos. Deixe o PericiaNet na lista de laudos.")
    time.sleep(5)
    main()