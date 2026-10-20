"""
Example Plugin 2: Duplicate Photos by SimHash
Uses perceptual hashing to find duplicate or similar photos
"""

import os
from pathlib import Path
from typing import List, Tuple
from plugins.base_plugin import BasePlugin


class DuplicatePhotosPlugin(BasePlugin):
    """Plugin to find duplicate/similar photos using hash comparison"""
    
    def __init__(self):
        self.name = "Duplicate Photo Finder"
        self.description = "Finds duplicate and similar photos using perceptual hashing"
        self.version = "1.0.0"
        
        # Image file extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    
    def get_metadata(self):
        """Return plugin metadata"""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': 'EatUp Pro Team',
            'capabilities': ['scan']
        }
    
    def customize_scan(self, scanner) -> list[str]:
        """Find all image files during scan"""
        found_images = []
        
        try:
            max_depth = 5
            
            for root, dirs, files in os.walk('C:/'):
                if root.count(os.sep) > max_depth:
                    dirs.clear()
                    continue
                
                for filename in files:
                    ext = Path(filename).suffix.lower()
                    if ext in self.image_extensions:
                        filepath = os.path.join(root, filename)
                        found_images.append(filepath)
                        
        except Exception as e:
            print(f"[PhotoPlugin] Error finding images: {e}")
        
        return found_images
    
    def calculate_simple_hash(self, filepath: str, size: int = 128) -> str:
        """Calculate a simple perceptual hash for an image"""
        try:
            from PIL import Image
            
            # Open and resize image
            img = Image.open(filepath)
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            img = img.convert('L')
            
            # Calculate average pixel value
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            
            # Create hash based on which pixels are above average
            binary = [1 if p > avg else 0 for p in pixels]
            
            # Convert to hex string
            hash_int = int("".join(map(str, binary)), 2)
            return format(hash_int, f'0{size*size}x')
            
        except ImportError:
            # Fallback: use MD5 of file content (less accurate but works without PIL)
            import hashlib
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"[PhotoPlugin] Could not hash {filepath}: {e}")
            return ""
    
    def find_similar_photos(self, images: List[Tuple[str, str]]) -> List[List[str]]:
        """Find groups of similar/duplicate photos"""
        groups = []
        hashes = {}  # hash -> list of filepaths
        
        for filepath, image_hash in images:
            if not image_hash:
                continue
            
            # Use first 16 chars for grouping (similarity threshold)
            short_hash = image_hash[:16]
            
            if short_hash not in hashes:
                hashes[short_hash] = []
            hashes[short_hash].append(filepath)
        
        # Group files with same hash
        for hash_val, files in hashes.items():
            if len(files) > 1:
                groups.append(files)
        
        return groups


if __name__ == "__main__":
    # Test the plugin
    plugin = DuplicatePhotosPlugin()
    print(f"Plugin: {plugin.get_metadata()['name']}")
    print(f"Description: {plugin.get_metadata()['description']}")
