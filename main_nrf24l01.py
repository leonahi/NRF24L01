import time
import spidev
import numpy as np
import nrf24l01_reg_def as nrf24

import RPi.GPIO as GPIO

class RadioNRF24:
    def __init__(self, GPIO_CE_PIN):
        self.nrf24_spi = spidev.SpiDev() 
        self.nrf24_spi.open(0,1)
        self.nrf24_ce_pin = GPIO_CE_PIN
        self.nrf24_small_pause = 0.05
        self.nrf24_long_pause = 0.5
        
        self.nrf24_SETUP_RETR_SET_ACK_RETR       = 0x2F  # 15 retries, 750us paus in between in auto ack
        self.nrf24_SETUP_AW_SET_ADR_WIDTH        = 0x03  # 5 bytes address width
        self.nrf24_SETUP_RF_CH_SET_FREQ          = 0x01  # Set channel freq to 2.401 MHz
        self.nrf24_SETUP_RF_SETUP_SET_DR_PWR     = 0x07  # Data Rate 1 Mbps
        self.nrf24_SETUP_RX_ADDR_SET_P0_ADDRESS  = [0x12, 0x12, 0x12, 0x12, 0x12]
        self.nrf24_SETUP_TX_ADDR_SET_ADDRESS     = [0x12, 0x12, 0x12, 0x12, 0x12]
        self.nrf24_SETUP_RX_PW_P0_SET_PAYLOAD_S  = 0x03  # 3 byte payload
        self.nrf24_SETUP_CONFIG                  = 0x1E
        
        self.nrf24_RESET_STATUS = 0x70
    
    def __nrf24_do_spi_operation(self, operation):
        return self.nrf24_spi.xfer(operation)
    
    def nrf24_setup_radio(self):
        # Setup EN_AA - Enable Auto Ack
        #byte_list = [nrf24.EN_AA | nrf24.W_REGISTER]
        #byte_list.append((1 << nrf24.ENAA_P0))
        #self.__nrf24_do_spi_operation(byte_list)
             
        byte_list = [nrf24.SETUP_RETR | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_RETR_SET_ACK_RETR)
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup EN_RXADDR
        byte_list = [nrf24.EN_RXADDR | nrf24.W_REGISTER]
        byte_list.append(1 << nrf24.ERX_P0)                 # Enable data pipe 0
        self.__nrf24_do_spi_operation(byte_list)
        
        byte_list = [nrf24.SETUP_AW | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_AW_SET_ADR_WIDTH)  # 5 bytes address width 
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup Radio Freq
        byte_list = [nrf24.RF_CH | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_RF_CH_SET_FREQ)  # set freq to 2.401 MHz 
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup data rate and power
        byte_list = [nrf24.RF_SETUP | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_RF_SETUP_SET_DR_PWR)  # data rate 1 Mbps 
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup RX address pipe 0
        byte_list = [nrf24.RX_ADDR_P0 | nrf24.W_REGISTER]
        byte_list.extend(self.nrf24_SETUP_RX_ADDR_SET_P0_ADDRESS)  # set rx pipe 0 address to 0x1212121212 
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup TX address
        byte_list = [nrf24.TX_ADDR | nrf24.W_REGISTER]
        byte_list.extend(self.nrf24_SETUP_TX_ADDR_SET_ADDRESS)  # set rx pipe 0 address to 0x1212121212 
        self.__nrf24_do_spi_operation(byte_list)
    
        # Setup RX payload for pipe 0
        byte_list = [nrf24.RX_PW_P0 | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_RX_PW_P0_SET_PAYLOAD_S)  # 3 bytes payload RX pipe 0
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup CONFIG register
        byte_list = [nrf24.CONFIG | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_CONFIG)  # 3 bytes payload RX pipe 0
        self.__nrf24_do_spi_operation(byte_list)
    
    
    def nrf24_read_reg(self, REGISTER, num_bytes):
        byte_list = [REGISTER | nrf24.R_REGISTER]
        for i in range(num_bytes):
            byte_list.append(nrf24.NOP)
        return self.__nrf24_do_spi_operation(byte_list)          
    
    def nrf24_receive_data(self):
        # reset status register
        byte_list = [nrf24.STATUS | nrf24.W_REGISTER]
        byte_list.append(( (1 << nrf24.MAX_RT) | (1 << nrf24.TX_DS) | (1 << nrf24.RX_DR) ))  # reset status 
        self.__nrf24_do_spi_operation(byte_list)
        
        try:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.nrf24_ce_pin, GPIO.OUT)
            GPIO.output(self.nrf24_ce_pin, True)
            time.sleep(self.nrf24_long_pause)
            GPIO.output(self.nrf24_ce_pin, False)
            time.sleep(self.nrf24_small_pause)
            GPIO.cleanup()
        except(KeyboardInterrupt, SystemExit):
            try:
                GPIO.cleanup()
                print("GPIO CE pin closed!!")
            except:
                pass
            raise
        
        status_reg = self.nrf24_read_reg(nrf24.STATUS, 0)
            
    
    def nrf24_send_data(self, tx_payload=None):
        # reset status register
        byte_list = [nrf24.STATUS | nrf24.W_REGISTER]
        byte_list.append(( (1 << nrf24.MAX_RT) | (1 << nrf24.TX_DS) | (1 << nrf24.RX_DR) ))  # reset status 
        self.__nrf24_do_spi_operation(byte_list)
        
        # flush TX FIFO
        self.__nrf24_do_spi_operation([nrf24.FLUSH_TX])
        
        # debug - print status before transmission
        print(self.nrf24_read_reg(nrf24.STATUS, 0))
        
        # debug - print receiver address
        print(self.nrf24_read_reg(nrf24.RX_ADDR_P0, 5))
        
        # write to send into TX buffer
        tx_payload = [48, 48, 48]
        byte_list = [nrf24.W_TX_PAYLOAD]
        byte_list.extend(tx_payload)
        self.__nrf24_do_spi_operation(byte_list)
        
        print(self.nrf24_read_reg(nrf24.FIFO_STATUS, 1))
        
        try:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.nrf24_ce_pin, GPIO.OUT)
            GPIO.output(self.nrf24_ce_pin, True)
            #time.sleep(self.nrf24_long_pause)
            time.sleep(.05)
            GPIO.output(self.nrf24_ce_pin, False)
            time.sleep(self.nrf24_small_pause)
            GPIO.cleanup()
        except(KeyboardInterrupt, SystemExit):
            try:
                GPIO.cleanup()
                print("GPIO CE pin closed!!")
            except:
                pass
            raise
        
        # debug - print status before transmission
        print(self.nrf24_read_reg(nrf24.STATUS, 0))
        
        
    
    def __del__(self):
        self.nrf24_spi.close()

def main():
    
    nrf_radio = RadioNRF24(16)
    nrf_radio.nrf24_setup_radio()
    print(nrf_radio.nrf24_read_reg(nrf24.EN_AA, 1))
    print(nrf_radio.nrf24_read_reg(nrf24.SETUP_RETR, 1))
    print(nrf_radio.nrf24_read_reg(nrf24.EN_RXADDR, 1))
    print(nrf_radio.nrf24_read_reg(nrf24.SETUP_AW, 1))
    print(nrf_radio.nrf24_read_reg(nrf24.RF_CH, 1))
    print(nrf_radio.nrf24_read_reg(nrf24.RF_SETUP, 1))
    print(nrf_radio.nrf24_read_reg(nrf24.RX_ADDR_P0, 5))
    print(nrf_radio.nrf24_read_reg(nrf24.TX_ADDR, 5))
    print(nrf_radio.nrf24_read_reg(nrf24.RX_PW_P0, 1))
    print(nrf_radio.nrf24_read_reg(nrf24.CONFIG, 1))
    print("{0:b}".format(nrf_radio.nrf24_read_reg(nrf24.STATUS, 0)[0]))
    print(hex(nrf_radio.nrf24_read_reg(nrf24.STATUS, 0)[0]))
    
    print("Sending data....")
    nrf_radio.nrf24_send_data();
    
    print(nrf_radio.nrf24_read_reg(nrf24.FIFO_STATUS, 1))
    
    """
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(16, GPIO.OUT)
    GPIO.output(16, 1)
    time.sleep(10)
    GPIO.output(16, 0)
    time.sleep(5)
    GPIO.output(16, 1)
    time.sleep(5)
    GPIO.cleanup()
    time.sleep(5)
    """
    
    del nrf_radio

if __name__ == "__main__":
    main()