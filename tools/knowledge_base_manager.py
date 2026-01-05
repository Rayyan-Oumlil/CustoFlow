"""Knowledge Base Manager for FAQ System"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import threading


class KBVersionStatus(Enum):
    """Knowledge base version status."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    TESTING = "testing"


class KnowledgeBaseManager:
    """
    Manages FAQ knowledge base versions and A/B testing.
    
    Supports:
    - Multiple versions of FAQ data
    - A/B testing different configurations
    - Version history and rollback
    - Metadata tracking
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize knowledge base manager.
        
        Args:
            data_dir: Directory for storing version data
        """
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.versions_dir = self.data_dir / "kb_versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.Lock()
        self._versions_metadata: Dict[str, Dict] = {}
        self._load_versions_metadata()
    
    def _load_versions_metadata(self) -> None:
        """Load versions metadata from disk."""
        metadata_file = self.versions_dir / "versions_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self._versions_metadata = json.load(f)
            except Exception:
                self._versions_metadata = {}
        else:
            self._versions_metadata = {}
    
    def _save_versions_metadata(self) -> None:
        """Save versions metadata to disk."""
        metadata_file = self.versions_dir / "versions_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self._versions_metadata, f, indent=2, ensure_ascii=False)
    
    def create_version(
        self,
        faqs: List[Dict],
        version_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Create a new version of the knowledge base.
        
        Args:
            faqs: List of FAQ dictionaries
            version_name: Optional version name (auto-generated if not provided)
            description: Optional version description
            tags: Optional list of tags
            
        Returns:
            Version ID
        """
        with self._lock:
            # Generate version ID
            if version_name:
                version_id = hashlib.md5(version_name.encode()).hexdigest()[:12]
            else:
                timestamp = datetime.now().isoformat()
                version_id = hashlib.md5(timestamp.encode()).hexdigest()[:12]
            
            # Create version data
            version_data = {
                "faqs": faqs,
                "version_id": version_id,
                "created_at": datetime.now().isoformat(),
                "version_name": version_name or f"version_{version_id}",
                "description": description,
                "tags": tags or [],
                "status": KBVersionStatus.DRAFT.value,
                "num_faqs": len(faqs),
                "languages": self._detect_languages(faqs)
            }
            
            # Save version file
            version_file = self.versions_dir / f"{version_id}.json"
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
            
            # Update metadata
            self._versions_metadata[version_id] = {
                "version_id": version_id,
                "version_name": version_data["version_name"],
                "description": description,
                "tags": tags or [],
                "status": KBVersionStatus.DRAFT.value,
                "created_at": version_data["created_at"],
                "num_faqs": len(faqs),
                "languages": version_data["languages"]
            }
            
            self._save_versions_metadata()
            
            return version_id
    
    def get_version(self, version_id: str) -> Optional[Dict]:
        """
        Get a specific version of the knowledge base.
        
        Args:
            version_id: Version ID
            
        Returns:
            Version data dictionary or None if not found
        """
        version_file = self.versions_dir / f"{version_id}.json"
        if not version_file.exists():
            return None
        
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def list_versions(
        self,
        status: Optional[KBVersionStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        List all versions with optional filtering.
        
        Args:
            status: Filter by status
            tags: Filter by tags (any match)
            
        Returns:
            List of version metadata dictionaries
        """
        versions = list(self._versions_metadata.values())
        
        if status:
            versions = [v for v in versions if v.get("status") == status.value]
        
        if tags:
            versions = [
                v for v in versions
                if any(tag in v.get("tags", []) for tag in tags)
            ]
        
        # Sort by created_at descending
        versions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return versions
    
    def activate_version(self, version_id: str) -> bool:
        """
        Activate a version (deactivates others).
        
        Args:
            version_id: Version ID to activate
            
        Returns:
            True if successful, False if version not found
        """
        if version_id not in self._versions_metadata:
            return False
        
        with self._lock:
            # Deactivate all other versions
            for vid, metadata in self._versions_metadata.items():
                if metadata.get("status") == KBVersionStatus.ACTIVE.value:
                    metadata["status"] = KBVersionStatus.ARCHIVED.value
            
            # Activate this version
            self._versions_metadata[version_id]["status"] = KBVersionStatus.ACTIVE.value
            self._save_versions_metadata()
            
            return True
    
    def set_version_status(
        self,
        version_id: str,
        status: KBVersionStatus
    ) -> bool:
        """
        Set status for a version.
        
        Args:
            version_id: Version ID
            status: New status
            
        Returns:
            True if successful, False if version not found
        """
        if version_id not in self._versions_metadata:
            return False
        
        with self._lock:
            self._versions_metadata[version_id]["status"] = status.value
            self._save_versions_metadata()
            return True
    
    def get_active_version(self) -> Optional[Dict]:
        """
        Get the currently active version.
        
        Returns:
            Active version data or None
        """
        for version_id, metadata in self._versions_metadata.items():
            if metadata.get("status") == KBVersionStatus.ACTIVE.value:
                return self.get_version(version_id)
        
        return None
    
    def compare_versions(
        self,
        version_id1: str,
        version_id2: str
    ) -> Dict[str, Any]:
        """
        Compare two versions of the knowledge base.
        
        Args:
            version_id1: First version ID
            version_id2: Second version ID
            
        Returns:
            Comparison dictionary with differences
        """
        v1 = self.get_version(version_id1)
        v2 = self.get_version(version_id2)
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        faqs1 = {faq.get("question", ""): faq for faq in v1.get("faqs", [])}
        faqs2 = {faq.get("question", ""): faq for faq in v2.get("faqs", [])}
        
        questions1 = set(faqs1.keys())
        questions2 = set(faqs2.keys())
        
        return {
            "version1": {
                "id": version_id1,
                "name": v1.get("version_name"),
                "num_faqs": len(faqs1)
            },
            "version2": {
                "id": version_id2,
                "name": v2.get("version_name"),
                "num_faqs": len(faqs2)
            },
            "added": list(questions2 - questions1),
            "removed": list(questions1 - questions2),
            "common": list(questions1 & questions2),
            "total_differences": len(questions1 ^ questions2)
        }
    
    def _detect_languages(self, faqs: List[Dict]) -> List[str]:
        """
        Detect languages in FAQ data (simple detection).
        
        Args:
            faqs: List of FAQ dictionaries
            
        Returns:
            List of detected language codes
        """
        # Simple language detection based on common words
        # In production, use a proper language detection library
        languages = set()
        
        for faq in faqs:
            question = faq.get("question", "").lower()
            answer = faq.get("answer", "").lower()
            text = question + " " + answer
            
            # Simple heuristics (can be improved with langdetect library)
            if any(word in text for word in ["the", "is", "are", "what", "how"]):
                languages.add("en")
            if any(word in text for word in ["le", "la", "les", "est", "sont"]):
                languages.add("fr")
            if any(word in text for word in ["el", "la", "los", "es", "son"]):
                languages.add("es")
            if any(word in text for word in ["der", "die", "das", "ist", "sind"]):
                languages.add("de")
        
        return sorted(list(languages)) if languages else ["en"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about all versions.
        
        Returns:
            Statistics dictionary
        """
        versions = list(self._versions_metadata.values())
        
        status_counts = {}
        for version in versions:
            status = version.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_faqs = sum(v.get("num_faqs", 0) for v in versions)
        all_languages = set()
        for version in versions:
            all_languages.update(version.get("languages", []))
        
        return {
            "total_versions": len(versions),
            "status_counts": status_counts,
            "total_faqs": total_faqs,
            "languages": sorted(list(all_languages)),
            "active_version": next(
                (v["version_id"] for v in versions if v.get("status") == KBVersionStatus.ACTIVE.value),
                None
            )
        }


# Global knowledge base manager instance
_kb_manager: Optional[KnowledgeBaseManager] = None
_kb_manager_lock = threading.Lock()


def get_kb_manager() -> KnowledgeBaseManager:
    """
    Get or create global knowledge base manager instance.
    
    Returns:
        KnowledgeBaseManager instance
    """
    global _kb_manager
    
    if _kb_manager is None:
        with _kb_manager_lock:
            if _kb_manager is None:
                _kb_manager = KnowledgeBaseManager()
    
    return _kb_manager

