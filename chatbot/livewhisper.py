#!/usr/bin/env python3
import whisper, os
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
# from model import handle_conversation
import sys
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import translators as ts
# from ui import get_template

# This is my attempt to make psuedo-live transcription of speech using Whisper.
# Since my system can't use pyaudio, I'm using sounddevice instead.
# This terminal implementation can run standalone or imported for assistant.py
# by Nik Stromberg - nikorasu85@gmail.com - MIT 2022 - copilot

Model = 'small'     # Whisper model size (tiny, base, small, medium, large)
English = False      # Use English-only model?
Translate = True   # Translate non-English to English?
SampleRate = 54100  # Stream device recording frequency
BlockSize = 100      # Block size in milliseconds
Threshold = 0.007    # Minimum volume threshold to activate listening
Vocals = [50, 1000] # Frequency range to detect sounds that could be speech
EndBlocks = 20      # Number of blocks to wait before sending to Whisper

def terminate():
    print("\n\033[93mStopping..\033[0m")
    if os.path.exists('dictate.wav'): os.remove('dictate.wav')
    


class StreamHandler:
    def __init__(self, assist=None):
        if assist == None:  # If not being run by my assistant, just run as terminal transcriber.
            class fakeAsst(): running, talking, analyze = True, False, None
            self.asst = fakeAsst()  # anyone know a better way to do this?
        else: self.asst = assist
        self.running = True
        self.padding = 0
        self.prevblock = self.buffer = np.zeros((0,1))
        self.fileready = False
        print("\033[96mLoading Whisper Model..\033[0m", end='', flush=True)
        self.model = whisper.load_model(f'{Model}{".en" if English else ""}')
        print("\033[90m Done.\033[0m")
    
    def callback(self, indata, frames, time, status):
        #if status: print(status) # for debugging, prints stream errors.
        if not any(indata):
            print('\033[31m.\033[0m', end='', flush=True) # if no input, prints red dots
            #print("\033[31mNo input or device is muted.\033[0m") #old way
            #self.running = False  # used to terminate if no input
            return
        # A few alternative methods exist for detecting speech.. #indata.max() > Threshold
        #zero_crossing_rate = np.sum(np.abs(np.diff(np.sign(indata)))) / (2 * indata.shape[0]) # threshold 20
        freq = np.argmax(np.abs(np.fft.rfft(indata[:, 0]))) * SampleRate / frames
        if np.sqrt(np.mean(indata**2)) > Threshold and Vocals[0] <= freq <= Vocals[1] and not self.asst.talking:
            print('.', end='', flush=True)
            if self.padding < 1: self.buffer = self.prevblock.copy()
            self.buffer = np.concatenate((self.buffer, indata))
            self.padding = EndBlocks
        else:
            self.padding -= 1
            if self.padding > 1:
                self.buffer = np.concatenate((self.buffer, indata))
            elif self.padding < 1 < self.buffer.shape[0] > SampleRate: # if enough silence has passed, write to file.
                self.fileready = True
                write('dictate.wav', SampleRate, self.buffer) # I'd rather send data to Whisper directly..
                self.buffer = np.zeros((0,1))
            elif self.padding < 1 < self.buffer.shape[0] < SampleRate: # if recording not long enough, reset buffer.
                self.buffer = np.zeros((0,1))
                print("\033[2K\033[0G", end='', flush=True)
            else:
                self.prevblock = indata.copy() #np.concatenate((self.prevblock[-int(SampleRate/10):], indata)) # SLOW

    # def process(self):
    #     if self.fileready:
    #         print("\n\033[90mTranscribing..\033[0m")
    #         self.result = self.model.transcribe('dictate.wav',fp16=False,language='en' if English else 'ru', task='translate' if Translate else 'transcribe')
    #         print(f"\033[1A\033[2K\033[0G{self.result['text']}") #вывод в терминал результата!!!
    #         if self.asst.analyze != None: self.asst.analyze(result['text'])
    #         self.fileready = False

    def listen(self, template):
        print("\033[35mListening.. \033[37m(Ctrl+C to Quit)\033[0m")
        with sd.InputStream(channels=1, callback=self.callback, blocksize=int(SampleRate * BlockSize / 1000), samplerate=SampleRate):
            while self.running and self.asst.running: 
                # self.process()
                if self.fileready:
                    print("\n\033[90mTranscribing..\033[0m")
                    self.result = self.model.transcribe('dictate.wav', fp16=False, language='en' if English else 'ru', task='translate' if Translate else 'transcribe')
                    if self.asst.analyze != None: self.asst.analyze(self.result['text'])
                    self.fileready = False

                    # model
                    model = OllamaLLM(model='llama3.1')
                    prompt = ChatPromptTemplate.from_template(template)
                    chain = prompt | model
                    context = ''
                    def handle_conversation(voice, context):
                        user_input = voice
                        result = chain.invoke({'context': context, 'user': user_input})
                        print(f"{user_input}")
                        print(f"{ts.translate_text(result, translator='yandex', to_language='ru')}")
                        context += f'\nUser: {user_input}\nModel: {result}'
                    # end model

                    handle_conversation(f"\033[1A\033[2K\033[0G{self.result['text']}", context)
                    sys.exit()
                    


def main(template):
    try:
        handler = StreamHandler()
        handler.listen(template)
    except (KeyboardInterrupt, SystemExit): pass
    finally:
        terminate()

if __name__ == '__main__':
    main()