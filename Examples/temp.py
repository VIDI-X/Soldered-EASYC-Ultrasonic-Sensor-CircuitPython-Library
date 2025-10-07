import board
import time
import analogio

PinTemp = analogio.AnalogIn(board.GPIO26)

print(PinTemp.reference_voltage)   # referentna vrijednost 
print("\n")

while True:
    temp = PinTemp.value   # ocitana analogna vrijednost
    print("Temperatura: " + str(temp))
    
    # analogna vrijednost pretvorena u milivolte (mV)
    tempV = temp * (PinTemp.reference_voltage * 1000 / 65535)
    print("Temperatura u mV: " + str(tempV))
    
    # mV pretvoreni u stupnjeve Celzijuseve
    tempC = (tempV - 500) / 10
    print("Temperatura u stupnjevima C: " + str(tempC))
    
    time.sleep(0.5)
