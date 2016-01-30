import time
import spidev
import numpy as np
import nrf24l01_reg_def as nrf24

#import RPi.GPIO as GPIO

SET_TX_ADDR = [nrf24.ADDRESS, nrf24.ADDRESS, nrf24.ADDRESS, nrf24.ADDRESS, nrf24.ADDRESS]
READ_CONFIG = [nrf24.ADDRESS, '0xFF']

spi = spidev.SpiDev()
spi.open(0,0)

def main():
    """
    print((nrf24.TX_ADDR | nrf24.WRITE_REG))
    resp = spi.xfer([nrf24.TX_ADDR | nrf24.WRITE_REG])
    print(resp)
    
    resp = spi.xfer(SET_TX_ADDR)
    print(resp)
    
    resp = spi.xfer([nrf24.TX_ADDR | nrf24.READ_REG])
    print(resp)
    
    resp = spi.xfer(SET_TX_ADDR)
    print(resp)
    """
    
    #resp = spi.xfer([nrf24.CONFIG | nrf24.R_REGISTER, 0xFF])
    #resp = spi.xfer([nrf24.EN_AA | nrf24.R_REGISTER, 0xFF])
    resp = spi.xfer([nrf24.EN_RXADDR | nrf24.R_REGISTER, 0xFF])
    
    print(resp)
    
    #resp = spi.xfer(SET_TX_ADDR)
    #print(resp)
    
    spi.close()

if __name__ == "__main__":
    main()