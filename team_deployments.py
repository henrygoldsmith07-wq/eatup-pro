#!/usr/bin/env python3
"""
EatUp Pro - Team Deployment Manager
Manages multiple machines, central policies, and aggregate reporting
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import socket


@dataclass
class MachineConfig:
    """Configuration for a machine in the team"""
    machine_id: str
    hostname: str
    ip_address: str
    last_reported: Optional[datetime] = None
    status: str = "active"  # active, inactive, offline
    drive_paths: List[str] = None
    enabled_plugins: List[str] = None
    schedule_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.drive_paths is None:
            self.drive_paths = ["C:"]
        if self.enabled_plugins is None:
            self.enabled_plugins = []


@dataclass
class PolicyRule:
    """Policy rule for team deployment"""
    id: str
    name: str
    description: str
    priority: int  # 1-10, higher = more important
    conditions: Dict[str, Any] = None  # When to apply
    actions: Dict[str, Any] = None  # What to do
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}
        if self.actions is None:
            self.actions = {}


@dataclass
class ComplianceReport:
    """Compliance report for team audit"""
    report_date: datetime
    total_machines: int
    compliant_machines: int
    non_compliant_machines: int
    compliance_score: float
    issues_found: List[Dict[str, Any]]
    
    @property
    def compliance_percentage(self) -> float:
        if self.total_machines == 0:
            return 100.0
        return (self.compliant_machines / self.total_machines) * 100


class TeamDeploymentManager:
    """Manages team deployment of EatUp Pro"""
    
    def __init__(self, config_file: str = "team_config.json"):
        self.config_file = config_file
        self.machines: Dict[str, MachineConfig] = {}
        self.policies: Dict[str, PolicyRule] = {}
        self.history: List[Dict[str, Any]] = []
        
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct objects
                for machine_id, m_data in data.get('machines', {}).items():
                    machine = MachineConfig(**m_data)
                    self.machines[machine_id] = machine
                
                for policy_id, p_data in data.get('policies', {}).items():
                    policy = PolicyRule(**p_data)
                    self.policies[policy_id] = policy
                    
                print(f"Loaded {len(self.machines)} machines, {len(self.policies)} policies")
        
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            data = {
                'machines': {k: asdict(v) for k, v in self.machines.items()},
                'policies': {k: asdict(v) for k, v in self.policies.items()}
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print("Configuration saved successfully")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def register_machine(self, hostname: str, ip_address: str, drive_paths: List[str] = None) -> str:
        """Register a new machine to the team"""
        machine_id = f"{hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        machine = MachineConfig(
            machine_id=machine_id,
            hostname=hostname,
            ip_address=ip_address,
            drive_paths=drive_paths or ["C:"],
            enabled_plugins=["cleanup_plugin", "scan_extension"],
            status="active"
        )
        
        self.machines[machine_id] = machine
        self.save_config()
        
        print(f"Registered machine: {machine_id}")
        return machine_id
    
    def unregister_machine(self, machine_id: str) -> bool:
        """Unregister a machine from the team"""
        if machine_id in self.machines:
            del self.machines[machine_id]
            self.save_config()
            return True
        return False
    
    def add_policy(self, policy: PolicyRule):
        """Add a new policy rule"""
        self.policies[policy.id] = policy
        self.save_config()
        print(f"Added policy: {policy.name}")
    
    def get_applicable_policies(self, machine_id: str) -> List[PolicyRule]:
        """Get policies applicable to a specific machine"""
        machine = self.machines.get(machine_id)
        if not machine:
            return []
        
        applicable = []
        for policy in self.policies.values():
            # Check if policy applies to this machine
            conditions = policy.conditions
            
            # Check machine_id condition
            if 'machine_ids' in conditions:
                if machine_id not in conditions['machine_ids']:
                    continue
            
            # Check IP range condition
            if 'ip_ranges' in conditions:
                ip_ok = any(
                    ip.startswith(range_str.split('-')[0])
                    for range_str in conditions['ip_ranges']
                )
                if not ip_ok:
                    continue
            
            # No specific conditions, apply to all
            applicable.append(policy)
        
        # Sort by priority
        applicable.sort(key=lambda p: p.priority, reverse=True)
        
        return applicable
    
    def execute_policy_actions(self, machine_id: str, action_type: str):
        """Execute policy actions on a machine"""
        policies = self.get_applicable_policies(machine_id)
        
        for policy in policies:
            if action_type in policy.actions:
                action = policy.actions[action_type]
                
                print(f"Executing policy action on {machine_id}:")
                print(f"  Policy: {policy.name}")
                print(f"  Action: {action}")
                
                # Here you would actually call the EatUp APIs
                # For now, log the action
                self.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'machine_id': machine_id,
                    'policy_id': policy.id,
                    'action_type': action_type,
                    'status': 'executed'
                })
    
    def generate_compliance_report(self) -> ComplianceReport:
        """Generate compliance report for all machines"""
        total = len(self.machines)
        compliant = 0
        issues = []
        
        for machine_id, machine in self.machines.items():
            # Check if machine is active and reporting
            if machine.status != "active":
                issues.append({
                    'machine_id': machine_id,
                    'issue': 'Machine not active',
                    'severity': 'high'
                })
                continue
            
            # Check if all required plugins are enabled
            required_plugins = ['cleanup_plugin', 'scan_extension']
            missing_plugins = [
                p for p in required_plugins 
                if p not in machine.enabled_plugins
            ]
            
            if missing_plugins:
                issues.append({
                    'machine_id': machine_id,
                    'issue': f'Missing plugins: {missing_plugins}',
                    'severity': 'medium'
                })
                continue
            
            # Check recent activity
            if machine.last_reported:
                hours_ago = (datetime.now() - machine.last_reported).total_seconds() / 3600
                if hours_ago > 24:  # Not reported in 24 hours
                    issues.append({
                        'machine_id': machine_id,
                        'issue': 'No recent reports (>24h)',
                        'severity': 'low'
                    })
                    continue
            
            compliant += 1
        
        return ComplianceReport(
            report_date=datetime.now(),
            total_machines=total,
            compliant_machines=compliant,
            non_compliant_machines=total - compliant,
            compliance_score=(compliant / total * 100) if total > 0 else 100,
            issues_found=issues
        )
    
    def deploy_scan_schedule(self, schedule_config: Dict[str, Any]):
        """Deploy scan schedule to all machines"""
        for machine_id in self.machines:
            machine = self.machines[machine_id]
            machine.schedule_config = schedule_config
            self.execute_policy_actions(machine_id, 'deploy_schedule')
        
        print(f"Deployed scan schedule to {len(self.machines)} machines")
    
    def force_cleanup_all(self, cleanup_type: str = 'smart'):
        """Force cleanup operation on all machines"""
        for machine_id in self.machines:
            self.execute_policy_actions(machine_id, f'start_{cleanup_type}_cleanup')
        
        print(f"Triggered {cleanup_type} cleanup on {len(self.machines)} machines")
    
    def get_team_analytics(self) -> Dict[str, Any]:
        """Get aggregate analytics for entire team"""
        return {
            'total_machines': len(self.machines),
            'active_machines': sum(1 for m in self.machines.values() if m.status == 'active'),
            'offline_machines': sum(1 for m in self.machines.values() if m.status == 'offline'),
            'last_update': max(
                (m.last_reported for m in self.machines.values() if m.last_reported),
                default=None
            ),
            'policies_count': len(self.policies),
            'recent_actions': len(self.history)
        }
    
    def export_audit_log(self, filename: str = "audit_log.json"):
        """Export audit log for compliance"""
        with open(filename, 'w') as f:
            json.dump(self.history, f, indent=2)
        
        print(f"Audit log exported to {filename}")
    
    def sync_with_server(self, server_url: str):
        """Sync local state with central server (placeholder)"""
        print(f"Would sync with server at: {server_url}")
        # Implementation would use REST API calls
    
    def backup_config(self, backup_dir: str = "backups"):
        """Create backup of configuration"""
        Path(backup_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = Path(backup_dir) / f"team_config_backup_{timestamp}.json"
        
        # Save backup
        data = {
            'machines': {k: asdict(v) for k, v in self.machines.items()},
            'policies': {k: asdict(v) for k, v in self.policies.items()},
            'history': self.history[-100:]  # Last 100 entries
        }
        
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Backup created: {backup_file}")


def main():
    """Demo team deployment"""
    print("=" * 70)
    print("EATUP PRO - TEAM DEPLOYMENT MANAGER")
    print("=" * 70)
    
    manager = TeamDeploymentManager()
    
    # Register some test machines
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"\nRegistering local machine...")
    machine_id = manager.register_machine(
        hostname=hostname,
        ip_address=f"{local_ip.replace(local_ip.split('.')[-1], '100')}",
        drive_paths=["C:", "D:"]
    )
    
    # Add another test machine
    print("\nRegistering second test machine...")
    manager.register_machine(
        hostname="WORKSTATION-02",
        ip_address="192.168.1.101",
        drive_paths=["C:"]
    )
    
    print(f"\nTotal registered: {len(manager.machines)}")
    
    # Add a policy
    print("\nAdding compliance policy...")
    policy = PolicyRule(
        id="policy_basic_cleanup",
        name="Basic Cleanup Policy",
        description="Ensure all machines run weekly cleanup",
        priority=5,
        conditions={'min_cpu_usage': 50},
        actions={'start_smart_cleanup': {'enabled': True}}
    )
    manager.add_policy(policy)
    
    # Generate compliance report
    print("\nGenerating compliance report...")
    report = manager.generate_compliance_report()
    
    print(f"\nTeam Compliance Report:")
    print(f"  Total Machines: {report.total_machines}")
    print(f"  Compliant: {report.compliant_machines}")
    print(f"  Score: {report.compliance_score:.1f}%")
    
    # Get team analytics
    print("\nTeam Analytics:")
    analytics = manager.get_team_analytics()
    print(f"  Active machines: {analytics['active_machines']}")
    print(f"  Policies deployed: {analytics['policies_count']}")


if __name__ == "__main__":
    main()
