"""
EatUp Pro - AR Data Export & 3D Visualization v2.0

Export disk usage data for Augmented Reality visualization and 3D rendering.
Perfect for immersive disk management experiences.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from datetime import datetime
import math


@dataclass
class File3DNode:
    """Represents a file/directory for 3D visualization"""
    id: str
    name: str
    path: str
    size_bytes: int
    file_type: str
    depth: int
    children: List[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class DiskUsageChunk:
    """Data chunk for AR visualization"""
    category: str
    total_size_gb: float
    file_count: int
    color_hex: str
    priority: int  # 1=highest (most junk), 5=lowest
    representative_files: List[str]


@dataclass
class ARVisualizationData:
    """Complete dataset for AR/3D visualization"""
    timestamp: str
    drive_name: str
    total_capacity_gb: float
    used_gb: float
    free_gb: float
    utilization_percent: float
    chunks: List[DiskUsageChunk]
    tree_structure: List[File3DNode]
    recommendations: List[Dict]
    export_version: str = "2.0"


class ARDataExporter:
    """
    Export disk usage data for AR/VR visualization platforms.
    Supports formats compatible with Three.js, Unity, Unreal Engine.
    """
    
    # Category colors for visualization
    CATEGORY_COLORS = {
        'Applications': '#3B82F6',      # Blue
        'Videos': '#10B981',             # Green
        'Documents': '#8B5CF6',          # Purple
        'Images': '#F59E0B',             # Orange
        'Music': '#EF4444',              # Red
        'Downloads': '#06B6D4',          # Cyan
        'System': '#6B7280',             # Gray
        'Temporary': '#EC4899',          # Pink
        'Duplicates': '#84CC16',         # Lime
        'Large Files': '#F97316',        # Amber
        'Other': '#A78BFA'               # Light Purple
    }
    
    PRIORITY_SCORES = {
        'Temporary': 1,   # Clean first
        'Duplicates': 1,
        'Downloads': 2,
        'Large Files': 3,
        'Applications': 4,
        'Videos': 4,
        'Documents': 5,
        'Images': 5,
        'Music': 5,
        'System': 5,
        'Other': 3
    }
    
    def __init__(self):
        self.export_history: List[Dict] = []
    
    def export_for_ar(self, scan_results: Any, 
                     categories: Dict[str, int],
                     cleanable_info: Dict) -> ARVisualizationData:
        """
        Create AR-ready visualization data from scan results.
        
        Args:
            scan_results: From cleaner.scan_drive()
            categories: Dict of category names to byte counts
            cleanable_info: Info about cleanable files
        
        Returns:
            ARVisualizationData object ready for export
        """
        total_used = scan_results.total_used if hasattr(scan_results, 'total_used') else sum(categories.values())
        total_space = scan_results.total_space if hasattr(scan_results, 'total_space') else total_used * 2
        
        # Build chunks for visualization
        chunks = []
        for category, size_bytes in categories.items():
            size_gb = size_bytes / (1024**3)
            
            # Estimate file count (very rough approximation)
            avg_file_size = 1024**2  # Assume 1MB average
            file_count = int(size_bytes / max(avg_file_size, 1))
            
            chunks.append(DiskUsageChunk(
                category=category,
                total_size_gb=round(size_gb, 2),
                file_count=file_count,
                color_hex=self.CATEGORY_COLORS.get(category, '#CCCCCC'),
                priority=self.PRIORITY_SCORES.get(category, 5),
                representative_files=[]  # Would be populated from scan
            ))
        
        # Sort by size (largest first)
        chunks.sort(key=lambda x: x.total_size_gb, reverse=True)
        
        # Generate simplified tree structure
        tree_structure = self._generate_tree_structure(categories)
        
        # Get cleanup recommendations
        recommendations = self._generate_recommendations(cleanable_info, chunks)
        
        return ARVisualizationData(
            timestamp=datetime.now().isoformat(),
            drive_name=scan_results.drive if hasattr(scan_results, 'drive') else "C:",
            total_capacity_gb=round(total_space / (1024**3), 2),
            used_gb=round(total_used / (1024**3), 2),
            free_gb=round((total_space - total_used) / (1024**3), 2),
            utilization_percent=round((total_used / total_space) * 100, 1),
            chunks=chunks,
            tree_structure=tree_structure,
            recommendations=recommendations
        )
    
    def _generate_tree_structure(self, categories: Dict[str, int]) -> List[File3DNode]:
        """Generate simplified directory tree for visualization"""
        nodes = []
        root_id = "root"
        
        current_depth = 0
        for category, size_bytes in categories.items():
            node = File3DNode(
                id=f"{category.lower().replace(' ', '_')}",
                name=category,
                path=f"/{category}",
                size_bytes=size_bytes,
                file_type="directory",
                depth=current_depth,
                children=[]
            )
            nodes.append(node)
        
        # Add root node
        total_size = sum(categories.values())
        root_node = File3DNode(
            id=root_id,
            name="Drive Root",
            path="/",
            size_bytes=total_size,
            file_type="directory",
            depth=0,
            children=[n.id for n in nodes]
        )
        nodes.insert(0, root_node)
        
        return nodes
    
    def _generate_recommendations(self, cleanable_info: Dict, 
                                  chunks: List[DiskUsageChunk]) -> List[Dict]:
        """Generate prioritized cleanup recommendations"""
        recommendations = []
        
        # Priority 1: Temporary files
        temp_gb = cleanable_info.get('temp_files_count', 0) / 1000  # Rough estimate
        if temp_gb > 0:
            recommendations.append({
                'priority': 1,
                'action': 'Clean temporary files',
                'space_saving_gb': round(temp_gb, 2),
                'risk_level': 'low',
                'description': 'Safe to remove system temp files'
            })
        
        # Priority 2: Duplicates
        dup_gb = cleanable_info.get('duplicate_groups', 0) * 0.5  # Avg 500MB per group
        if dup_gb > 0:
            recommendations.append({
                'priority': 1,
                'action': 'Remove duplicate files',
                'space_saving_gb': round(dup_gb, 2),
                'risk_level': 'low',
                'description': 'Eliminate redundant copies'
            })
        
        # Priority 3: Large files review
        large_count = cleanable_info.get('large_files_count', 0)
        if large_count > 0:
            recommendations.append({
                'priority': 2,
                'action': 'Review large files',
                'potential_savings_gb': round(large_count * 2.0, 2),
                'risk_level': 'medium',
                'description': f'Review {large_count} files >1GB manually'
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'])
        
        return recommendations
    
    def export_three_js(self, ar_data: ARVisualizationData, 
                       output_path: str = "data/ar_exports/threejs_disks.json"):
        """
        Export data for Three.js web-based 3D visualization.
        
        Compatible with: https://threejs.org/
        """
        export_data = {
            'metadata': {
                'version': ar_data.export_version,
                'timestamp': ar_data.timestamp,
                'drive': ar_data.drive_name,
                'total_capacity_gb': ar_data.total_capacity_gb,
                'used_percentage': ar_data.utilization_percent
            },
            'globe_data': {
                'total_volume_gb': ar_data.used_gb,
                'free_volume_gb': ar_data.free_gb,
                'utilization': ar_data.utilization_percent / 100
            },
            'categories': [{
                'name': chunk.category,
                'size_gb': chunk.total_size_gb,
                'color': chunk.color_hex,
                'file_count': chunk.file_count,
                'priority': chunk.priority,
                'geometry': self._calculate_geometry(chunk.total_size_gb, ar_data.total_capacity_gb)
            } for chunk in ar_data.chunks],
            'interactions': {
                'click_action': 'show_details',
                'hover_tooltip': True,
                'expand_on_click': True
            }
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Three.js export saved to {output_path}")
        return output_path
    
    def export_unity_format(self, ar_data: ARVisualizationData,
                           output_path: str = "data/ar_exports/unity_disks.json"):
        """
        Export data for Unity 3D engine.
        
        Format suitable for Unity's 3D visualization system.
        """
        unity_data = {
            'project_name': 'EatUp Pro Disk Visualizer',
            'data_version': ar_data.export_version,
            'scene_settings': {
                'camera_position': {'x': 0, 'y': 0, 'z': 10},
                'light_intensity': 0.8,
                'background_color': '#1a1a2e'
            },
            'objects': [],
            'ui_labels': [
                {'text': f"Total: {ar_data.total_capacity_gb:.1f} GB", 'position': {'x': -200, 'y': 300}},
                {'text': f"Used: {ar_data.used_gb:.1f} GB ({ar_data.utilization_percent:.1f}%)", 'position': {'x': -200, 'y': 250}},
                {'text': f"Free: {ar_data.free_gb:.1f} GB", 'position': {'x': -200, 'y': 200}}
            ]
        }
        
        for i, chunk in enumerate(ar_data.chunks):
            angle = (i / len(ar_data.chunks)) * 2 * math.pi
            radius = 5
            
            unity_data['objects'].append({
                'name': f"Category_{chunk.category}",
                'type': 'cylinder',
                'material': {
                    'color': chunk.color_hex,
                    'emissive': chunk.color_hex,
                    'metallic': 0.3,
                    'smoothness': 0.5
                },
                'scale': {
                    'x': chunk.total_size_gb / 10,  # Scale by size
                    'y': 2,
                    'z': 1
                },
                'position': {
                    'x': radius * math.cos(angle),
                    'y': 0,
                    'z': radius * math.sin(angle)
                },
                'rotation': {'x': 0, 'y': 0, 'z': 0},
                'properties': {
                    'file_count': chunk.file_count,
                    'priority': chunk.priority
                }
            })
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(unity_data, f, indent=2)
        
        print(f"✅ Unity export saved to {output_path}")
        return output_path
    
    def export_unreal_format(self, ar_data: ARVisualizationData,
                            output_path: str = "data/ar_exports/unreal_disks.json"):
        """
        Export data for Unreal Engine.
        
        Blueprint-compatible JSON format.
        """
        unreal_data = {
            'level_name': 'DiskUsageVisualization',
            'export_date': ar_data.timestamp,
            'actors': [],
            'billboard_text': {
                'title': f"Storage Analysis: {ar_data.drive_name}",
                'metrics': [
                    f"Total Capacity: {ar_data.total_capacity_gb:.1f} GB",
                    f"Used Space: {ar_data.used_gb:.1f} GB",
                    f"Available Space: {ar_data.free_gb:.1f} GB",
                    f"Utilization: {ar_data.utilization_percent:.1f}%"
                ]
            }
        }
        
        # Create column actors for each category
        total_width = len(ar_data.chunks) * 2
        offset = -total_width / 2 + 1
        
        for chunk in ar_data.chunks:
            height = min(chunk.total_size_gb / 5, 10)  # Cap height at 10 units
            
            unreal_data['actors'].append({
                'actor_class': 'DynamicBoxComponent',
                'name': f"AR_Category_{chunk.category.replace(' ', '_')}",
                'location': {'x': offset, 'y': 0, 'z': height / 2},
                'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0},
                'scale': {'x': 1.5, 'y': 1.5, 'z': height},
                'materials': [{
                    'name': 'Primary',
                    'diffuse_color': self._hex_to_vector(chunk.color_hex),
                    'emmissive_color': self._hex_to_vector(chunk.color_hex),
                    'metallic': 0.2,
                    'roughness': 0.6
                }],
                'collision': {
                    'enabled': True,
                    'response': 'Overlap'
                },
                'blueprint_variables': {
                    'category_name': chunk.category,
                    'size_gb': chunk.total_size_gb,
                    'file_count': chunk.file_count,
                    'priority_level': chunk.priority
                }
            })
            
            offset += 2  # Gap between columns
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(unreal_data, f, indent=2)
        
        print(f"✅ Unreal Engine export saved to {output_path}")
        return output_path
    
    def _calculate_geometry(self, size_gb: float, total_gb: float) -> Dict:
        """Calculate 3D geometry parameters based on data size"""
        ratio = size_gb / total_gb if total_gb > 0 else 0
        
        return {
            'type': 'cylinder',
            'radius_bottom': 1 + ratio * 3,
            'radius_top': 1 + ratio * 3,
            'height': ratio * 10,
            'segments': 32
        }
    
    def _hex_to_vector(self, hex_color: str) -> List[float]:
        """Convert hex color to RGB vector (0-1 range)"""
        hex_color = hex_color.lstrip('#')
        return [
            int(hex_color[i:i+2], 16) / 255.0
            for i in (0, 2, 4)
        ]
    
    def export_mobile_compatible(self, ar_data: ARVisualizationData,
                                output_path: str = "data/ar_exports/mobile_disks.json"):
        """
        Optimized export for mobile AR apps (ARKit/ARCore).
        
        Lightweight format with essential data only.
        """
        mobile_data = {
            'schema_version': '1.0',
            'generated_at': ar_data.timestamp,
            'summary': {
                'storage_used_gb': ar_data.used_gb,
                'storage_free_gb': ar_data.free_gb,
                'utilization_percent': ar_data.utilization_percent
            },
            'augmented_layers': []
        }
        
        # Simplified data for mobile performance
        for chunk in ar_data.chunks[:6]:  # Limit to top 6 categories
            mobile_data['augmented_layers'].append({
                'layer_name': chunk.category,
                'icon_uri': f"assets/icons/{chunk.category.lower()}.png",
                'primary_metric': f"{chunk.total_size_gb:.1f} GB",
                'secondary_metric': f"{chunk.file_count:,} files",
                'color_hex': chunk.color_hex,
                'tap_action': 'show_file_list'
            })
        
        # Quick actions overlay
        mobile_data['quick_actions'] = [
            {'label': 'Scan Now', 'icon': 'scan', 'action': 're_scan'},
            {'label': 'Clean Junk', 'icon': 'clean', 'action': 'cleanup'},
            {'label': 'Find Duplicates', 'icon': 'duplicate', 'action': 'find_dupes'}
        ]
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(mobile_data, f, indent=2)
        
        print(f"✅ Mobile AR export saved to {output_path}")
        return output_path
    
    def save_all_formats(self, ar_data: ARVisualizationData):
        """Export to all supported formats"""
        base_path = "data/ar_exports/"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exports = {
            'threejs': self.export_three_js,
            'unity': self.export_unity_format,
            'unreal': self.export_unreal_format,
            'mobile': self.export_mobile_compatible
        }
        
        for format_name, export_func in exports.items():
            output_file = f"{base_path}{format_name}_disks_{timestamp}.json"
            export_func(ar_data, output_file)
        
        print(f"\n📦 All exports completed! Check {base_path}/")


# CLI interface
if __name__ == "__main__":
    print("🕶️ EatUp Pro AR Data Exporter")
    print("=" * 40)
    
    from cleaner import EatUpCleaner
    
    # Perform scan
    print("\n🔍 Scanning drive for AR data...")
    cleaner = EatUpCleaner()
    result = cleaner.scan_drive("C:")
    
    # Prepare cleanable info
    cleanable_info = {
        'temp_files_count': len(cleaner.temp_files),
        'duplicate_groups': len(cleaner.duplicates),
        'large_files_count': len(cleaner.large_files)
    }
    
    # Export
    exporter = ARDataExporter()
    ar_data = exporter.export_for_ar(result, cleaner.categories, cleanable_info)
    
    print(f"\n📊 Generated visualization data:")
    print(f"  Drive: {ar_data.drive_name}")
    print(f"  Used: {ar_data.used_gb:.1f} GB / {ar_data.total_capacity_gb:.1f} GB")
    print(f"  Categories: {len(ar_data.chunks)}")
    
    # Save all formats
    exporter.save_all_formats(ar_data)
    
    print("\n💡 Tip: Import these files into your preferred 3D platform!")
