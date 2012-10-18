import pygame
import rfidreader
import signal
import sys

# Start pygame mixer.
pygame.init()
pygame.mixer.init()

# Map rfid tags to filenames (songs).
rfid_dict = {'480020087A': 'test1.mp3',
             '52007EEE55': 'test2.mp3'}

# Callback for ctrl-c.
def signal_handler(signal, frame):
  if pygame.mixer.music.get_busy():
    pygame.mixer.music.stop()
  if rdr.looping():
    rdr.stop_looping()
  print ""
  sys.exit(0)

# Callback for rfid tags.  
def play_song_by_rfid(rfid):
  if rfid in rfid_dict:
    pygame.mixer.music.load(rfid_dict[rfid])
    pygame.mixer.music.play()
  else:
    if pygame.mixer.music.get_busy():
      pygame.mixer.music.stop()

# Create reader object, add callback and start the background loop.
rdr = rfidreader.RFIDReader()
rdr.set_callback(play_song_by_rfid)
rdr.start_looping()

# Register handler for Ctrl-C then wait for rfid events or ctrl-c.
signal.signal(signal.SIGINT, signal_handler)
print 'Press Ctrl-C to exit.'
signal.pause()
