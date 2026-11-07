#CÓDIGO DE TESTE PARA VERIFICAR A QUESTÃO DA VELOCIDADE MÁXIMA DO CÓDIGO 
#E ÁREA DE CAPTURA

import pyautogui as pa
from time import sleep

pa.FAILSAFE = True
pa.PAUSE = 0.3

while True:
    try:
        icone = pa.locateOnScreen(
            "recebimento_laudo.png",
            confidence=0.7
        )
    except pa.ImageNotFoundException:
        icone = None

    if icone is not None:
        print("Encontrado!!!")
        break 
        
