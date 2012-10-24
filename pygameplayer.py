import csv
import pygame
import random
import threading

def read_tagslist(filename="tags.csv"):
  with open(filename, 'rb') as f:
    tags = dict([x[0], x[1:]] for x in csv.reader(f))
  return tags
  
def write_tagslist(tags, filename="tags.csv"):
  with open(filename, 'wb') as f:
    writer = csv.writer(f)
    for k in tags: 
      writer.writerow([k] + tags[k])

class Player(object):
  PLAYING = 1
  PAUSED = 2
  STOPPED = 3
  STOP_EVENT = pygame.USEREVENT + 1
  
  def __init__(self, filename=None):
    # Start pygame mixer, set the end event.
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.set_endevent(Player.STOP_EVENT)
    self.pos = -1
    self.state = Player.STOPPED
    self.playlist = None
    if filename:
      self.read_playlist(filename)
    self.__start_pygameloop()

  def __del__(self):
    pygame.event.post(pygame.event.Event(pygame.QUIT))

  def __start_pygameloop(self):
    self.thread = threading.Thread(target=self.__pygameloop)
    self.thread.daemon = True
    self.thread.start()

  def __pygameloop(self):
    running = 1
    while running:
      event = pygame.event.wait()
      if event.type == pygame.QUIT:
        running = 0
      elif event.type == Player.STOP_EVENT:
        self.play(pos=self.pos + 1)

  def read_playlist(self, filename="playlist.csv"):
    with open(filename, 'rb') as f:
      self.playlist = list(x for x in csv.reader(f))
    print "Read %d songs" % len(self.playlist)
    
  def play_random(self):
    if self.playlist:
      self.play(pos = random.randint(0, len(self.playlist) - 1))

  def play(self, song=None, playlist=None, album=None, pos=None):
    # Note, playlist and album are currently annoyed.
    if self.state == Player.PAUSED:
      return self.pause()
    if pos is None and song is None:
      if self.state == Player.STOPPED:
        pos = 0
      else:
        return -1
    if song:
      pos_list = [i for i, x in enumerate(self.playlist) if x[0] == song]
      if pos_list:
        pos = pos_list[0]
      else:
        return -1
    if pos >= len(self.playlist):
      self.state, self.pos = Player.STOPPED, len(self.playlist)
      return -1
    self.state, self.pos = Player.PLAYING, pos
    print "Playing song %s" % self.playlist[pos][1]
    pygame.mixer.music.load(self.playlist[pos][1])
    pygame.mixer.music.play()
    return pos

  def stop(self):
    if pygame.mixer.music.get_busy():
      pygame.mixer.music.stop()
    self.state = Player.STOPPED

  def pause(self):
    if self.state == Player.PLAYING and pygame.mixer.music.get_busy():
      pygame.mixer.music.pause()
      self.state = Player.PAUSED
    elif self.state == Player.PAUSED:
      pygame.mixer.music.unpause()
      self.state = Player.PLAYING
