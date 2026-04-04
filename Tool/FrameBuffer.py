import threading
import time
import collections
import cv2
import win32gui, win32ui, win32con, win32api
import numpy as np
import tensorflow as tf
from Tool.GameProfile import get_active_profile

class FrameBuffer(threading.Thread):
  def __init__(self, threadID, name, width,height,  maxlen=5, station_size=None, window_title=None):
    threading.Thread.__init__(self)
    self.threadID = threadID
    self.name = name
    self.buffer = collections.deque(maxlen=maxlen)
    self.lock = threading.Lock()

    profile = get_active_profile()
    self.station_size = station_size if station_size is not None else profile.station_size
    self.WIDTH = width
    self.HEIGHT = height
    self._stop_event = threading.Event()
    
    active_window_title = window_title if window_title is not None else profile.window_title
    self.hwnd = win32gui.FindWindow(None, active_window_title)
    self.left,self.top,x2,y2 = self.station_size
    self.width = x2 - self.left + 1
    self.height = y2 - self.top + 1

    self.hwindc = win32gui.GetWindowDC(self.hwnd)
    self.srcdc = win32ui.CreateDCFromHandle(self.hwindc)
    self.memdc = self.srcdc.CreateCompatibleDC()
    self.bmp = win32ui.CreateBitmap()
    self.bmp.CreateCompatibleBitmap(self.srcdc, self.width, self.height)


  def run(self):
    while not self.stopped():
      self.get_frame()
      time.sleep(0.05)
    self.srcdc.DeleteDC()
    self.memdc.DeleteDC()
    win32gui.ReleaseDC(self.hwnd, self.hwindc)
    win32gui.DeleteObject(self.bmp.GetHandle())

  def get_frame(self):
    self.lock.acquire(blocking=True)
    station = cv2.resize(cv2.cvtColor(self.grab_screen(), cv2.COLOR_RGBA2RGB),(self.WIDTH,self.HEIGHT))
    self.buffer.append(tf.convert_to_tensor(station))
    self.lock.release()

  def get_buffer(self):
    stations = []
    self.lock.acquire(blocking=True)
    for f in self.buffer:
      stations.append(f)
    self.lock.release()
    return stations

  def stop(self):
    self._stop_event.set()
 
  def stopped(self):
    return self._stop_event.is_set()

  def grab_screen(self):
    self.memdc.SelectObject(self.bmp)
    self.memdc.BitBlt((0, 0), (self.width, self.height), self.srcdc, (self.left, self.top), win32con.SRCCOPY)
    
    signedIntsArray = self.bmp.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (self.height,self.width,4)

    

    return img
