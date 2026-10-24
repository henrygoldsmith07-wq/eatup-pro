#!/usr/bin/env python3
"""
EatUp Pro v8.1 - Advanced AR/3D Visualization Export
Multi-platform exports: Three.js (Web), Unity, Unreal Engine, Mobile AR (ARKit/ARCore)
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import colorsys


@dataclass
class FileCategoryColor:
    """Color configuration for file categories"""
    name: str
    hex_color: str
    rgb: Tuple[int, int, int]
    size_bytes: int = 0
    file_count: int = 0


class ARVisualizationExporter:
    """Export storage data to multiple AR/3D platforms"""
    
    def __init__(self):
        self.scan_results: Dict[str, Any] = {}
        self.export_timestamp = datetime.now().isoformat()
        
        # Color palette for categories
        self.category_colors = {
            'Applications': {'hex': '#3498db', 'rgb': (52, 152, 219)},
            'Documents': {'hex': '#e74c3c', 'rgb': (231, 76, 60)},
            'Media': {'hex': '#2ecc71', 'rgb': (46, 204, 113)},
            'Music': {'hex': '#9b59b6', 'rgb': (155, 89, 182)},
            'Videos': {'hex': '#f39c12', 'rgb': (243, 156, 18)},
            'Temp Files': {'hex': '#95a5a6', 'rgb': (149, 165, 166)},
            'Downloads': {'hex': '#34495e', 'rgb': (52, 73, 94)},
            'System': {'hex': '#e67e22', 'rgb': (230, 126, 34)},
            'Games': {'hex': '#1abc9c', 'rgb': (26, 188, 156)},
            'Other': {'hex': '#7f8c8d', 'rgb': (127, 140, 141)}
        }
    
    def set_scan_results(self, results: Dict[str, Any]):
        """Set scan results for visualization"""
        self.scan_results = results
    
    def export_to_threejs(self, output_file: str = 'ar_storage_3d.html') -> str:
        """
        Export interactive 3D visualization for web browsers
        Uses Three.js library for WebGL rendering
        """
        print(f"📐 Generating Three.js 3D visualization...")
        
        html_content = self._generate_threejs_html()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Three.js export saved to {output_file}")
        return output_file
    
    def _generate_threejs_html(self) -> str:
        """Generate complete HTML file with Three.js 3D scene"""
        
        # Prepare scene data
        scene_data = self._prepare_scene_data()
        
        # Generate cleanup recommendations embedded in 3D scene
        recommendations = self.scan_results.get('recommendations', [])
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EatUp Pro - Interactive 3D Storage Visualization</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
        }}
        #canvas-container {{ width: 100vw; height: 100vh; }}
        .info-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 20px;
            border-radius: 10px;
            max-width: 350px;
            z-index: 100;
        }}
        .info-panel h1 {{
            font-size: 24px;
            margin-bottom: 10px;
            color: #ffd700;
        }}
        .category-stats {{
            margin-top: 15px;
        }}
        .stat-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .category-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 2px;
            margin-right: 8px;
        }}
        .recommendation-box {{
            margin-top: 15px;
            padding: 10px;
            background: rgba(255,215,0,0.2);
            border-left: 3px solid #ffd700;
            font-size: 12px;
        }}
        #loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 24px;
        }}
    </style>
</head>
<body>
    <div id="loading">Loading 3D Scene...</div>
    <div id="canvas-container"></div>
    
    <div class="info-panel">
        <h1>🗄️ EatUp Pro Storage Map</h1>
        <p id="total-info">Total: 0 GB | Used: 0 GB</p>
        <div class="category-stats" id="category-list"></div>
        
        <div class="recommendation-box">
            <strong>💡 Cleanup Suggestions:</strong><br>
            <span id="rec-count">{len(recommendations)} optimizations available</span>
        </div>
    </div>
    
    <!-- Load Three.js from CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    
    <script>
        // Scene data from backend
        const sceneData = {json.dumps(scene_data)};
        
        // Initialize Three.js scene
        let scene, camera, renderer, controls;
        const cylinders = [];
        
        function init() {{
            // Create scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a1a2e);
            
            // Camera setup
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(20, 20, 20);
            camera.lookAt(0, 0, 0);
            
            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            document.getElementById('canvas-container').appendChild(renderer.domElement);
            
            // Orbit controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 20, 10);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
            
            // Create cylinder group
            createStorageCylinders(sceneData.categories);
            
            // Animation loop
            animate();
            
            // Remove loading message
            document.getElementById('loading').style.display = 'none';
            
            // Update stats panel
            updateStatsPanel();
        }}
        
        function createStorageCylinders(categories) {{
            const totalSize = Object.values(categories).reduce((sum, size) => sum + size, 0);
            const maxRadius = 8;
            const radiusStep = maxRadius / Math.sqrt(Object.keys(categories).length);
            
            let angle = 0;
            let index = 0;
            
            for (const [name, size] of Object.entries(categories)) {{
                const scale = Math.sqrt(size / totalSize);
                const radius = 1.5 + scale * maxRadius;
                const height = 0.5 + (size / totalSize) * 4;
                
                // Get color
                const color = {{color}}[name] || {{color}}['Other'];
                const rgb = new THREE.Color(color.rgb[0]/255, color.rgb[1]/255, color.rgb[2]/255);
                
                // Geometry
                const geometry = new THREE.CylinderGeometry(radius, radius, height, 32);
                const material = new THREE.MeshPhongMaterial({{
                    color: rgb,
                    transparent: true,
                    opacity: 0.9,
                    shininess: 100
                }});
                
                const cylinder = new THREE.Mesh(geometry, material);
                cylinder.position.x = Math.cos(angle) * radius * 1.5;
                cylinder.position.z = Math.sin(angle) * radius * 1.5;
                cylinder.position.y = height / 2;
                cylinder.castShadow = true;
                cylinder.receiveShadow = true;
                
                // Store metadata
                cylinder.userData = {{
                    category: name,
                    size: size,
                    percentage: ((size / totalSize) * 100).toFixed(1)
                }};
                
                scene.add(cylinder);
                cylinders.push(cylinder);
                
                angle += (Math.PI * 2) / Object.keys(categories).length;
                index++;
            }}
            
            // Add floor
            const floorGeometry = new THREE.PlaneGeometry(30, 30);
            const floorMaterial = new THREE.MeshPhongMaterial({{
                color: 0x2c3e50,
                side: THREE.DoubleSide
            }});
            const floor = new THREE.Mesh(floorGeometry, floorMaterial);
            floor.rotation.x = -Math.PI / 2;
            floor.position.y = 0;
            floor.receiveShadow = true;
            scene.add(floor);
        }}
        
        function updateStatsPanel() {{
            const totalSpace = {{total_space}};
            const usedSpace = {{total_used}};
            const totalGB = (totalSpace / (1024**3)).toFixed(1);
            const usedGB = (usedSpace / (1024**3)).toFixed(1);
            
            document.getElementById('total-info').innerHTML = `
                Total: <strong>${{totalGB}}</strong> GB<br>
                Used: <strong style="color: #e74c3c">${{usedGB}}</strong> GB
            `;
            
            const categoryList = document.getElementById('category-list');
            const entries = Object.entries({{categories}});
            
            entries.forEach(([name, size]) => {{
                const color = {{{{colors}}}}[name].rgb;
                const pct = ((size / usedSpace) * 100).toFixed(1);
                const gb = (size / (1024**3)).toFixed(2);
                
                const item = document.createElement('div');
                item.className = 'stat-item';
                item.innerHTML = `
                    <div>
                        <span class="category-indicator" style="background: rgb(${{color[0]}}, ${{color[1]}}, ${{color[2]}})"></span>
                        ${{name}}
                    </div>
                    <div>
                        ${{gb}} GB (${{pct}}%)
                    </div>
                `;
                categoryList.appendChild(item);
            }});
        }}
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            
            // Animate cylinders gently
            cylinders.forEach((cyl, i) => {{
                cyl.rotation.y += 0.001 * (i + 1);
            }});
            
            renderer.render(scene, camera);
        }}
        
        // Handle window resize
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
        
        // Initialize when page loads
        window.onload = init;
    </script>
</body>
</html>'''
        
        return html
    
    def export_to_unity(self, output_dir: str = 'unity_exports') -> str:
        """
        Export to Unity 3D format for mobile/desktop games
        Creates prefab configurations and material assets
        """
        print(f"🎮 Generating Unity 3D assets...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Export materials JSON (Unity will import as assets)
        materials_data = self._prepare_unity_materials()
        
        materials_file = os.path.join(output_dir, 'StorageMaterials.json')
        with open(materials_file, 'w') as f:
            json.dump(materials_data, f, indent=2)
        
        # Export prefabs configuration
        prefab_config = self._prepare_unity_prefabs()
        
        config_file = os.path.join(output_dir, 'StoragePrefabConfig.json')
        with open(config_file, 'w') as f:
            json.dump(prefab_config, f, indent=2)
        
        # Export C# script for runtime loading
        script_content = self._generate_unity_script()
        
        script_file = os.path.join(output_dir, 'StorageVisualizer.cs')
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        print(f"✅ Unity export saved to {output_dir}/")
        return output_dir
    
    def _prepare_unity_materials(self) -> Dict:
        """Prepare materials data for Unity import"""
        materials = []
        
        for category, data in self.category_colors.items():
            if self.scan_results.get('categories', {}).get(category, 0) > 0:
                materials.append({
                    'name': f'{category}_Material',
                    'color': data['hex'],
                    'category': category,
                    'size': self.scan_results['categories'].get(category, 0)
                })
        
        return {
            'version': '1.0',
            'export_date': self.export_timestamp,
            'materials': materials
        }
    
    def _prepare_unity_prefabs(self) -> Dict:
        """Generate prefab configuration data"""
        categories = self.scan_results.get('categories', {})
        
        prefabs = []
        total_size = sum(categories.values()) or 1
        
        for category, size in categories.items():
            if size > 0:
                prefabs.append({
                    'prefab_name': f'Category_{category}',
                    'material': f'{category}_Material',
                    'scale': (size / total_size) ** 0.33,
                    'position_offset': len(prefabs),
                    'active': True
                })
        
        return {
            'scene_name': 'StorageVisualization',
            'prefabs': prefabs,
            'camera_position': {'x': 20, 'y': 20, 'z': 20}
        }
    
    def _generate_unity_script(self) -> str:
        """Generate Unity C# script for runtime visualization"""
        return '''using UnityEngine;
using System.Collections.Generic;
using System.IO;

public class StorageVisualizer : MonoBehaviour
{{
    [Header("Configuration")]
    public string jsonDataPath = "StorageMaterials.json";
    public float baseScale = 2.0f;
    public float cylinderHeightMultiplier = 1.0f;
    
    private Dictionary<string, Material> materialCache = new Dictionary<string, Material>();
    
    void Start()
    {{
        LoadAndCreateScene();
    }}
    
    void LoadAndCreateScene()
    {{
        string jsonPath = Path.Combine(Application.dataPath, "..", jsonDataPath);
        
        if (File.Exists(jsonPath))
        {{
            string json = File.ReadAllText(jsonPath);
            MaterialData[] materials = Json.Deserialize(json) as MaterialData[];
            
            CreateCylinderScene(materials);
        }}
        else
        {{
            Debug.Log("JSON file not found: " + jsonPath);
        }}
    }}
    
    void CreateCylinderScene(MaterialData[] materials)
    {{
        GameObject parent = new GameObject("StorageCategories");
        
        for (int i = 0; i < materials.Length; i++)
        {{
            MaterialData matData = materials[i];
            
            // Create cylinder
            GameObject cylinder = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            cylinder.name = matData.category;
            cylinder.transform.SetParent(parent.transform);
            
            // Apply material
            if (!materialCache.ContainsKey(matData.material))
            {{
                LoadMaterial(matData.material, out Material mat);
                materialCache[matData.material] = mat;
            }}
            
            cylinder.GetComponent<MeshRenderer>().material = materialCache[matData.material];
            
            // Scale based on data
            float scale = Mathf.Pow(matData.size / 1024.0f, 0.3f) * baseScale;
            cylinder.transform.localScale = new Vector3(scale, scale * cylinderHeightMultiplier, scale);
            
            // Position around circle
            float angle = (float)i / materials.Length * Mathf.PI * 2;
            float radius = 5.0f;
            cylinder.transform.localPosition = new Vector3(
                Mathf.Cos(angle) * radius,
                scale * cylinderHeightMultiplier / 2,
                Mathf.Sin(angle) * radius
            );
        }}
    }}
    
    void LoadMaterial(string materialName, out Material material)
    {{
        // In production, load from serialized asset
        // For now, create procedural material
        material = new Material(Shader.Find("Standard"));
        
        // Parse hex color from material name
        Color color = HexToColor(materialName.Replace("_Material", ""));
        material.color = color;
    }}
    
    Color HexToColor(string hex)
    {{
        // Parse #RRGGBB format
        byte r = byte.Parse(hex.Substring(1, 2), System.Globalization.NumberStyles.HexNumber);
        byte g = byte.Parse(hex.Substring(3, 2), System.Globalization.NumberStyles.HexNumber);
        byte b = byte.Parse(hex.Substring(5, 2), System.Globalization.NumberStyles.HexNumber);
        
        return new Color(r / 255f, g / 255f, b / 255f);
    }}
}}

[System.Serializable]
public class MaterialData
{{
    public string name;
    public string material;
    public string category;
    public float size;
}}
'''
    
    def export_to_unreal(self, output_dir: str = 'unreal_exports') -> str:
        """
        Export to Unreal Engine 5 format
        Creates Blueprint-compatible data structures
        """
        print(f"🎯 Generating Unreal Engine 5 assets...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Export UBlueprint data structure
        blueprint_data = {
            'ClassVersion': '5',
            'ImportedFrom': 'EatUp Pro v8.1',
            'Categories': [],
            'Lighting': {
                'WorldLightingMode': 'Realtime',
                'BounceResolution': 64
            }
        }
        
        for category, size in self.scan_results.get('categories', {}).items():
            if size > 0:
                color = self.category_colors.get(category, self.category_colors['Other'])
                
                blueprint_data['Categories'].append({
                    'Name': category,
                    'CMaterialColor': list(color['rgb']),
                    'InstanceSize': float(size),
                    'PercentOfTotal': (size / sum(self.scan_results.get('categories', {}).values())) * 100
                })
        
        # Save blueprint structure
        blueprint_file = os.path.join(output_dir, 'BP_StorageVisualizer.json')
        with open(blueprint_file, 'w') as f:
            json.dump(blueprint_data, f, indent=2)
        
        # Export actor data
        actor_data = {
            'ActorType': 'StaticMeshActor',
            'Mobility': 'Movable',
            'Transform': {
                'Location': [0, 0, 100],
                'Rotation': [0, 0, 0],
                'Scale3D': [1.0, 1.0, 1.0]
            },
            'Components': [
                {
                    'ComponentId': 'RootComponent',
                    'ComponentType': 'SphereComponent',
                    'CollisionEnabled': 'NoCollision',
                    'SphereRadius': 1000
                }
            ]
        }
        
        actor_file = os.path.join(output_dir, 'StorageVisualizerActor.json')
        with open(actor_file, 'w') as f:
            json.dump(actor_data, f, indent=2)
        
        print(f"✅ Unreal Engine 5 export saved to {output_dir}/")
        return output_dir
    
    def export_to_mobile_ar(self, output_dir: str = 'mobile_ar') -> str:
        """
        Export to mobile AR format (ARKit/ARCore compatible)
        Lightweight JSON for iOS/Android devices
        """
        print(f"📱 Generating mobile AR (ARKit/ARCore) export...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        ar_export = {
            'version': '1.0',
            'format': 'arkit-arcore-unified',
            'metadata': {
                'generated_by': 'EatUp Pro v8.1',
                'timestamp': self.export_timestamp,
                'device_compatibility': ['iOS 12+', 'Android 7+']
            },
            'scene': {
                'worldOrigin': [0, 0, 0],
                'upAxis': 'Y',
                'lighting': 'environment_estimated'
            },
            'anchors': [],
            'geometry': [],
            'quick_actions': [
                {
                    'action': 'cleanup_temp',
                    'label': 'Clean Temporary Files',
                    'icon': 'trash.fill',
                    'color': '#95a5a6'
                },
                {
                    'action': 'view_largest',
                    'label': 'Largest Files',
                    'icon': 'arrow.up.circle.fill',
                    'color': '#e74c3c'
                },
                {
                    'action': 'show_details',
                    'label': 'Details',
                    'icon': 'info.circle.fill',
                    'color': '#3498db'
                }
            ]
        }
        
        # Calculate totals
        categories = self.scan_results.get('categories', {})
        total_size = sum(categories.values()) or 1
        
        # Create anchors and geometry for each category
        for idx, (category, size) in enumerate(categories.items()):
            if size > 0:
                color = self.category_colors.get(category, self.category_colors['Other'])
                
                anchor_id = f'anchor_{idx}'
                geo_id = f'geo_{idx}'
                
                ar_export['anchors'].append({
                    'id': anchor_id,
                    'transform': {
                        'translation': [idx * 2.0, 0, 0],
                        'rotation': [0, 0, 0, 1]  # Quaternion
                    },
                    'placement': 'horizontal'
                })
                
                ar_export['geometry'].append({
                    'id': geo_id,
                    'anchor_id': anchor_id,
                    'type': 'cylinder',
                    'dimensions': {
                        'radius': 0.5 + (size / total_size) * 2.0,
                        'height': 0.3 + (size / total_size) * 1.5,
                        'segments': 16
                    },
                    'material': {
                        'color': color['hex'],
                        'metallic': 0.3,
                        'roughness': 0.7
                    },
                    'metadata': {
                        'category': category,
                        'size_bytes': size,
                        'size_gb': round(size / (1024**3), 2)
                    }
                })
        
        # Save AR export
        ar_file = os.path.join(output_dir, 'storage_ar_scene.json')
        with open(ar_file, 'w') as f:
            json.dump(ar_export, f, indent=2)
        
        # Generate AR quick view HTML for preview
        preview_html = self._generate_ar_preview()
        
        preview_file = os.path.join(output_dir, 'preview_ar_view.html')
        with open(preview_file, 'w') as f:
            f.write(preview_html)
        
        print(f"✅ Mobile AR export saved to {output_dir}/")
        print(f"   Preview at: {preview_file}")
        
        return output_dir
    
    def _generate_ar_preview(self) -> str:
        """Generate HTML preview for AR scene"""
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>AR Preview - EatUp Pro</title>
    <style>
        body {{ margin: 0; background: #000; color: white; font-family: Arial; }}
        #viewer {{ width: 100vw; height: 100vh; }}
        .info {{ 
            position: absolute; top: 10px; left: 10px; 
            background: rgba(0,0,0,0.7); padding: 10px; 
        }}
    </style>
</head>
<body>
    <div class="info">AR Scene Preview - EatUp Pro v8.1</div>
    <div id="viewer">
        <p>Load this JSON into your AR app:<br>
        <code id="json-path">storage_ar_scene.json</code></p>
    </div>
</body>
</html>'''
    
    def export_all_formats(self, base_dir: str = 'ar_exports') -> Dict[str, str]:
        """Export to all supported formats"""
        print("\n🚀 Starting multi-format AR export...\n")
        
        os.makedirs(base_dir, exist_ok=True)
        
        exports = {}
        
        try:
            exports['threejs'] = self.export_to_threejs(
                os.path.join(base_dir, 'web/ar_storage_3d.html')
            )
        except Exception as e:
            print(f"❌ Three.js export failed: {e}")
        
        try:
            exports['unity'] = self.export_to_unity(
                os.path.join(base_dir, 'unity')
            )
        except Exception as e:
            print(f"❌ Unity export failed: {e}")
        
        try:
            exports['unreal'] = self.export_to_unreal(
                os.path.join(base_dir, 'unreal')
            )
        except Exception as e:
            print(f"❌ Unreal export failed: {e}")
        
        try:
            exports['mobile_ar'] = self.export_to_mobile_ar(
                os.path.join(base_dir, 'mobile_ar')
            )
        except Exception as e:
            print(f"❌ Mobile AR export failed: {e}")
        
        print("\n✅ All exports completed!")
        return exports


if __name__ == '__main__':
    # Demo mode
    print("=" * 60)
    print("EatUp Pro AR Visualization Exporter v8.1")
    print("=" * 60)
    
    exporter = ARVisualizationExporter()
    
    # Sample data for demo
    demo_results = {
        'categories': {
            'Applications': 214748364800,  # 200 GB
            'Documents': 107374182400,     # 100 GB
            'Media': 536870912000,         # 500 GB
            'Music': 53687091200,          # 50 GB
            'Videos': 214748364800,        # 200 GB
            'Temp Files': 21474836480,     # 20 GB
            'Downloads': 107374182400,     # 100 GB
            'System': 42949672960,         # 40 GB
            'Games': 322122547200,         # 300 GB
            'Other': 10737418240           # 10 GB
        },
        'total_used': 1734123456704,
        'total_space': 2000000000000,
        'recommendations': [
            {'type': 'temp_cleanup', 'potential_savings_gb': 20},
            {'type': 'duplicate_removal', 'potential_savings_gb': 15}
        ]
    }
    
    exporter.set_scan_results(demo_results)
    
    # Export to all formats
    exports = exporter.export_all_formats('demo_ar_exports')
    
    print(f"\n📊 Export Summary:")
    for format_type, path in exports.items():
        print(f"  • {format_type}: {path}")
