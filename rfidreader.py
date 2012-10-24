import re
import select
import serial
import threading
import time

class RFIDReader(object):
  __TO_OPEN  = 1
  __TO_CLOSE = 2
  __CLOSED   = 3
  __OPEN     = 4

  __MAX_PORT = 10

  def __init__(self, port='/dev/ttyUSB0', baudrate=2400, read_delay=1500, 
               same_tag_delay=4000):
    self.port = port
    self.baudrate = baudrate
    self.read_delay = read_delay
    self.same_tag_delay = same_tag_delay
    self.last_tag = None
    self.last_tag_time = None
    self.read_thread = None
    self.ser = None
    self.callback = None
    self.__threads = {}
    self.__port_status = RFIDReader.__TO_OPEN
    self.__open_failed = False
    self.__start_read_thread()
    self.__start_open_thread()


  def __del__(self):
    self.close_port()
    for thread_name in self.__threads:
      self.__stop_thread(thread_name)

  def open_port(self, port=None, baudrate=None, read_delay=None):
    # Close an existing connection.
    self.close_port()
    if port: self.port = port
    if baudrate: self.buadrate = baudrate
    if read_delay: self.read_delay = read_delay
    self.__port_status = RFIDReader.__TO_OPEN

  def __open_port(self):
    self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
    self.ser.nonblocking()
    self.last_read = None
    self.__port_status = RFIDReader.__OPEN

  def close_port(self):
    self.__port_status = RFIDReader.__TO_CLOSE
    if self.ser:
      self.ser.close()
    self.ser = None
    self.__port_status = RFIDReader.__CLOSED

  def set_callback(self, fun):
    self.callback = fun
  
  def __read(self):
    if self.ser is None:
      return None
    if not self.ser.inWaiting():
      return None
    # After a small timeout, read the available bytes.
    time.sleep(0.05) # Would flush be a better thing to do here?
    x = self.ser.read(self.ser.inWaiting())
    rfid_string = self.__convert_string(x)
    now = time.time() * 1000
    if not self.__delay_ok(now) or self.__tag_repeat(rfid_string, now):
      return None
    if rfid_string and self.callback:
      self.callback(rfid_string)
    return rfid_string

  def __delay_ok(self, now=None):
    now = now if now else time.time() * 1000
    if self.last_read is None:
      self.last_read = now - 2 * self.read_delay
    if now - self.last_read >= self.read_delay:
      self.last_read = now
      return True
    else:
      return False

  def __tag_repeat(self, tag, now=None):
    if now is None:
      now = time.time() * 1000
    if self.last_tag and self.last_tag == tag:
      if now - self.last_tag_time < self.same_tag_delay:
        return True
      self.last_tag_time = now
      return False
    else:
      self.last_tag = tag
      self.last_tag_time = now
      return False

  def __convert_string(self, s):
    s = s.replace('\r', '')
    x = [x for x in s.split('\n') if len(x) == 10]
    return x[len(x) - 1] if x else None

  def __open_thread(self):
    while self.__threads['open_loop']['keep_looping']:
      if self.__port_status == RFIDReader.__TO_OPEN:
        try:
          self.__open_port()
        except serial.serialutil.SerialException:
          if self.__open_failed:
            # We've already failed to open at least once, let's try cycling
            # through ports.
            port_num = int(re.sub(r'[^0-9]', '', self.port))
            port_num = (port_num + 1) % (RFIDReader.__MAX_PORT + 1)
            self.port = "%s%d" % (re.sub(r'[0-9]', '', self.port), port_num)
          self.__open_failed = True
        else:
          self.__open_failed = False
        time.sleep(0.05)
      time.sleep(0.05)

  def __read_thread(self):
    while self.__threads['read_loop']['keep_looping']:
      if self.ser is None:
        time.sleep(0.10)
      else:
        # Wait until there is data to read, timeout is for thread control.
        try:
          readable, _, _ = select.select([self.ser.fileno()], [], [], 0.05)
          if readable:
            self.__read()
        except IOError:
          # Reading failed, assume port is closed.
          self.ser = None
          self.__port_status = RFIDReader.__TO_OPEN
    
  def __stop_thread(self, thread_name):
    if thread_name not in self.__threads:
      return
    self.__threads[thread_name]['keep_looping'] = False
    self.__threads[thread_name]['thread'].join()
    del self.__threads[thread_name]
    
  def __start_thread(self, thread, thread_name):
    self.__stop_thread(thread_name)
    self.__threads[thread_name] = {'thread': thread, 'keep_looping': True}
    self.__threads[thread_name]['thread'].daemon = True
    self.__threads[thread_name]['thread'].start()

  def __start_read_thread(self):
    thread = threading.Thread(target=self.__read_thread)
    self.__start_thread(thread, 'read_loop')
    
  def __start_open_thread(self):
    thread = threading.Thread(target=self.__open_thread)
    self.__start_thread(thread, 'open_loop')
     
