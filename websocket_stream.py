#!/usr/bin/env python3
"""
EatUp Pro v8.2+ - Real-Time WebSocket Streaming Server
Live disk usage updates, achievement notifications, chat system
"""

import asyncio
import json
from typing import Dict, List, Any, Set
from datetime import datetime
import websockets
from collections import defaultdict


class WebSocketHub:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        self.active_connections: Set[websockets.WebSocketServerProtocol] = set()
        self.user_sessions: Dict[str, Dict] = {}
        self.channel_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        print("🌐 WebSocket Hub Initialized")
    
    async def connect(self, websocket: websockets.WebSocketServerProtocol):
        """Handle new WebSocket connection"""
        self.active_connections.add(websocket)
        session_id = f"session_{id(websocket)}"
        
        # Create user session
        self.user_sessions[session_id] = {
            'websocket': websocket,
            'connected_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'subscribed_channels': ['system', 'personal'],
            'status': 'active'
        }
        
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'connection_established',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'message': f'Connected to EatUp Pro! You are session #{len(self.active_connections)}'
        }))
        
        print(f"💬 New connection #{len(self.active_connections)}")
    
    async def disconnect(self, websocket: websockets.WebSocketServerProtocol):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Clean up session
        for session_id, session in list(self.user_sessions.items()):
            if session['websocket'] == websocket:
                del self.user_sessions[session_id]
                break
        
        print(f"🔌 Disconnected connection #{len(self.active_connections) + 1}")
    
    async def broadcast(self, message: Dict, exclude_session: str = None):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        # Format message
        payload = json.dumps(message)
        
        # Send to all except excluded session
        disconnected = []
        for ws in self.active_connections:
            try:
                if exclude_session is None or id(ws) != int(exclude_session.split('_')[1]):
                    await asyncio.wait_for(ws.send(payload), timeout=2.0)
            except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError) as e:
                disconnected.append(ws)
                print(f"⚠️  Failed to send to client: {e}")
        
        # Remove disconnected clients
        for ws in disconnected:
            self.active_connections.discard(ws)
    
    async def send_to_user(self, user_id: str, message: Dict):
        """Send message to specific user"""
        session = self.user_sessions.get(user_id)
        
        if session:
            try:
                await session['websocket'].send(json.dumps(message))
                session['last_activity'] = datetime.now().isoformat()
            except Exception as e:
                print(f"❌ Failed to send to {user_id}: {e}")
    
    def subscribe_channel(self, user_id: str, channel: str):
        """Subscribe user to a channel"""
        if user_id in self.user_sessions:
            sessions = self.user_sessions[user_id]['subscribed_channels']
            
            if channel not in sessions:
                sessions.append(channel)
            
            print(f"✅ User {user_id} subscribed to {channel}")
    
    def unsubscribe_channel(self, user_id: str, channel: str):
        """Unsubscribe user from channel"""
        if user_id in self.user_sessions:
            channels = self.user_sessions[user_id]['subscribed_channels']
            
            if channel in channels:
                channels.remove(channel)
            
            print(f"❌ User {user_id} unsubscribed from {channel}")
    
    def emit_achievement_unlocked(self, achievement: Dict, user_id: str):
        """Emit achievement unlock notification"""
        message = {
            'type': 'achievement_unlocked',
            'data': achievement,
            'timestamp': datetime.now().isoformat(),
            'priority': 'high',
            'sound': 'achievement.mp3',
            'animation': 'confetti',
            'channels': ['system', 'personal']
        }
        
        asyncio.create_task(self.broadcast(message))
        print(f"🎉 Emitted achievement: {achievement['name']}")
    
    def emit_disk_usage_update(self, metrics: Dict):
        """Broadcast disk usage changes"""
        message = {
            'type': 'disk_usage_update',
            'data': metrics,
            'timestamp': datetime.now().isoformat(),
            'channels': ['system', 'realtime']
        }
        
        asyncio.create_task(self.broadcast(message))
    
    def emit_system_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Emit system alert"""
        message_data = {
            'type': 'system_alert',
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'channels': ['system']
        }
        
        asyncio.create_task(self.broadcast(message_data))
        
        if severity == 'critical':
            print(f"🚨 CRITICAL ALERT: {message}")


# Global hub instance
hub = WebSocketHub()


async def handle_client(websocket: websockets.WebSocketServerProtocol):
    """Handle incoming WebSocket messages"""
    await hub.connect(websocket)
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Update activity timestamp
                for session in hub.user_sessions.values():
                    if session['websocket'] == websocket:
                        session['last_activity'] = datetime.now().isoformat()
                        break
                
                # Process command
                await process_command(data, websocket)
                
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'error': 'Invalid JSON format',
                    'type': 'error'
                }))
    
    finally:
        await hub.disconnect(websocket)


async def process_command(data: Dict, websocket: websockets.WebSocketServerProtocol):
    """Process received commands"""
    cmd_type = data.get('type')
    
    if cmd_type == 'subscribe':
        channel = data.get('channel', 'system')
        await hub.subscribe_channel(str(id(websocket)), channel)
    
    elif cmd_type == 'unsubscribe':
        channel = data.get('channel', 'system')
        await hub.unsubscribe_channel(str(id(websocket)), channel)
    
    elif cmd_type == 'ping':
        await websocket.send(json.dumps({
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        }))
    
    elif cmd_type == 'request_stats':
        # Send current stats
        await websocket.send(json.dumps({
            'type': 'stats_response',
            'data': {
                'total_connections': len(hub.active_connections),
                'active_users': len(hub.user_sessions)
            },
            'timestamp': datetime.now().isoformat()
        }))
    
    elif cmd_type == 'chat_message':
        # Broadcast chat message
        chat_msg = {
            'type': 'chat_message',
            'data': data.get('message', ''),
            'sender': data.get('sender', 'anonymous'),
            'timestamp': datetime.now().isoformat()
        }
        
        await hub.broadcast(chat_msg)


async def heartbeat_loop():
    """Send periodic heartbeats to maintain connections"""
    while True:
        await asyncio.sleep(30)  # Every 30 seconds
        
        await hub.broadcast({
            'type': 'heartbeat',
            'timestamp': datetime.now().isoformat(),
            'connections': len(hub.active_connections),
            'users_online': len(hub.user_sessions)
        })
        
        print(f"💓 Heartbeat sent ({len(hub.active_connections)} connections)")


async def cleanup_inactive_sessions():
    """Clean up inactive user sessions"""
    while True:
        await asyncio.sleep(60)  # Check every minute
        
        now = datetime.now()
        
        to_remove = []
        for session_id, session in hub.user_sessions.items():
            last_activity = datetime.fromisoformat(session['last_activity'])
            age_minutes = (now - last_activity).total_seconds() / 60
            
            if age_minutes > 30:  # Timeout after 30 minutes
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del hub.user_sessions[session_id]
        
        if to_remove:
            print(f"🧹 Cleaned up {len(to_remove)} inactive sessions")


def main():
    """Run WebSocket server demo"""
    print("\n🌐 Starting EatUp Pro WebSocket Server...")
    print("=" * 60)
    
    # Demo commands
    commands = [
        {"type": "ping"},
        {"type": "subscribe", "channel": "system"},
        {"type": "request_stats"}
    ]
    
    print("\nAvailable Commands:")
    for cmd in commands:
        print(f"  • {json.dumps(cmd)}")
    
    print("\nServer will listen on ws://localhost:8765")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Start servers
        print_info = lambda s: print(s)
        start_server = lambda **kw: asyncio.run(_start_demo(**kw))
        
        # Run in background mode for demo
        loop = asyncio.new_event_loop()
        
        async def run_servers():
            # Start WebSocket server
            server = await websockets.serve(
                handle_client,
                "0.0.0.0",
                8765
            )
            
            # Start background tasks
            heartbeat = loop.create_task(heartbeat_loop())
            cleanup = loop.create_task(cleanup_inactive_sessions())
            
            await server.wait_closed()
        
        # Don't actually run - just show demo
        print("WebSocket server ready!")
        print("\nTo connect, use WebSocket client:")
        print("  const ws = new WebSocket('ws://localhost:8765');")
        print("  ws.onmessage = (event) => console.log(event.data);")
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped")


if __name__ == '__main__':
    import websockets
    main()
