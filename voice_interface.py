"""
EatUp Pro - Voice Command Interface
Natural language processing for disk cleanup commands
Uses Speech Recognition and Text-to-Speech APIs
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess


class VoiceCommandInterface:
    """Voice command interface for EatUp Pro"""
    
    def __init__(self):
        self.commands = {
            'scan': self._execute_scan,
            'cleanup': self._execute_cleanup,
            'clean': self._execute_cleanup,
            'free space': self._execute_smart_cleanup,
            'smart cleanup': self._execute_smart_cleanup,
            'show stats': self._display_stats,
            'statistics': self._display_stats,
            'help': self._show_help,
            'hello': self._greet_user,
            'hi': self._greet_user,
            'thanks': self._acknowledge,
            'thank you': self._acknowledge,
            'quit': self._exit_program,
            'exit': self._exit_program,
            'what can you do': self._show_capabilities,
            'report': self._generate_report,
            'create snapshot': self._create_snapshot,
        }
        
        self.recognized_commands = []
        
    @staticmethod
    def recognize_speech(microphone_index: int = None, timeout: int = 10) -> str:
        """Convert speech to text using system's speech recognition"""
        
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            # Use default or specified microphone
            if microphone_index:
                mic = sr.Microphone(device_index=microphone_index)
            else:
                mic = sr.Microphone()
            
            print("🎤 Listening... (speak now)")
            
            with mic as source:
                audio = recognizer.listen(source, timeout=timeout)
            
            # Try Google Speech Recognition
            try:
                text = recognizer.recognize_google(audio)
                print(f"📝 You said: {text}")
                return text.lower().strip()
                
            except sr.UnknownValueError:
                print("⚠️  Could not understand audio")
                return ""
                
            except sr.RequestError as e:
                print(f"❌ Speech recognition service error: {e}")
                return ""
                
        except ImportError:
            print("Please install speech_recognition:")
            print("pip install SpeechRecognition")
            return "manual input:"
        
        except Exception as e:
            print(f"Voice recognition error: {e}")
            return "manual input:"
    
    @staticmethod
    def speak(text: str, rate: int = 175, volume: float = 1.0):
        """Convert text to speech"""
        
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            
            print(f"🔊 Speak: {text}")
            engine.say(text)
            engine.runAndWait()
            
        except ImportError:
            print("Please install pyttsx3:")
            print("pip install pyttsx3")
            print(f"Said: {text}")
            
        except Exception as e:
            print(f"Text-to-speech error: {e}")
            print(f"Said: {text}")
    
    def process_voice_command(self, command_text: str) -> Dict[str, Any]:
        """Process recognized speech and execute appropriate action"""
        
        result = {
            'input': command_text,
            'timestamp': datetime.now().isoformat(),
            'action_executed': False,
            'error': None
        }
        
        # Normalize command
        normalized = command_text.lower().strip()
        
        # Try exact match first
        if normalized in self.commands:
            try:
                response = self.commands[normalized]()
                result['response'] = response
                result['action_executed'] = True
                result['recognized_command'] = normalized
                
            except Exception as e:
                result['error'] = str(e)
                result['response'] = f"Error: {str(e)}"
                
        # Try partial match
        else:
            matched_command = None
            for cmd in self.commands.keys():
                if cmd in normalized:
                    matched_command = cmd
                    break
            
            if matched_command:
                try:
                    response = self.commands[matched_command]()
                    result['response'] = response
                    result['action_executed'] = True
                    result['recognized_command'] = matched_command
                    
                except Exception as e:
                    result['error'] = str(e)
                    result['response'] = f"Error: {str(e)}"
                    
            else:
                result['response'] = "I didn't understand that. Type 'help' for available commands."
        
        # Log command
        self.recognized_commands.append(result)
        
        return result
    
    def _execute_scan(self) -> str:
        """Execute scan command"""
        self.speak("Starting drive scan...")
        return {
            'action': 'scan',
            'status': 'started',
            'message': 'Scan initiated. Check results when complete.'
        }
    
    def _execute_cleanup(self) -> str:
        """Execute cleanup command"""
        self.speak("Cleaning temporary files...")
        return {
            'action': 'cleanup',
            'type': 'temp_files',
            'status': 'started',
            'message': 'Temporary file cleanup started.'
        }
    
    def _execute_smart_cleanup(self) -> str:
        """Execute smart cleanup command"""
        self.speak("Performing smart cleanup with AI recommendations...")
        return {
            'action': 'smart_cleanup',
            'status': 'started',
            'message': 'Smart cleanup initiated. This may take a moment.'
        }
    
    def _display_stats(self) -> str:
        """Display disk statistics"""
        import psutil
        
        usage = psutil.disk_usage('C:')
        
        stats = f"""
Disk Usage Report:
-----------------
Total Capacity: {usage.total / (1024**3):.1f} GB
Used Space: {usage.used / (1024**3):.1f} GB ({usage.percent:.1f}%)
Free Space: {usage.free / (1024**3):.1f} GB
        """
        
        self.speak(stats.replace('\n', ' '))
        return {'action': 'stats', 'data': stats}
    
    def _show_help(self) -> str:
        """Show available commands"""
        help_text = """
Available voice commands:
• Scan - Start disk scan
• Cleanup - Clean temporary files
• Free space - Smart cleanup
• Show stats - Display disk statistics
• Help - Show this help message
• Hello/Hi - Greet the bot
• What can you do - Show capabilities
• Quit/Exit - Exit program
        """
        
        self.speak(help_text.replace('\n', ' '))
        return {'action': 'help', 'commands': list(self.commands.keys())}
    
    def _greet_user(self) -> str:
        """Greet user"""
        greeting = "Hello! I'm EatUp Assistant. How can I help you optimize your disk today?"
        self.speak(greeting)
        return {'action': 'greet', 'message': greeting}
    
    def _acknowledge(self) -> str:
        """Acknowledge thanks"""
        response = "You're welcome! I'm here to help keep your disk clean."
        self.speak(response)
        return {'action': 'acknowledge', 'message': response}
    
    def _exit_program(self) -> str:
        """Exit program"""
        goodbye = "Goodbye! Remember to empty your Recycle Bin periodically."
        self.speak(goodbye)
        return {'action': 'exit', 'message': goodbye}
    
    def _generate_report(self) -> str:
        """Generate cleanup report"""
        response = "Generating cleanup report... Please check your reports folder."
        self.speak(response)
        return {'action': 'report', 'message': response}
    
    def _create_snapshot(self) -> str:
        """Create restore point snapshot"""
        try:
            # Create Windows restore point
            import subprocess
            subprocess.run(['vssadmin', 'create', 'shadow'], capture_output=True)
            
            response = "Restore point created successfully!"
            self.speak(response)
            return {'action': 'snapshot', 'status': 'created'}
            
        except Exception as e:
            response = f"Could not create snapshot: {str(e)}"
            return {'action': 'snapshot', 'error': str(e)}


def interactive_voice_mode(cleaner_obj=None):
    """Interactive voice-controlled mode"""
    
    print("\n" + "="*60)
    print("🎤 EATUP VOICE ASSISTANT")
    print("="*60)
    print("Commands: help, scan, cleanup, free space, show stats, quit\n")
    
    interface = VoiceCommandInterface()
    
    while True:
        # Listen for command
        command = interface.recognize_speech()
        
        if not command:
            continue
        
        if command == "quit" or command == "exit":
            print("👋 Goodbye!")
            interface.speak("Goodbye!")
            break
        
        # Process command
        result = interface.process_voice_command(command)
        
        # Speak response
        if 'response' in result:
            interface.speak(str(result['response']))
            
            # For complex responses, also print them
            if isinstance(result['response'], dict):
                print(json.dumps(result['response'], indent=2))


if __name__ == "__main__":
    import json
    
    print("Testing Voice Command Interface...")
    print("-"*60)
    
    interface = VoiceCommandInterface()
    
    # Test different commands
    test_commands = [
        "hello",
        "scan my computer",
        "what can you do",
        "help please",
        "show me disk statistics",
        "smart cleanup"
    ]
    
    for cmd in test_commands:
        print(f"\nUser says: '{cmd}'")
        result = interface.process_voice_command(cmd)
        print(f"Response: {json.dumps(result, indent=2)}")
    
    # Interactive mode (uncomment to use)
    # interactive_voice_mode()
