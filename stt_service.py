import playsound
import sounddevice as sd
import soundfile as sf
import os
import numpy as np
import speech_recognition as sr
import pyttsx3
import threading
import time
import queue
import io
import asyncio
from typing import Optional, Callable

class SpeechHandler:
    def __init__(self):
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # TTS queue for thread-safe operations
        self.tts_queue = queue.Queue()
        self.is_running = True
        self.worker_thread = None
        
        # Start TTS worker thread - CALL THIS ONCE
        self._start_tts_worker()
        
        # Calibrate microphone for ambient noise
        self.calibrate_microphone()
        
    def setup_tts(self):
        """Configure text-to-speech settings"""
        voices = self.tts_engine.getProperty('voices')
        # Set voice (0 for male, 1 for female - may vary by system)
        if len(voices) > 1:
            self.tts_engine.setProperty('voice', voices[1].id)
        
        # Set speech rate
        self.tts_engine.setProperty('rate', 150)
        
        # Set volume
        self.tts_engine.setProperty('volume', 0.8)
    
    def _start_tts_worker(self):
        """Start the TTS worker thread for safe audio operations"""
        def tts_worker():
            while self.is_running:
                try:
                    # Get TTS request from queue with timeout
                    text, callback, audio_buffer = self.tts_queue.get(timeout=1)
                    if text is None:  # Shutdown signal
                        break
                    
                    try:
                        # Create a new TTS engine instance for this request to avoid threading issues
                        temp_engine = pyttsx3.init()
                        temp_engine.setProperty('rate', 150)
                        temp_engine.setProperty('volume', 0.8)
                        
                        if audio_buffer:
                            # Save to in-memory buffer
                            temp_engine.save_to_file(text, 'temp_speech.wav')
                            temp_engine.runAndWait()
                            
                            # Read the file into buffer
                            with open('temp_speech.wav', 'rb') as f:
                                audio_buffer.write(f.read())
                            audio_buffer.seek(0)
                            
                            if callback:
                                callback(audio_buffer)
                        else:
                            # Direct speech output
                            temp_engine.say(text)
                            temp_engine.runAndWait()
                            if callback:
                                callback(None)
                                
                    except Exception as e:
                        print(f"TTS error: {e}")
                        if callback:
                            callback(None)
                    
                    self.tts_queue.task_done()
                    
                except queue.Empty:
                    continue
                    
        self.worker_thread = threading.Thread(target=tts_worker, daemon=True)
        self.worker_thread.start()
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        print("Calibrating microphone for ambient noise... Please wait.")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("Microphone calibrated!")
        except Exception as e:
            print(f"Microphone calibration failed: {e}")
    
    async def text_to_speech(self, text: str) -> io.BytesIO:
        """Convert text to speech and return audio buffer (async)"""
        if not text:
            return io.BytesIO()
        
        try:
            # Run TTS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            audio_buffer = await loop.run_in_executor(
                None, 
                self._blocking_text_to_speech, 
                text
            )
            return audio_buffer
        except Exception as e:
            print(f"TTS failed: {e}")
            return io.BytesIO()

    def play_audio(self, temp_file):
        data, rate = sf.read(temp_file)
        data = data.astype(np.float32)  # convert to float32 explicitly
        stream = sd.OutputStream(samplerate=rate, channels=data.shape[1] if data.ndim > 1 else 1)
        stream.start()
        stream.write(data)
        return stream  # call stream.stop() to interrupt

   

    
    def _blocking_text_to_speech(self, text: str) -> io.BytesIO:
        """Blocking TTS operation with automatic playback and cleanup."""
        try:
            temp_engine = pyttsx3.init()
            temp_engine.setProperty('rate', 150)
            temp_engine.setProperty('volume', 0.8)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            temp_file = f"temp_speech_{timestamp}.wav"

            # Generate speech file
            temp_engine.save_to_file(text, temp_file)
            temp_engine.runAndWait()

            # Play generated speech
            try:
                str = self.play_audio(temp_file)
                str.stop()
                str.close()
            except Exception as play_err:
                print(f"Audio playback failed: {play_err}")

            # Read into memory buffer
            audio_buffer = io.BytesIO()
            with open(temp_file, 'rb') as f:
                audio_buffer.write(f.read())
            audio_buffer.seek(0)

            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)

            return audio_buffer

        except Exception as e:
            print(f"Blocking TTS error: {e}")
            return io.BytesIO()

    
    def speak(self, text: str):
        """Non-blocking speech output (fire and forget)"""
        if not text:
            return
        
        def tts_callback(_):
            pass  # Callback not needed for fire-and-forget
        
        self.tts_queue.put((text, tts_callback, None))
    
    async def speech_to_text(self, timeout: int = 5) -> Optional[str]:
        """Convert speech to text with timeout (async)"""
        try:
            print(f"Listening... (timeout: {timeout} seconds)")
            
            # Run blocking recognition in thread pool
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None, 
                self._blocking_speech_recognition, 
                timeout
            )
            
            return text.lower() if text else None
            
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return None
    
    def _blocking_speech_recognition(self, timeout: int) -> Optional[str]:
        """Blocking speech recognition (run in thread pool)"""
        try:
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=timeout
                )
            
            print("Processing speech...")
            # Use Google's speech recognition
            text = self.recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period.")
            return None
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            return None
    
    async def continuous_conversation(self, callback: Optional[Callable] = None):
        """Run continuous speech-to-text and text-to-speech conversation (async)"""
        print("Starting continuous conversation. Say 'exit' to stop.")
        
        while True:
            # Speech to Text
            recognized_text = await self.speech_to_text(timeout=7)
            
            if recognized_text and callback:
                # Use callback for response handling
                should_continue = await callback(recognized_text)
                if not should_continue:
                    break
    
    async def conversation_callback(self, text: str) -> bool:
        """Example callback for continuous conversation"""
        if 'exit' in text or 'quit' in text:
            response = "Goodbye! Have a great day."
            print(f"Response: {response}")
            self.speak(response)
            return False
        elif 'hello' in text:
            response = "Hello there! How can I help you today?"
        elif 'time' in text:
            current_time = time.strftime("%I:%M %p")
            response = f"The current time is {current_time}"
        elif 'name' in text:
            response = "I am your Python speech assistant!"
        else:
            response = f"You said: {text}. That's interesting!"
        
        print(f"Response: {response}")
        self.speak(response)
        return True
    
    def get_voice_info(self):
        """Display available voices"""
        voices = self.tts_engine.getProperty('voices')
        print("\nAvailable voices:")
        for i, voice in enumerate(voices):
            print(f"{i}: {voice.name} - {voice.id}")
    
    async def save_speech_to_file(self, text: str, filename: str = "output.wav"):
        """Save speech to WAV file (async)"""
        try:
            audio_buffer = await self.text_to_speech(text)
            if audio_buffer and audio_buffer.getbuffer().nbytes > 0:
                with open(filename, 'wb') as f:
                    f.write(audio_buffer.getvalue())
                print(f"Speech saved to {filename}")
                return True
        except Exception as e:
            print(f"Error saving speech to file: {e}")
        return False
    
    def shutdown(self):
        """Clean shutdown of speech handler"""
        print("Shutting down speech handler...")
        self.is_running = False
        
        # Send shutdown signal to worker thread
        self.tts_queue.put((None, None, None))
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        print("Speech handler shutdown complete.")

# Example usage
async def main():
    handler = SpeechHandler()
    
    try:
        # Test async TTS
        print("Testing async TTS...")
        audio_buffer = await handler.text_to_speech("Hello, this is a test of async text to speech.")
        
        # Test async STT
        print("Speak something...")
        text = await handler.speech_to_text(timeout=5)
        if text:
            print(f"You said: {text}")
            
        # Test continuous conversation
        # await handler.continuous_conversation(handler.conversation_callback)
        
    finally:
        handler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())