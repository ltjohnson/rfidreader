import select
import serial
import threading
import time

class RFIDReader(object):
  def __init__(self, port='/dev/ttyUSB0', baudrate=2400, read_delay=1500):
    self.port = port
    self.baudrate = baudrate
    self.read_delay = read_delay
    self.read_thread = None
    self.ser = None
    self.callback = None
    self.__keep_looping = True
    self.thread = None
    self.open_port()

  def __del__(self):
    self.stop_loop()
    self.close_port()

  def open_port(self, port=None, baudrate=None, read_delay=None):
    # Close an existing connection.
    self.close_port()
    if port: self.port = port
    if baudrate: self.buadrate = baudrate
    if read_delay: self.read_delay = read_delay
    self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
    self.ser.nonblocking()
    self.last_read = None

  def close_port(self):
    if self.ser:
      self.ser.close()
    self.ser = None

  def set_callback(self, fun):
    self.callback = fun
  
  def read(self):
    if self.ser is None:
      return None
    if not self.ser.inWaiting():
      return None
    # After a small timeout, read the available bytes.
    time.sleep(0.05) # Would flush be a better thing to do here?
    x = self.ser.read(self.ser.inWaiting())
    if not self.__delay_ok():
      return None
    self.last_read = time.time() * 1000
    # Find the last full id number read.
    rfid_string = self.__convert_string(x)
    if rfid_string and self.callback:
      self.callback(rfid_string)
    return rfid_string

  def __delay_ok(self, now=None):
    if self.last_read is None: 
      return True
    if now is None:
      now = time.time() * 1000
    return now - self.last_read >= self.read_delay

  def __convert_string(self, s):
    s = s.replace('\r', '')
    x = [x for x in s.split('\n') if len(x) == 10]
    return x[len(x) - 1] if x else None

  def __read_loop(self):
    while self.__keep_looping:
      # Wait until there is data to read, timeout is for thread control.
      readable, _, _ = select.select([self.ser.fileno()], [], [], 0.05)
      if readable:
        self.read()
    
  def looping(self):
    return self.thread.is_alive() if self.thread else False

  def stop_loop(self):
    if not self.thread:
      return
    # Set the stop flag and wait until the thread exits.
    self.__keep_looping = False
    self.thread.join()

  def start_loop(self):
    self.stop_loop()
    self.__keep_looping = True
    self.thread = threading.Thread(target=self.__read_loop)
    self.thread.daemon = True
    self.thread.start()
      
     
