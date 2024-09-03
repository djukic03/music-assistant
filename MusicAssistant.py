import speech_recognition as sr
from youtube_search import YoutubeSearch
import webbrowser
from gtts import gTTS
import struct
import pyaudio
import pvporcupine
import os
import time
import vlc
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QMovie, QIcon, QPixmap, QCursor
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal

global num

class MyWindow(QMainWindow):
  def __init__(self):
    super(MyWindow, self).__init__()
    self.setWindowTitle("Đuka muzički asistent")
    self.setFixedSize(500,500)
    self.stoploop = False
    self.initUI()
    
  def initUI(self):
    self.button = QPushButton(self)
    self.button.setFixedSize(200, 200)
    self.button.setStyleSheet("border-radius : 100px; border : 2px solid black")
    self.button.setCursor(QCursor(Qt.PointingHandCursor))
    
    self.mic_off=QPixmap("Slike/mikrofon.png")
    self.mic_on=QMovie("Slike/micanimacija.gif")
    self.mic_on.setScaledSize(QSize(self.button.width(), self.button.height()))

    self.label1 = QLabel(self.button)
    self.label1.setFixedWidth(self.button.width())
    self.label1.setFixedHeight(self.button.height())
    self.label1.setPixmap(self.mic_off.scaled(self.button.width(), self.button.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    self.label2 = QLabel(self)
    self.label2.setText("Pritisnite mikrofon")
    self.label2.setGeometry(0,400,500,20)
    self.label2.setAlignment(Qt.AlignCenter)
    
    self.button.clicked.connect(self.clicked)
    
    self.layout = QHBoxLayout()
    self.layout.addWidget(self.button)

    self.widget = QWidget()
    self.widget.setLayout(self.layout)
    self.setCentralWidget(self.widget)
    
    self.stop = QPushButton(self)
    self.stop.setCursor(QCursor(Qt.PointingHandCursor))
    self.stop.setText("Zaustavi")
    self.stop.setGeometry(390,460,100,30)
    self.stop.clicked.connect(self.stopit)
    
  def clicked(self):
    self.label1.setMovie(self.mic_on)
    self.mic_on.start()  
    self.worker = WorkerThread()
    self.worker.start()
    self.worker.update_progress.connect(self.evit_update_progress)
  
  def evit_update_progress(self, val):
    self.label2.setText(val)
    self.label2.setAlignment(Qt.AlignCenter)

  def stopit(self):
    self.stoploop = True
    self.label1.setMovie(None)
    self.label1.setPixmap(self.mic_off.scaled(self.button.width(), self.button.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
      
    
    
class WorkerThread(QThread):
    update_progress = pyqtSignal(str)
    def run(self):
        try:
            porcupine = pvporcupine.create(access_key="mIsoidSrNKab1jlAhs3hZ5GlItaMW9Z9neH+0qzMyOnCPwxfuc/DUg==", library_path=None,model_path=None, keyword_paths=["keyword.ppn"],keywords=None, sensitivities=[0.5])
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length)
            while not win.stoploop:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0 and win.stoploop==False:
                    tekst="Koju pesmu da pustim?"
                    self.update_progress.emit(tekst)
                    num=1
                    if win.stoploop:
                        break
                    Text_to_Speech(t=tekst, num=num)
                    time.sleep(5)
                    r = sr.Recognizer()
                    with sr.Microphone() as source:
                        if win.stoploop:
                            break
                        r.adjust_for_ambient_noise(source)
                        audio = r.listen(source, phrase_time_limit=5)
                        try:
                            text = r.recognize_google(audio, language="sr-RS",)
                            tekst="Puštam " + text
                            self.update_progress.emit(tekst)
                            num=2
                            if win.stoploop:
                                break
                            Text_to_Speech(t=tekst, num=num)
                            time.sleep(2)
                            results = YoutubeSearch(text, max_results=1).to_dict()
                            video_id = results[0]['url_suffix']
                            video_url =f"https://www.youtube.com/{video_id}"
                            webbrowser.open(video_url)
                        except sr.UnknownValueError:
                            tekst="Izvinite, nisam Vas čuo"
                            self.update_progress.emit(tekst)
                            num=3
                            if win.stoploop:
                                break
                            Text_to_Speech(t=tekst, num=num)
                        except sr.RequestError as e:
                            print(f"Error while connecting to Google Speech Recognition service; {e}")
        finally:
            if porcupine is not None:
                porcupine.delete()
            if audio_stream is not None:
                audio_stream.close()
            if pa is not None:
                pa.terminate()
        win.stoploop = False



class OnMyWatch:
  watchDirectory = "Zvukovi"
  def __init__(self):
    self.observer = Observer()
    
  def run(self, f, tts):
    event_handler = Handler()
    self.observer.schedule(event_handler, self.watchDirectory, recursive = True)
    self.observer.start()
    tts.save(f)
    try:
      while True:
        time.sleep(0.5)
        return
    except:
      self.observer.stop()
    self.observer.join()
    
class Handler(FileSystemEventHandler):
  @staticmethod
  def on_any_event(event):
    if event.is_directory:
      return None
    elif event.event_type == 'modified':
      Player(event.src_path)



class newPlayer(object):
  def __init__(self):
    super(object, self).__init__()
    self.Instance = vlc.Instance()
    self.player = self.Instance.media_player_new()

  def Open(self, f):
    self.Media = self.Instance.media_new_path(f)
    self.player.set_media(self.Media)

  def Play(self):
    self.player.get_media()
    self.player.play()
    time.sleep(3)
    self.player.stop()

def Player(p):
  player=newPlayer()
  player.Open(p)
  player.Play()



def path_choose(num):
  if num==1:
    file="Zvukovi/tts.wav"
  elif num==2:
    file="Zvukovi/pop.wav"
  elif num==3:
    file="Zvukovi/ntc.wav"
  return file

def Text_to_Speech(t, num):
  f=path_choose(num=num)
  tts = gTTS(text=t, lang="bs", slow=False)
  watch = OnMyWatch()
  watch.run(f=f,tts=tts)
  
if __name__=="__main__":
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())
    