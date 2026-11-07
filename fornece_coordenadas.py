#CÓDIGO PARA VERIFICAR A COORDENADA, ALTURA E LARGURA DO ÍCONE
#
#from mouseinfo import mouseInfo
#mouseInfo()

import pyautogui as pa
import time

coordenadas = pa.locateOnScreen("recebimento_laudo.png", confidence=0.7)

print(coordenadas)