#!/usr/bin/env python3
"""
EatUp Pro v8.1 - Voice Command Interface
Natural language speech recognition and control for hands-free operation
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

try:
    import speech_recognition as sr
    import pyttsx2
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False


class VoiceCommandController:
    """Hands-free voice control system for EatUp Pro"""
    
    def __init__(self):
        self.recognizer = None
        self.engine = None
        self.is_listening = False
        self.command_history: List[Dict] = []
        
        if VOICE_AVAILABLE:
            self._initialize_voice_system()
            print("✅ Voice Command System Ready")
    
    def _initialize_voice_system(self):
        """Initialize speech recognition and synthesis engines"""
        try:
            # Speech recognition
            self.recognizer = sr.Recognizer()
            self.recognizer.pause_threshold = 0.8
            self.recognizer.energy_threshold = 400
            
            # Speech synthesis (TTS)
            self.engine = pyttsx2.init()
            self.engine.setProperty('rate', 150)  # Words per minute
            self.engine.setProperty('volume', 1.0)
            
            # Set voice (prefer female voice if available)
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'female' in voice.name.lower() or 'female' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            print("🎤 Voice system initialized successfully")
            
        except Exception as e:
            print(f"⚠️  Voice system initialization failed: {e}")
    
    def listen_command(self, timeout: int = 10, phrasetimeout: int = 5) -> Optional[str]:
        """
        Listen for voice command with natural language processing
        
        Returns:
            Parsed command tuple (action, parameters) or None
        """
        if not VOICE_AVAILABLE or not self.recognizer:
            return None
        
        try:
            print("🎧 Listening... (say a command)")
            
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Record audio
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrasetimeport
                )
            
            # Convert speech to text using Google Web API
            command = self.recognizer.recognize_google(audio)
            print(f"🗣️  Heard: '{command}'")
            
            # Parse natural language into structured command
            parsed = self._parse_natural_language(command.lower())
            
            if parsed:
                self.command_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'raw_input': command,
                    'parsed': parsed
                })
            
            return parsed
            
        except sr.WaitTimeoutError:
            print("⏱️  No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"🚫 Speech recognition service error: {e}")
            return None
    
    def _parse_natural_language(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse natural language commands into structured operations
        
        Examples:
            "scan my C drive" → {"action": "scan", "drive": "C:"}
            "clean up temporary files" → {"action": "cleanup", "type": "temp"}
            "find duplicate files" → {"action": "find_duplicates"}
        """
        patterns = {
            # Scan commands
            r'\b(scan|analyze|check)\s+(my\s+)?(.+?)(\s+drive)?\b': 
                lambda m: {'action': 'scan', 'drive': m.group(3).strip()},
            
            r'what\s+(is|are) the disk\s+(space|usage)\b':
                lambda m: {'action': 'status'},
            
            # Cleanup commands
            r'(clean|remove)\s+(up\s+)?(the\s+)?((?:temp|temporary|junk|cache)[^\s]*)\b':
                lambda m: {'action': 'cleanup', 'type': 'temp'},
            
            r'(clean|remove)\s+(up\s+)?(duplicate|duplicate)\b.*file':
                lambda m: {'action': 'cleanup', 'type': 'duplicates'},
            
            r'(clean|remove)\s+(up\s+)?(game|gaming).*cache':
                lambda m: {'action': 'cleanup', 'type': 'game_cache'},
            
            # Find/locate commands
            r'(find|locate|search)\s+(large|big|huge)(\s+files?)?\b':
                lambda m: {'action': 'find_large_files'},
            
            r'(find|locate|search)\s+(duplicate|identical).*file(s)?':
                lambda m: {'action': 'find_duplicates'},
            
            # Status/check commands
            r'(how much|what is) space left\b':
                lambda m: {'action': 'free_space'},
            
            r'(how much|what is) space used\b':
                lambda m: {'action': 'used_space'},
            
            r'tell me about my storage\b':
                lambda m: {'action': 'storage_summary'},
            
            # AI features
            r'run smart cleanup(?: on (.+))?':
                lambda m: {'action': 'smart_cleanup', 'params': {'drive': m.group(1)}},
            
            r'optimize my system\b':
                lambda m: {'action': 'optimize'},
            
            # Quit commands
            r'(quit|exit|stop)\b.*voice':
                lambda m: {'action': 'quit'},
            
            r'stop listening\b':
                lambda m: {'action': 'stop_listening'},
        }
        
        for pattern, parser in patterns.items():
            match = re.search(pattern, text)
            if match:
                try:
                    return parser(match)
                except Exception as e:
                    print(f"❌ Parse error: {e}")
                    return None
        
        # Fallback: simple keyword matching
        if any(word in text for word in ['scan', 'analyze']):
            return {'action': 'scan'}
        elif any(word in text for word in ['clean', 'remove', 'delete']):
            if 'duplicate' in text:
                return {'action': 'cleanup', 'type': 'duplicates'}
            elif 'temp' in text or 'temporary' in text:
                return {'action': 'cleanup', 'type': 'temp'}
            elif 'game' in text:
                return {'action': 'cleanup', 'type': 'game_cache'}
            else:
                return {'action': 'cleanup'}
        elif any(word in text for word in ['find', 'search', 'locate']):
            return {'action': 'find'}
        elif any(word in text for word in ['help', 'what can you do']):
            return {'action': 'help'}
        
        return None
    
    def speak(self, message: str, priority: str = 'normal'):
        """Speak response using text-to-speech"""
        if not VOICE_AVAILABLE or not self.engine:
            print(f"💬 {message}")
            return
        
        try:
            if priority == 'urgent':
                self.engine.stop()  # Interrupt ongoing speech
            
            self.engine.say(message)
            self.engine.runAndWait()
            
        except Exception as e:
            print(f"❌ TTS error: {e}")
            print(f"💬 {message}")
    
    def show_feedback(self, message: str, feedback_type: str = 'info'):
        """Show visual feedback alongside speech"""
        icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'speech': '🎤'
        }
        
        icon = icons.get(feedback_type, '💬')
        print(f"{icon} {message}")
        self.speak(message, 'urgent' if feedback_type == 'error' else 'normal')
    
    def continuous_listen_loop(self, poll_interval: float = 2.0):
        """Run continuous listening loop for hands-free operation"""
        print("\n🎤 Starting voice command loop (Ctrl+C to stop)")
        print("   Say: 'scan my C drive', 'clean temp files', or 'help'\n")
        
        self.is_listening = True
        
        try:
            while self.is_listening:
                command = self.listen_command()
                
                if command:
                    self.show_feedback(f"Executing: {command['action']}", 'speech')
                    
                    # Process command (in real implementation, call actual functions)
                    self._execute_command(command)
                
                # Brief pause before next listening cycle
                import time
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            self.is_listening = False
            self.show_feedback("Voice commands stopped", 'info')
    
    def _execute_command(self, command: Dict[str, Any]):
        """Execute parsed voice command"""
        action = command.get('action')
        params = command.get('params', {})
        
        print(f"\n🔧 Executing: {json.dumps(command)}")
        
        if action == 'scan':
            drive = params.get('drive', 'C:')
            print(f"🔍 Scanning {drive} drive...")
            # Would call: scan_drive(drive)
        
        elif action == 'cleanup':
            cleanup_type = params.get('type', 'all')
            print(f"🧹 Cleaning {cleanup_type}...")
            # Would call: cleanup_type(cleanup_type)
        
        elif action == 'find_duplicates':
            print("🔎 Searching for duplicates...")
            # Would call: find_duplicates()
        
        elif action == 'find_large_files':
            print("📊 Finding large files...")
            # Would call: find_large_files(threshold_gb=1)
        
        elif action == 'smart_cleanup':
            print("🤖 Running intelligent cleanup...")
            # Would call: smart_cleanup()
        
        elif action == 'status':
            print("📊 Showing system status...")
            # Would call: get_status_report()
        
        elif action == 'help':
            self.speak("I can help you scan your drives, clean temporary files, "
                      "find duplicates, or optimize your storage. Try saying "
                      "'scan my C drive' or 'clean temporary files'")
        
        elif action == 'quit' or action == 'stop_listening':
            self.is_listening = False
        
        else:
            self.show_feedback(f"Unknown command: {action}", 'error')
        
        self.show_feedback("Done", 'success')
    
    def get_command_history(self, limit: int = 10) -> List[Dict]:
        """Get recent voice command history"""
        return self.command_history[-limit:]


# Quick demo interface
def voice_demo():
    """Demonstrate voice command capabilities"""
    print("=" * 60)
    print("EatUp Pro Voice Commands Demo v8.1")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  • 'scan my C drive'")
    print("  • 'clean temporary files'")
    print("  • 'find duplicate files'")
    print("  • 'what is my disk usage'")
    print("  • 'run smart cleanup'")
    print("  • 'help'")
    print("\nIn production, this would listen via microphone.\n")
    
    # Test command parsing
    test_commands = [
        "scan my C drive",
        "clean up all the temporary files please",
        "find duplicate files on my system",
        "what is the disk usage",
        "run smart cleanup on C:",
        "optimize my storage"
    ]
    
    controller = VoiceCommandController()
    
    for test_cmd in test_commands:
        print(f"\n🎤 User says: '{test_cmd}'")
        parsed = controller._parse_natural_language(test_cmd.lower())
        print(f"⚙️  Parsed: {parsed}\n")


if __name__ == '__main__':
    voice_demo()
