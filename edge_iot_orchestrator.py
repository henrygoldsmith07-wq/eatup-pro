"""
EatUp Pro - Edge Computing & IoT Integration v5.0

Revolutionary expansion into edge computing and IoT device orchestration.
Manages disk optimization across smart devices, IoT sensors, and edge computing nodes.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import os
import json
import socket
import hashlib
import asyncio
import aiohttp
from datetime import datetime, timedelta
from collections import defaultdict
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Types of edge/IoT devices"""
    SMART_TV = "smart_tv"
    ROBOT_VACUUM = "robot_vacuum"
    SECURITY_CAMERA = "security_camera"
    NASSYSTEM = "nas_system"
    RASPBERRY_PI = "raspberry_pi"
    NUC_MINI_PC = "nuc_mini_pc"
    GAME_CONSOLE = "game_console"
    HOME_ASSISTANT = "home_assistant"
    INDUSTRIAL_GATEWAY = "industrial_gateway"


@dataclass
class EdgeNode:
    """Represents an edge computing node"""
    node_id: str
    hostname: str
    ip_address: str
    device_type: DeviceType
    storage_capacity_gb: float
    storage_used_gb: float
    cpu_cores: int
    ram_gb: float
    online_status: bool
    last_heartbeat: datetime
    capabilities: List[str]
    firmware_version: str
    
    def health_score(self) -> float:
        """Calculate overall health score (0-1)"""
        factors = [
            self.online_status,
            min(1.0, (self.storage_capacity_gb - self.storage_used_gb) / self.storage_capacity_gb),
            0.8  # Could add CPU/Memory checks
        ]
        return sum(factors) / len(factors)


@dataclass
class IOTCommand:
    """Command to execute on IoT device"""
    command_id: str
    target_node: str
    command_type: str
    parameters: Dict[str, Any]
    timeout_seconds: int
    priority: int  # 1=critical, 5=low
    scheduled_at: Optional[datetime] = None


@dataclass
class EdgeOptimizationResult:
    """Results from edge node optimization"""
    node_id: str
    hostname: str
    timestamp: datetime
    success: bool
    space_freed_bytes: int
    operations_performed: List[str]
    errors: List[str]
    metrics: Dict[str, Any]


class EdgeIoTOrchestrator:
    """
    Orchestrates disk cleanup across edge computing and IoT ecosystem.
    Manages heterogeneous devices with different architectures and protocols.
    """
    
    def __init__(self, config_path: str = "data/edge_ioT_config.json"):
        self.config_path = config_path
        
        # Node registry
        self.nodes: Dict[str, EdgeNode] = {}
        
        # Command queue
        self.command_queue: List[IOTCommand] = []
        
        # Optimization history
        self.optimization_history: List[EdgeOptimizationResult] = []
        
        # Communication sessions
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        
        # Protocol adapters
        self.adapters = {
            'ssh': SSHAdapter(),
            'http': HTTPAdapter(),
            'mqtt': MQTTAdapter(),
            'local': LocalAdapter()
        }
        
        # Load existing configuration
        self.load_config()
        
        logger.info("🔗 Edge IoT Orchestrator initialized")
    
    def register_edge_node(self, node_info: Dict) -> str:
        """Register a new edge/IoT device"""
        node_id = f"{node_info['hostname'][:8]}_{hash(node_info['ip_address']) % 1000}"
        
        device_type = DeviceType(node_info.get('device_type', 'raspberry_pi'))
        
        node = EdgeNode(
            node_id=node_id,
            hostname=node_info['hostname'],
            ip_address=node_info['ip_address'],
            device_type=device_type,
            storage_capacity_gb=node_info.get('storage_capacity', 32),
            storage_used_gb=node_info.get('storage_used', 16),
            cpu_cores=node_info.get('cpu_cores', 4),
            ram_gb=node_info.get('ram_gb', 2),
            online_status=True,
            last_heartbeat=datetime.now(),
            capabilities=node_info.get('capabilities', ['disk_scan']),
            firmware_version=node_info.get('firmware', '1.0.0')
        )
        
        self.nodes[node_id] = node
        self.save_config()
        
        logger.info(f"✅ Registered {device_type.value} '{node.hostname}' at {node.ip_address}")
        return node_id
    
    def discover_network_nodes(self, network_range: str = "192.168.1.0/24") -> List[str]:
        """Auto-discover available nodes on local network"""
        logger.info(f"🔍 Scanning network {network_range} for edge nodes...")
        
        # Simulated discovery (would use SSDP/mDNS in production)
        discovered = [
            {"hostname": "SmartTV-LivingRoom", "ip": "192.168.1.100", "type": "smart_tv"},
            {"hostname": "RasPi-Kitchen", "ip": "192.168.1.101", "type": "raspberry_pi"},
            {"hostname": "NAS-Main", "ip": "192.168.1.102", "type": "nas_system"},
            {"hostname": "SecurityHub", "ip": "192.168.1.103", "type": "home_assistant"}
        ]
        
        registered_ids = []
        for dev in discovered:
            self.register_edge_node({
                'hostname': dev['hostname'],
                'ip_address': dev['ip'],
                'device_type': dev['type'],
                'storage_capacity': 64 if 'nas' not in dev['hostname'] else 1000,
                'storage_used': 20 if 'nas' not in dev['hostname'] else 750,
                'cpu_cores': 4,
                'ram_gb': 2 if 'rasp' in dev['hostname'].lower() else 8,
                'capabilities': ['disk_scan', 'file_cleanup', 'cache_clear']
            })
            registered_ids.append(dev['hostname'])
        
        return registered_ids
    
    async def execute_optimization(self, node_id: str, 
                                   optimization_type: str = "smart") -> EdgeOptimizationResult:
        """Execute optimization on specific edge node"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        
        logger.info(f"⚡ Optimizing node '{node.hostname}' ({node.device_type.value})...")
        
        try:
            # Select appropriate adapter
            adapter = self._select_adapter(node)
            
            # Execute optimization remotely
            result_data = await adapter.execute_optimization(
                node.ip_address,
                optimization_type,
                node.capabilities
            )
            
            result = EdgeOptimizationResult(
                node_id=node_id,
                hostname=node.hostname,
                timestamp=datetime.now(),
                success=result_data['success'],
                space_freed_bytes=result_data.get('space_freed_bytes', 0),
                operations_performed=result_data.get('operations', []),
                errors=result_data.get('errors', []),
                metrics=result_data.get('metrics', {})
            )
            
            self.optimization_history.append(result)
            logger.info(f"   ✅ Freed {result.space_freed_bytes/(1024**3):.2f} GB on {node.hostname}")
            
            return result
            
        except Exception as e:
            error_result = EdgeOptimizationResult(
                node_id=node_id,
                hostname=node.hostname,
                timestamp=datetime.now(),
                success=False,
                space_freed_bytes=0,
                operations_performed=[],
                errors=[str(e)],
                metrics={}
            )
            
            logger.error(f"   ❌ Failed to optimize {node.hostname}: {e}")
            return error_result
    
    async def batch_optimize(self, node_ids: List[str], 
                            optimization_type: str = "smart") -> List[EdgeOptimizationResult]:
        """Execute parallel optimization across multiple nodes"""
        logger.info(f"\n🚀 Starting batch optimization on {len(node_ids)} nodes...")
        
        tasks = [
            self.execute_optimization(node_id, optimization_type)
            for node_id in node_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        successful = [r for r in results if isinstance(r, EdgeOptimizationResult)]
        failed_count = len(results) - len(successful)
        
        total_freed = sum(r.space_freed_bytes for r in successful)
        
        logger.info(f"\n✅ Batch complete!")
        logger.info(f"   Successful: {len(successful)}/{len(node_ids)}")
        logger.info(f"   Total freed: {total_freed/(1024**3):.2f} GB")
        
        return successful
    
    def schedule_command(self, command: IOTCommand):
        """Queue a command for execution"""
        self.command_queue.append(command)
        
        # Sort by priority
        self.command_queue.sort(key=lambda x: x.priority)
        
        logger.info(f"📝 Scheduled {command.command_type} on {command.target_node} (priority {command.priority})")
    
    async def process_command_queue(self):
        """Process queued commands"""
        while self.command_queue:
            cmd = self.command_queue.pop(0)
            
            if cmd.scheduled_at and cmd.scheduled_at > datetime.now():
                # Re-queue for later
                self.command_queue.append(cmd)
                break
            
            try:
                await self._execute_command(cmd)
            except Exception as e:
                logger.error(f"Command {cmd.command_id} failed: {e}")
    
    async def _execute_command(self, command: IOTCommand):
        """Execute a specific command on target node"""
        if command.target_node not in self.nodes:
            raise ValueError(f"Target node not found")
        
        node = self.nodes[command.target_node]
        adapter = self._select_adapter(node)
        
        await adapter.execute_command(
            node.ip_address,
            command.command_type,
            command.parameters,
            command.timeout_seconds
        )
    
    def _select_adapter(self, node: EdgeNode) -> "ProtocolAdapter":
        """Select appropriate protocol adapter for node"""
        if node.device_type in [DeviceType.RASPBERRY_PI, DeviceType.NUC_MINI_PC]:
            return self.adapters['ssh']
        elif node.device_type in [DeviceType.SMART_TV, DeviceType.GAME_CONSOLE]:
            return self.adapters['http']
        elif node.device_type in [DeviceType.SECURITY_CAMERA, DeviceType.HOME_ASSISTANT]:
            return self.adapters['mqtt']
        else:
            return self.adapters['local']
    
    def get_network_health(self) -> Dict[str, Any]:
        """Get comprehensive network health overview"""
        online_count = sum(1 for n in self.nodes.values() if n.online_status)
        total_capacity = sum(n.storage_capacity_gb for n in self.nodes.values())
        total_used = sum(n.storage_used_gb for n in self.nodes.values())
        
        avg_health = sum(n.health_score() for n in self.nodes.values()) / max(len(self.nodes), 1)
        
        return {
            'total_nodes': len(self.nodes),
            'online_nodes': online_count,
            'offline_nodes': len(self.nodes) - online_count,
            'average_health': avg_health,
            'total_storage_tb': total_capacity / 1024,
            'used_storage_tb': total_used / 1024,
            'utilization_percent': (total_used / total_capacity * 100) if total_capacity > 0 else 0,
            'by_device_type': self._stats_by_device_type(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _stats_by_device_type(self) -> Dict[str, Dict]:
        """Statistics grouped by device type"""
        groups = defaultdict(lambda: {'count': 0, 'capacity': 0, 'used': 0})
        
        for node in self.nodes.values():
            dtype = node.device_type.value
            groups[dtype]['count'] += 1
            groups[dtype]['capacity'] += node.storage_capacity_gb
            groups[dtype]['used'] += node.storage_used_gb
        
        return dict(groups)
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        recent = self.optimization_history[-100:]  # Last 100 operations
        
        successful = [r for r in recent if r.success]
        failed = [r for r in recent if not r.success]
        
        total_freed = sum(r.space_freed_bytes for r in successful)
        
        # Best performing node
        best_node = max(
            successful,
            key=lambda x: x.space_freed_bytes,
            default=None
        )
        
        return {
            'report_generated': datetime.now().isoformat(),
            'summary': {
                'total_operations': len(recent),
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': len(successful) / max(len(recent), 1),
                'total_space_freed_tb': total_freed / (1024**4)
            },
            'top_performer': best_node.to_dict() if best_node else None,
            'nodes_optimized_today': len(set(r.node_id for r in recent if (datetime.now() - r.timestamp).days < 1)),
            'pending_commands': len(self.command_queue)
        }
    
    def save_config(self):
        """Persist configuration"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        config_data = {
            'nodes': {
                nid: {
                    'hostname': n.hostname,
                    'ip_address': n.ip_address,
                    'device_type': n.device_type.value,
                    'storage_capacity': n.storage_capacity_gb,
                    'storage_used': n.storage_used_gb,
                    'cpu_cores': n.cpu_cores,
                    'ram_gb': n.ram_gb,
                    'capabilities': n.capabilities,
                    'firmware': n.firmware_version
                }
                for nid, n in self.nodes.items()
            },
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_config(self):
        """Load configuration"""
        if not os.path.exists(self.config_path):
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            for node_id, node_data in config.get('nodes', {}).items():
                self.register_edge_node({
                    **node_data,
                    'device_type': node_data['device_type']
                })
            
            logger.info(f"📂 Loaded {len(self.nodes)} edge nodes")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")


# Protocol Adapters
class ProtocolAdapter:
    """Base class for communication protocols"""
    
    async def execute_optimization(self, ip: str, opt_type: str, 
                                  capabilities: List[str]) -> Dict:
        raise NotImplementedError
    
    async def execute_command(self, ip: str, cmd_type: str, 
                             params: Dict, timeout: int):
        raise NotImplementedError


class SSHAdapter(ProtocolAdapter):
    """SSH protocol adapter for Linux-based devices"""
    
    async def execute_optimization(self, ip: str, opt_type: str, 
                                  capabilities: List[str]) -> Dict:
        # Simulated SSH execution
        return {
            'success': True,
            'space_freed_bytes': hash(ip) % 1000000000,  # Simulated
            'operations': ['scan', 'cleanup_cache', 'remove_duplicates'],
            'metrics': {'duration_ms': 45000, 'files_processed': 1250}
        }
    
    async def execute_command(self, ip: str, cmd_type: str, 
                             params: Dict, timeout: int):
        pass


class HTTPAdapter(ProtocolAdapter):
    """HTTP API adapter for web-based devices"""
    
    async def execute_optimization(self, ip: str, opt_type: str, 
                                  capabilities: List[str]) -> Dict:
        # Would use aiohttp to call device REST API
        return {
            'success': True,
            'space_freed_bytes': hash(ip) % 500000000,
            'operations': ['clear_temp', 'optimize_storage'],
            'metrics': {'http_status': 200, 'response_time_ms': 2300}
        }
    
    async def execute_command(self, ip: str, cmd_type: str, 
                             params: Dict, timeout: int):
        pass


class MQTTAdapter(ProtocolAdapter):
    """MQTT protocol adapter for IoT devices"""
    
    async def execute_optimization(self, ip: str, opt_type: str, 
                                  capabilities: List[str]) -> Dict:
        return {
            'success': True,
            'space_freed_bytes': hash(ip) % 200000000,
            'operations': ['purge_logs', 'compress_records'],
            'metrics': {'mqtt_qos': 1, 'message_latency_ms': 150}
        }
    
    async def execute_command(self, ip: str, cmd_type: str, 
                             params: Dict, timeout: int):
        pass


class LocalAdapter(ProtocolAdapter):
    """Local filesystem adapter for same-machine operations"""
    
    async def execute_optimization(self, ip: str, opt_type: str, 
                                  capabilities: List[str]) -> Dict:
        return {
            'success': True,
            'space_freed_bytes': 100000000,
            'operations': ['local_cleanup'],
            'metrics': {'method': 'direct_fs_access'}
        }
    
    async def execute_command(self, ip: str, cmd_type: str, 
                             params: Dict, timeout: int):
        pass


# CLI interface
if __name__ == "__main__":
    print("🔗 EatUp Pro Edge IoT Orchestrator v5.0")
    print("="*60)
    
    orchestrator = EdgeIoTOrchestrator()
    
    # Discover devices
    print("\n🔍 Discovering edge nodes...")
    device_ids = orchestrator.discover_network_nodes()
    
    # Show network health
    health = orchestrator.get_network_health()
    print(f"\n📊 Network Health:")
    print(f"  Total Nodes: {health['total_nodes']}")
    print(f"  Online: {health['online_nodes']}")
    print(f"  Storage Used: {health['used_storage_tb']*1000:.1f} GB / {health['total_storage_tb']*1000:.1f} GB")
    print(f"  Avg Health Score: {health['average_health']:.1%}")
    
    # Simulate async optimization
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    results = loop.run_until_complete(
        orchestrator.batch_optimize(device_ids[:3])
    )
    
    # Generate report
    report = orchestrator.generate_optimization_report()
    print(f"\n📈 Report Summary:")
    print(f"  Operations: {report['summary']['total_operations']}")
    print(f"  Space Freed: {report['summary']['total_space_freed_tb']*1000:.2f} TB")
    print(f"  Success Rate: {report['summary']['success_rate']:.1%}")
