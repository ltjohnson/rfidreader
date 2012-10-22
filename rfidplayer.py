import csv
import pygameplayer
import rfidreader
import signal
import sys

class TagAction(object):
  def __init__(self, l):
    self.tag_id = None
    self.action = None
    self.song = None
    if l:
      self.tag_id = l[0]
      self.action = l[1]
      if len(l) > 2:
        self.song = l[2]

def read_tagslist(filename="tags.csv"):
  with open(filename, 'rb') as f:
    tags = dict([x[0], TagAction(x)] for x in csv.reader(f))
  return tags
  
def write_tagslist(tags, filename="tags.csv"):
  with open(filename, 'wb') as f:
    writer = csv.writer(f)
    for k in tags: 
      tag = tags[k]
      writer.writerow([tags[k].tag_id, tags[k].action, tags[k].song])

def tag_callback(tag_id):
  if not tag_id in tags:
    print "[%s] UNKNOWN" % tag_id
    return
  tag = tags[tag_id]
  print "[%s] %s" % (tag_id, tag.action),
  if tag.action == "stop":
    player.stop()
  elif tag.action == "play":
    player.play()
  elif tag.action == "pause":
    player.pause()
  elif tag.action == "random":
    player.play_random()
  elif tag.action == "song":
    player.play(song=tag.song)
    print "%s" % tag.song,
  else:
    print "UNKNOWN ACTION",
  print

def signal_handler(signal, frame):
  print ""
  sys.exit(0)
   
### startup ####
rdr = None
player = None

if __name__ == '__main__':
  print 'Press Ctrl-C to exit.'

  tags = read_tagslist('tags.csv')

  rdr = rfidreader.RFIDReader()
  rdr.set_callback(tag_callback)
  rdr.start_looping()

  player = pygameplayer.Player('playlist.csv')

  signal.signal(signal.SIGINT, signal_handler)
  signal.pause()
