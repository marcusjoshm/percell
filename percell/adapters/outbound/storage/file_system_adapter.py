"""
File system adapter implementation for Percell.

Implements the StoragePort interface for file system operations.
"""

import os
import json
import shutil
import time
from typing import List, Optional, Dict, Any, Iterator
from pathlib import Path
import numpy as np
from PIL import Image as PILImage
import zipfile
import glob

from percell.ports.outbound.storage_port import StoragePort, StorageError
from percell.domain.entities.image import Image
from percell.domain.entities.roi import ROI
from percell.domain.value_objects.file_path import FilePath


class FileSystemAdapter(StoragePort):
    """
    File system implementation of the StoragePort interface.
    
    This adapter handles all file system operations including reading/writing
    images, ROI files, and general file management.
    """
    
    def __init__(self, base_path: Optional[FilePath] = None):
        """
        Initialize the file system adapter.
        
        Args:
            base_path: Optional base path for relative operations
        """
        self.base_path = base_path
    
    def create_directory(self, path: FilePath) -> None:
        """Create a directory."""
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise StorageError(f"Failed to create directory {path}: {e}")
    
    def directory_exists(self, path: FilePath) -> bool:
        """Check if directory exists."""
        return path.is_directory()
    
    def file_exists(self, path: FilePath) -> bool:
        """Check if file exists."""
        return path.is_file()
    
    def list_files(self, directory: FilePath, pattern: Optional[str] = None, 
                  recursive: bool = False) -> List[FilePath]:
        """List files in a directory."""
        try:
            if not directory.exists():
                return []
            
            if pattern is None:
                pattern = "*"
            
            if recursive:
                glob_pattern = f"**/{pattern}"
                files = list(directory.path.glob(glob_pattern))
            else:
                files = list(directory.path.glob(pattern))
            
            # Filter to only include files (not directories)
            file_paths = [FilePath(f) for f in files if f.is_file()]
            return sorted(file_paths)
            
        except OSError as e:
            raise StorageError(f"Failed to list files in {directory}: {e}")
    
    def list_directories(self, directory: FilePath, recursive: bool = False) -> List[FilePath]:
        """List subdirectories in a directory."""
        try:
            if not directory.exists():
                return []
            
            if recursive:
                dirs = [FilePath(p) for p in directory.path.rglob("*") if p.is_dir()]
            else:
                dirs = [FilePath(p) for p in directory.path.iterdir() if p.is_dir()]
            
            return sorted(dirs)
            
        except OSError as e:
            raise StorageError(f"Failed to list directories in {directory}: {e}")
    
    def read_image(self, path: FilePath) -> np.ndarray:
        """Read image data from file."""
        try:
            if not path.exists():
                raise StorageError(f"Image file not found: {path}")
            
            # Use PIL for most image formats
            if path.get_suffix().lower() in ['.tif', '.tiff']:
                # For TIFF files, we might want to use a specialized library
                # For now, use PIL but this could be extended
                with PILImage.open(str(path)) as img:
                    return np.array(img)
            else:
                with PILImage.open(str(path)) as img:
                    return np.array(img)
                    
        except Exception as e:
            raise StorageError(f"Failed to read image {path}: {e}")
    
    def write_image(self, data: np.ndarray, path: FilePath, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Write image data to file."""
        try:
            # Ensure output directory exists
            path.get_parent().mkdir(parents=True, exist_ok=True)
            
            # Convert numpy array to PIL Image and save
            if data.dtype == np.float64 or data.dtype == np.float32:
                # Convert float to uint8 for saving
                data = (data * 255).astype(np.uint8)
            
            img = PILImage.fromarray(data)
            img.save(str(path))
            
        except Exception as e:
            raise StorageError(f"Failed to write image {path}: {e}")
    
    def read_roi_file(self, path: FilePath) -> List[ROI]:
        """Read ROI data from file."""
        try:
            if not path.exists():
                raise StorageError(f"ROI file not found: {path}")
            
            rois = []
            
            # For now, implement a basic ZIP file reader
            # In a full implementation, this would use ImageJ's ROI format
            if path.get_suffix().lower() == '.zip':
                with zipfile.ZipFile(str(path), 'r') as zip_file:
                    for file_info in zip_file.filelist:
                        if file_info.filename.endswith('.roi'):
                            # This is a placeholder - would need actual ROI parsing
                            roi = ROI(
                                roi_id=file_info.filename,
                                name=file_info.filename.replace('.roi', '')
                            )
                            rois.append(roi)
            
            return rois
            
        except Exception as e:
            raise StorageError(f"Failed to read ROI file {path}: {e}")
    
    def write_roi_file(self, rois: List[ROI], path: FilePath) -> None:
        """Write ROI data to file."""
        try:
            # Ensure output directory exists
            path.get_parent().mkdir(parents=True, exist_ok=True)
            
            # For now, create a simple ZIP file with ROI metadata
            # In a full implementation, this would write actual ImageJ ROI format
            with zipfile.ZipFile(str(path), 'w') as zip_file:
                for roi in rois:
                    roi_data = {
                        'roi_id': roi.roi_id,
                        'name': roi.name,
                        'coordinates': roi.coordinates,
                        'area': roi.area,
                        'measurements': roi.measurements
                    }
                    roi_json = json.dumps(roi_data, indent=2)
                    zip_file.writestr(f"{roi.roi_id}.json", roi_json)
                    
        except Exception as e:
            raise StorageError(f"Failed to write ROI file {path}: {e}")
    
    def copy_file(self, source: FilePath, destination: FilePath) -> None:
        """Copy a file."""
        try:
            destination.get_parent().mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(destination))
        except Exception as e:
            raise StorageError(f"Failed to copy {source} to {destination}: {e}")
    
    def move_file(self, source: FilePath, destination: FilePath) -> None:
        """Move a file."""
        try:
            destination.get_parent().mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
        except Exception as e:
            raise StorageError(f"Failed to move {source} to {destination}: {e}")
    
    def delete_file(self, path: FilePath) -> None:
        """Delete a file."""
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            raise StorageError(f"Failed to delete file {path}: {e}")
    
    def delete_directory(self, path: FilePath, recursive: bool = False) -> None:
        """Delete a directory."""
        try:
            if path.exists():
                if recursive:
                    shutil.rmtree(str(path))
                else:
                    path.path.rmdir()
        except Exception as e:
            raise StorageError(f"Failed to delete directory {path}: {e}")
    
    def get_file_size(self, path: FilePath) -> int:
        """Get file size in bytes."""
        try:
            return path.path.stat().st_size
        except Exception as e:
            raise StorageError(f"Failed to get file size for {path}: {e}")
    
    def get_modification_time(self, path: FilePath) -> float:
        """Get file modification time."""
        try:
            return path.path.stat().st_mtime
        except Exception as e:
            raise StorageError(f"Failed to get modification time for {path}: {e}")
    
    def read_text_file(self, path: FilePath) -> str:
        """Read text file content."""
        try:
            with open(str(path), 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise StorageError(f"Failed to read text file {path}: {e}")
    
    def write_text_file(self, content: str, path: FilePath) -> None:
        """Write text content to file."""
        try:
            path.get_parent().mkdir(parents=True, exist_ok=True)
            with open(str(path), 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise StorageError(f"Failed to write text file {path}: {e}")
    
    def read_json_file(self, path: FilePath) -> Dict[str, Any]:
        """Read JSON file content."""
        try:
            with open(str(path), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise StorageError(f"Failed to read JSON file {path}: {e}")
    
    def write_json_file(self, data: Dict[str, Any], path: FilePath) -> None:
        """Write data to JSON file."""
        try:
            path.get_parent().mkdir(parents=True, exist_ok=True)
            with open(str(path), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise StorageError(f"Failed to write JSON file {path}: {e}")
    
    def cleanup_temp_files(self, directory: FilePath, 
                          older_than_hours: Optional[float] = None) -> int:
        """Clean up temporary files."""
        try:
            if not directory.exists():
                return 0
            
            current_time = time.time()
            deleted_count = 0
            
            # Look for common temp file patterns
            temp_patterns = ['*.tmp', '*.temp', '*~', '.DS_Store']
            
            for pattern in temp_patterns:
                temp_files = directory.path.glob(pattern)
                for temp_file in temp_files:
                    try:
                        if older_than_hours is not None:
                            file_age_hours = (current_time - temp_file.stat().st_mtime) / 3600
                            if file_age_hours < older_than_hours:
                                continue
                        
                        temp_file.unlink()
                        deleted_count += 1
                    except Exception:
                        continue  # Skip files we can't delete
            
            return deleted_count
            
        except Exception as e:
            raise StorageError(f"Failed to cleanup temp files in {directory}: {e}")
    
    def get_disk_usage(self, path: FilePath) -> Dict[str, int]:
        """Get disk usage information."""
        try:
            statvfs = os.statvfs(str(path))
            total = statvfs.f_frsize * statvfs.f_blocks
            free = statvfs.f_frsize * statvfs.f_available
            used = total - free
            
            return {
                'total': total,
                'used': used,
                'free': free
            }
        except Exception as e:
            raise StorageError(f"Failed to get disk usage for {path}: {e}")
    
    def create_backup(self, source: FilePath, backup_dir: FilePath) -> FilePath:
        """Create a backup of a file or directory."""
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source.get_stem()}_{timestamp}{source.get_suffix()}"
            backup_path = backup_dir.join(backup_name)
            
            if source.is_file():
                self.copy_file(source, backup_path)
            elif source.is_directory():
                shutil.copytree(str(source), str(backup_path))
            else:
                raise StorageError(f"Source {source} is neither file nor directory")
            
            return backup_path
            
        except Exception as e:
            raise StorageError(f"Failed to create backup of {source}: {e}")
    
    def watch_directory(self, directory: FilePath) -> Iterator[FilePath]:
        """Watch directory for changes."""
        # This is a simplified implementation
        # A full implementation would use a proper file system watcher
        try:
            last_scan = {}
            
            while True:
                current_files = {}
                
                if directory.exists():
                    for file_path in self.list_files(directory, recursive=True):
                        try:
                            mtime = self.get_modification_time(file_path)
                            current_files[str(file_path)] = mtime
                        except:
                            continue
                
                # Check for new or modified files
                for file_path_str, mtime in current_files.items():
                    if (file_path_str not in last_scan or 
                        last_scan[file_path_str] < mtime):
                        yield FilePath.from_string(file_path_str)
                
                last_scan = current_files.copy()
                time.sleep(1)  # Poll every second
                
        except Exception as e:
            raise StorageError(f"Failed to watch directory {directory}: {e}")
