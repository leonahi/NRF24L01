import time
import spidev
import numpy as np
import nrf24l01_reg_def as nrf24

import RPi.GPIO as GPIO

class RadioNRF24:
    def __init__(self, mode='SENDER', payload_size=3, rx_pipe=0, data_rate='1MBPS', gpio_ce_pin=16):
        self.nrf24_spi = spidev.SpiDev() 
        self.nrf24_spi.open(0,0)
        self.nrf24_CE_PIN = gpio_ce_pin
        self.nrf24_small_pause = 0.05
        self.nrf24_long_pause = 0.5
        
        # decide rx pipe for payload
        self.nrf24_REG_RX_PW_Px = (nrf24.RX_PW_P0 + rx_pipe)  # rx_pipe decides which rx pipe number
        self.nrf24_SET_RX_PW_Px_PAYLOAD_SIZE = payload_size
        
        # enable rx pipe 
        self.nrf24_SET_EN_RXADDR_ERX_Px = (1 << rx_pipe)
        
        self.nrf24_SETUP_RETR_SET_ACK_RETR       = 0x2F  # 15 retries, 750us paus in between in auto ack
        self.nrf24_SETUP_AW_SET_ADR_WIDTH        = 0x03  # 5 bytes address width
        self.nrf24_SETUP_RF_CH_SET_FREQ          = 0x01  # Set channel freq to 2.401 MHz
        
        self.nrf24_SETUP_RX_ADDR_SET_P0_ADDRESS  = [0x12, 0x12, 0x12, 0x12, 0x12]
        self.nrf24_SETUP_TX_ADDR_SET_ADDRESS     = [0x12, 0x12, 0x12, 0x12, 0x12]        
        
        if data_rate is '1MBPS':
            self.nrf24_SETUP_RF_SETUP = ( (0x03 << nrf24.RF_SETUP_RF_PWR) | (0x00 << nrf24.RF_SETUP_RF_DR_HIGH) )  # 1 Mbps data rate
        elif data_rate is '2MBPS':
            self.nrf24_SETUP_RF_SETUP = ( (0x03 << nrf24.RF_SETUP_RF_PWR) | (0x01 << nrf24.RF_SETUP_RF_DR_HIGH) )  # 2 Mbps data rate
        else:
            self.nrf24_SETUP_RF_SETUP = ( (0x03 << nrf24.RF_SETUP_RF_PWR) | (0x01 << nrf24.RF_SETUP_RF_DR_LOW) )  # 250kbps data rate 
        
        if mode == 'RECEIVER':
            self.nrf24_SETUP_CONFIG = 0x1F  # Sender
        elif mode == 'SENDER':
            self.nrf24_SETUP_CONFIG = 0x1E  # Receiver
        
        self.nrf24_RESET_STATUS = 0x70
    
    def __nrf24_do_spi_operation(self, operation):
        return self.nrf24_spi.xfer(operation)
    
    def nrf24_setup_radio(self):
        # Setup EN_AA - Enable Auto Ack
        byte_list = [nrf24.EN_AA | nrf24.W_REGISTER]
        byte_list.append((1 << nrf24.ENAA_P0))
        self.__nrf24_do_spi_operation(byte_list)
             
        byte_list = [nrf24.SETUP_RETR | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_RETR_SET_ACK_RETR)
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup EN_RXADDR
        byte_list = [nrf24.EN_RXADDR | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SET_EN_RXADDR_ERX_Px)  # Enable data pipe 0
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup address width
        byte_list = [nrf24.SETUP_AW | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_AW_SET_ADR_WIDTH)  # 5 bytes address width 
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup Radio Freq
        byte_list = [nrf24.RF_CH | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_RF_CH_SET_FREQ)  # set freq to 2.401 MHz 
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup data rate and power
        byte_list = [nrf24.RF_SETUP | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_RF_SETUP)  # data rate 1 Mbps 
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup RX address pipe 0
        byte_list = [nrf24.RX_ADDR_P0 | nrf24.W_REGISTER]
        byte_list.extend(self.nrf24_SETUP_RX_ADDR_SET_P0_ADDRESS)  # set rx pipe 0 address to 0x1212121212 
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup TX address
        byte_list = [nrf24.TX_ADDR | nrf24.W_REGISTER]
        byte_list.extend(self.nrf24_SETUP_TX_ADDR_SET_ADDRESS)  # set rx pipe 0 address to 0x1212121212 
        self.__nrf24_do_spi_operation(byte_list)
    
        # Setup RX payload for pipe
        byte_list = [self.nrf24_REG_RX_PW_Px | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SET_RX_PW_Px_PAYLOAD_SIZE)  # payload_size bytes payload RX pipe = rx_pipe
        self.__nrf24_do_spi_operation(byte_list)
        
        # Setup CONFIG register
        byte_list = [nrf24.CONFIG | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_SETUP_CONFIG)
        self.__nrf24_do_spi_operation(byte_list)
    
    
    def nrf24_read_reg(self, REGISTER, num_bytes):
        byte_list = [REGISTER | nrf24.R_REGISTER]
        for i in range(num_bytes):
            byte_list.append(nrf24.NOP)
        return self.__nrf24_do_spi_operation(byte_list)       
    
    def nrf24_change_address(self, tx_rx_address):
        byte_list = [nrf24.RX_ADDR_P0 | nrf24.W_REGISTER]
        byte_list.extend(tx_rx_address)  # set rx pipe 0 address 
        self.__nrf24_do_spi_operation(byte_list)
        
        byte_list = [nrf24.TX_ADDR | nrf24.W_REGISTER]
        byte_list.extend(tx_rx_address)  # set tx address
        self.__nrf24_do_spi_operation(byte_list)
        
    def nrf24_change_radio_mode(self, md):
        byte_list = [nrf24.CONFIG | nrf24.W_REGISTER]
        if md is 'tx':
            byte_list.append(0x0E)
        elif md is 'rx':
            byte_list.append(0x0F)
        self.__nrf24_do_spi_operation(byte_list)
    
    def nrf24_en_auto_ack(self, pipe_number):
        byte_list = [nrf24.EN_AA | nrf24.W_REGISTER]
        byte_list.append((1 << pipe_number))
        self.__nrf24_do_spi_operation(byte_list)
    
    def nrf24_flush_tx_fifo(self):
        self.__nrf24_do_spi_operation([nrf24.FLUSH_TX])
    
    def nrf24_flush_rx_fifo(self):
        self.__nrf24_do_spi_operation([nrf24.FLUSH_RX])
        
    def nrf24_write_tx_fifo(self, tx_payload):
        byte_list = [nrf24.W_TX_PAYLOAD]
        byte_list.extend(tx_payload)
        self.__nrf24_do_spi_operation(byte_list)
    
    def nrf24_read_rx_fifo(self, payload_length):
        return self.nrf24_read_reg(nrf24.R_RX_PAYLOAD, payload_length)
    
    def nrf24_reset_status(self):
        byte_list = [nrf24.STATUS | nrf24.W_REGISTER]
        byte_list.append(self.nrf24_RESET_STATUS)
        self.__nrf24_do_spi_operation(byte_list)        
    
    def nrf24_enter_transceiver_mode(self):
        try:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.nrf24_CE_PIN, GPIO.OUT)
            GPIO.output(self.nrf24_CE_PIN, True)
            #time.sleep(self.nrf24_long_pause)
            time.sleep(.05)
            GPIO.output(self.nrf24_CE_PIN, False)
            time.sleep(self.nrf24_small_pause)
            GPIO.cleanup()
        except(KeyboardInterrupt, SystemExit):
            try:
                GPIO.cleanup()
                print("GPIO CE pin closed!!")
            except:
                pass
            raise

    def nrf24_receive_data(self):
        self.nrf24_reset_status()
        self.nrf24_flush_rx_fifo()
        
        print("STATUS : {0}".format(self.nrf24_read_reg(nrf24.STATUS, 0)))
        print("FIFO Status : {0}\n".format(self.nrf24_read_reg(nrf24.FIFO_STATUS, 1)))
        
        self.nrf24_enter_transceiver_mode()
        
        while 1:
            status = self.nrf24_read_reg(nrf24.STATUS, 0)[0]
            if status & 0x40 == 0x40:
                break
            time.sleep(.2)
        
        print("STATUS : {0}".format(self.nrf24_read_reg(nrf24.STATUS, 0)))
        print("Payload : {0}\n".format(self.nrf24_read_rx_fifo(3)))
        print("FIFO Status : {0}\n".format(self.nrf24_read_reg(nrf24.FIFO_STATUS, 1)))
            
    def nrf24_send_data(self, tx_payload=None):
        self.nrf24_reset_status()
        
        # flush TX FIFO
        self.nrf24_flush_tx_fifo()
        
        # debug - print status before transmission
        print("STATUS : {0}".format(self.nrf24_read_reg(nrf24.STATUS, 0)))
        print("FIFO status : {0}\n".format(self.nrf24_read_reg(nrf24.FIFO_STATUS, 1)))
        
        # debug - print receiver address
        print(self.nrf24_read_reg(nrf24.RX_ADDR_P0, 5))
        
        # write to send into TX buffer
        self.nrf24_write_tx_fifo([21, 29, 6])
        
        print("FIFO status : {0}\n".format(self.nrf24_read_reg(nrf24.FIFO_STATUS, 1)))
        
        self.nrf24_enter_transceiver_mode()
        
        # debug - print status before transmission
        print("STATUS : {0}".format(self.nrf24_read_reg(nrf24.STATUS, 0)))      
    
    def __del__(self):
        self.nrf24_spi.close()

def main():
    
    nrf_radio = RadioNRF24(mode='RECEIVER')
    nrf_radio.nrf24_setup_radio()
    
    print("\nAck enable for rx pipe...")
    print( hex(nrf_radio.nrf24_read_reg(nrf24.EN_AA, 1)[1]) )   
    
    print('\nNumber of retry and retry interval...')
    print( hex(nrf_radio.nrf24_read_reg(nrf24.SETUP_RETR, 1)[1]) )  
    
    print('\nRX pipe number...')
    print( hex(nrf_radio.nrf24_read_reg(nrf24.EN_RXADDR, 1)[1]) )   
    
    print('\nAddress width...')
    print( hex(nrf_radio.nrf24_read_reg(nrf24.SETUP_AW, 1)[1]) )   
    
    print('\nRF Channel freq...')
    print( hex(nrf_radio.nrf24_read_reg(nrf24.RF_CH, 1)[1]) )  
    
    print('\nRF_SETUP...')
    print( hex(nrf_radio.nrf24_read_reg(nrf24.RF_SETUP, 1)[1]) )   
    
    print('\nRX Address...')
    print(nrf_radio.nrf24_read_reg(nrf24.RX_ADDR_P0, 5)) 
    
    print('\nTX Address...')
    print(nrf_radio.nrf24_read_reg(nrf24.TX_ADDR, 5))
    
    print('\nPayload...')
    print( hex(nrf_radio.nrf24_read_reg(nrf24.RX_PW_P0, 1)[1]) )
    
    print('\nCONFIG register')
    print( hex(nrf_radio.nrf24_read_reg(nrf24.CONFIG, 1)[1]) )   
    
    #print("{0:b}".format(nrf_radio.nrf24_read_reg(nrf24.STATUS, 0)[0]))
    #print(hex(nrf_radio.nrf24_read_reg(nrf24.STATUS, 0)[0]))
    
    #print("Sending data....")
    #nrf_radio.nrf24_send_data();
    
    #print(nrf_radio.nrf24_read_reg(nrf24.FIFO_STATUS, 1))
    
    
    mode = "sender"
    
    if mode is "receiver":
        print("Receiving Data....\n\n")
        nrf_radio.nrf24_change_radio_mode('rx')
        while(1):
            nrf_radio.nrf24_receive_data()
            time.sleep(nrf_radio.nrf24_long_pause)
    else:
        print("Sendind Data....\n\n")
        nrf_radio.nrf24_change_radio_mode('tx')
        nrf_radio.nrf24_send_data()
        time.sleep(nrf_radio.nrf24_long_pause)
        
    del nrf_radio

if __name__ == "__main__":
    main()
