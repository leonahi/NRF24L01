import time
import spidev
import numpy as np
import nrf24l01_reg_def as nrf24

import RPi.GPIO as GPIO

SET_TX_ADDR = [nrf24.ADDRESS, nrf24.ADDRESS, nrf24.ADDRESS, nrf24.ADDRESS, nrf24.ADDRESS]
READ_CONFIG = [nrf24.ADDRESS, '0xFF']

#spi = spidev.SpiDev()
#spi.open(0,0)

class RadioNRF24:
    def __init__(self, GPIO_CE_PIN):
        self.nrf24_spi = spidev.SpiDev() 
        self.nrf24_spi.open(0,0)
        self.small_pause = 0.05
        self.long_pause = 0.5
    
    def __nrf24_do_spi_operation(self, operation):
        return self.nrf24_spi.xfer(operation)
    
    def nrf24_setup_radio(self):
        pass
    
    def nrf24_read_reg(self, REGISTER, num_bytes):
        byte_list = [REGISTER | nrf24.R_REGISTER]
        for i in range(num_bytes):
            byte_list.append(nrf24.NOP)
        print(self.__nrf24_do_spi_operation(byte_list))    
    
    def nrf24_receive_data(self):
        pass
    
    def nrf24_send_data(self):
        pass
    
    def __del__(self):
        self.nrf24_spi.close()

def main():
    
    nrf_radio = RadioNRF24(18)
    nrf_radio.nrf24_read_reg(nrf24.CONFIG, 1)
    
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
    #resp = spi.xfer([nrf24.EN_RXADDR | nrf24.R_REGISTER, 0xFF])
    
    #print(resp)
    
    #resp = spi.xfer(SET_TX_ADDR)
    #print(resp)
    
    #spi.close()
    
    del nrf_radio

if __name__ == "__main__":
    main()