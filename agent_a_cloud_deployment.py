"""
Author Agent with Memory - Vertex AI Agent Engine Deployment
=============================================================
Production-ready Author Agent with persistent memory, caching, and session management.

Features:
- Firestore for session state and iteration history
- Redis caching for Source Manifests and Hypotheses
- Cloud Storage for artifacts (manifests, documents, DS-STAR results)
- Smart deduplication to minimize redundant LLM calls
- Session-based memory across multi-turn conversations

Deployment: vertex-ai-agent-engine deploy
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Google Cloud imports
try:
    from google.cloud import firestore
    from google.cloud import storage
    import redis
    CLOUD_AVAILABLE = True
except ImportError:
    print("Warning: Google Cloud libraries not installed. Running in mock mode.")
    CLOUD_AVAILABLE = False

# LLM imports (replace with actual provider)
try:
    from vertexai.preview import generative_models
    LLM_AVAILABLE = True
except ImportError:
    print("Warning: Vertex AI not available. Using mock LLM.")
    LLM_AVAILABLE = False


# --- Configuration ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
FIRESTORE_COLLECTION = "research_sessions"
GCS_BUCKET = os.getenv("GCS_BUCKET", "agent-a-outputs")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Cache TTLs
SOURCE_MANIFEST_TTL = 7 * 24 * 3600  # 7 days
HYPOTHESES_TTL = 7 * 24 * 3600  # 7 days
DS_STAR_RESULTS_TTL = 30 * 24 * 3600  # 30 days


# --- Cloud Storage Manager ---
class CloudStorageManager:
    """Manages artifact storage in Google Cloud Storage."""
    
    def __init__(self, bucket_name: str):
        if CLOUD_AVAILABLE:
            self.storage_client = storage.Client(project=PROJECT_ID)
            self.bucket = self.storage_client.bucket(bucket_name)
        else:
            self.storage_client = None
            self.bucket = None
            print("Warning: Using local file storage (Cloud Storage not available)")
    
    def save_artifact(self, session_id: str, artifact_name: str, content: str) -> str:
        """
        Saves an artifact to Cloud Storage.
        
        Args:
            session_id: Unique session identifier
            artifact_name: Name of the artifact (e.g., "source_manifest.json")
            content: Artifact content as string
            
        Returns:
            GCS URI or local path
        """
        blob_path = f"{session_id}/{artifact_name}"
        
        if self.bucket:
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(content)
            uri = f"gs://{self.bucket.name}/{blob_path}"
            print(f"  ✓ Artifact saved to Cloud Storage: {uri}")
            return uri
        else:
            # Fallback to local storage
            local_path = Path(f"./local_storage/{blob_path}")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Artifact saved locally: {local_path}")
            return str(local_path)
    
    def load_artifact(self, session_id: str, artifact_name: str) -> Optional[str]:
        """Loads an artifact from Cloud Storage."""
        blob_path = f"{session_id}/{artifact_name}"
        
        if self.bucket:
            blob = self.bucket.blob(blob_path)
            if blob.exists():
                return blob.download_as_text()
        else:
            local_path = Path(f"./local_storage/{blob_path}")
            if local_path.exists():
                return local_path.read_text(encoding='utf-8')
        
        return None


# --- Cache Manager (Redis) ---
class CacheManager:
    """Manages caching layer using Redis/Memorystore."""
    
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT):
        if CLOUD_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=host, 
                    port=port, 
                    decode_responses=True
                )
                self.redis_client.ping()
                print(f"✓ Connected to Redis at {host}:{port}")
            except Exception as e:
                print(f"Warning: Redis connection failed ({e}). Using in-memory cache.")
                self.redis_client = None
                self.memory_cache = {}
        else:
            self.redis_client = None
            self.memory_cache = {}
    
    def _generate_cache_key(self, prefix: str, content: str) -> str:
        """Generates a deterministic cache key using SHA256 hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{prefix}:{content_hash}"
    
    def get(self, key: str) -> Optional[str]:
        """Gets a value from cache."""
        if self.redis_client:
            return self.redis_client.get(key)
        else:
            return self.memory_cache.get(key)
    
    def set(self, key: str, value: str, ttl: int):
        """Sets a value in cache with TTL."""
        if self.redis_client:
            self.redis_client.setex(key, ttl, value)
        else:
            self.memory_cache[key] = value
    
    def get_source_manifest(self, research_topic: str) -> Optional[List[Dict]]:
        """Gets cached source manifest for a research topic."""
        cache_key = self._generate_cache_key("source_manifest", research_topic)
        cached = self.get(cache_key)
        
        if cached:
            print(f"  ✓ Cache HIT: Source Manifest for topic hash {cache_key[-8:]}")
            return json.loads(cached)
        
        print(f"  ✗ Cache MISS: Source Manifest")
        return None
    
    def set_source_manifest(self, research_topic: str, manifest: List[Dict]):
        """Caches source manifest for a research topic."""
        cache_key = self._generate_cache_key("source_manifest", research_topic)
        self.set(cache_key, json.dumps(manifest), SOURCE_MANIFEST_TTL)
        print(f"  ✓ Cached Source Manifest (TTL: {SOURCE_MANIFEST_TTL // 86400} days)")
    
    def get_hypotheses(self, research_topic: str, sources_hash: str) -> Optional[List[str]]:
        """Gets cached hypotheses."""
        cache_key = self._generate_cache_key("hypotheses", f"{research_topic}:{sources_hash}")
        cached = self.get(cache_key)
        
        if cached:
            print(f"  ✓ Cache HIT: Hypotheses")
            return json.loads(cached)
        
        print(f"  ✗ Cache MISS: Hypotheses")
        return None
    
    def set_hypotheses(self, research_topic: str, sources_hash: str, hypotheses: List[str]):
        """Caches hypotheses."""
        cache_key = self._generate_cache_key("hypotheses", f"{research_topic}:{sources_hash}")
        self.set(cache_key, json.dumps(hypotheses), HYPOTHESES_TTL)
        print(f"  ✓ Cached Hypotheses (TTL: {HYPOTHESES_TTL // 86400} days)")


# --- Session Manager (Firestore) ---
class SessionManager:
    """Manages session state and iteration history using Firestore."""
    
    def __init__(self, collection_name: str = FIRESTORE_COLLECTION):
        if CLOUD_AVAILABLE:
            self.db = firestore.Client(project=PROJECT_ID)
            self.collection = self.db.collection(collection_name)
            print(f"✓ Connected to Firestore collection: {collection_name}")
        else:
            self.db = None
            self.collection = None
            self.local_sessions = {}
            print("Warning: Using in-memory session storage")
    
    def create_session(self, research_topic: str) -> str:
        """Creates a new session and returns session ID."""
        session_id = hashlib.sha256(
            f"{research_topic}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        session_data = {
            "session_id": session_id,
            "research_topic": research_topic,
            "created_at": datetime.now(),
            "iterations": [],
            "status": "active"
        }
        
        if self.collection:
            self.collection.document(session_id).set(session_data)
        else:
            self.local_sessions[session_id] = session_data
        
        print(f"✓ Session created: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieves session data."""
        if self.collection:
            doc = self.collection.document(session_id).get()
            return doc.to_dict() if doc.exists else None
        else:
            return self.local_sessions.get(session_id)
    
    def add_iteration(
        self, 
        session_id: str, 
        iteration_num: int,
        kill_list: str,
        document: str,
        audit_result: Optional[str] = None
    ):
        """Adds an iteration to the session history."""
        iteration_data = {
            "iteration": iteration_num,
            "timestamp": datetime.now(),
            "kill_list": kill_list,
            "document_length": len(document),
            "audit_result": audit_result
        }
        
        if self.collection:
            self.collection.document(session_id).update({
                "iterations": firestore.ArrayUnion([iteration_data]),
                "last_updated": datetime.now()
            })
        else:
            session = self.local_sessions.get(session_id)
            if session:
                session["iterations"].append(iteration_data)
    
    def get_previous_kill_list(self, session_id: str) -> str:
        """Gets the most recent kill list from session history."""
        session = self.get_session(session_id)
        if session and session.get("iterations"):
            last_iteration = session["iterations"][-1]
            return last_iteration.get("kill_list", "")
        return ""


# --- Author Agent with Memory ---
class AuthorAgentWithMemory:
    """
    Production Author Agent with persistent memory and caching.
    
    Key Features:
    - Caches Source Manifests by research topic (7-day TTL)
    - Caches Hypotheses by topic+sources (7-day TTL)
    - Session-based state management
    - Artifact persistence in Cloud Storage
    - Smart deduplication to minimize LLM costs
    """
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        research_topic: Optional[str] = None
    ):
        # Initialize cloud services
        self.storage = CloudStorageManager(GCS_BUCKET)
        self.cache = CacheManager()
        self.sessions = SessionManager()
        
        # Initialize or resume session
        if session_id:
            self.session_id = session_id
            session_data = self.sessions.get_session(session_id)
            self.research_topic = session_data.get("research_topic", research_topic)
        else:
            if not research_topic:
                raise ValueError("Either session_id or research_topic must be provided")
            self.research_topic = research_topic
            self.session_id = self.sessions.create_session(research_topic)
        
        # State
        self.source_manifest = []
        self.hypotheses = []
        self.iteration_count = 0
        
        print(f"\n{'='*70}")
        print("AUTHOR AGENT WITH MEMORY - Initialized")
        print(f"{'='*70}")
        print(f"  Session ID: {self.session_id}")
        print(f"  Research Topic: {self.research_topic}")
        print(f"{'='*70}\n")
    
    def phase_1_research_with_cache(self, previous_kill_list: str = "") -> List[Dict]:
        """
        Phase 1: Research with intelligent caching.
        
        Cache Strategy:
        - Check cache first for existing Source Manifest
        - Only call LLM if cache miss
        - Save to cache on generation
        """
        print(f"\n{'='*70}")
        print("PHASE 1: RESEARCH (with caching)")
        print(f"{'='*70}")
        
        # Check cache first
        cached_manifest = self.cache.get_source_manifest(self.research_topic)
        
        if cached_manifest and not previous_kill_list:
            # Cache hit and no feedback to incorporate
            self.source_manifest = cached_manifest
            print(f"✓ Using cached Source Manifest ({len(cached_manifest)} sources)")
            return cached_manifest
        
        # Cache miss or feedback present - generate new manifest
        print("Generating new Source Manifest (cache miss or feedback present)...")
        
        # Mock LLM call (replace with actual Vertex AI call)
        self.source_manifest = [
            {
                "source_id": "S1",
                "title": "Mobile App Retention Strategies 2024",
                "authors": ["Smith, J.", "Johnson, A."],
                "year": 2024,
                "type": "academic_paper",
                "key_findings": "Personalization increases retention by 34%",
                "relevance_score": 9,
                "citation": "Smith, J., & Johnson, A. (2024)..."
            }
        ]
        
        # Cache the result (only if no kill list feedback)
        if not previous_kill_list:
            self.cache.set_source_manifest(self.research_topic, self.source_manifest)
        
        # Save to Cloud Storage
        self.storage.save_artifact(
            self.session_id,
            "source_manifest.json",
            json.dumps(self.source_manifest, indent=2)
        )
        
        return self.source_manifest
    
    def phase_2_hypotheses_with_cache(self, source_manifest: List[Dict]) -> List[str]:
        """
        Phase 2: Hypothesis Generation with caching.
        
        Cache Strategy:
        - Hash the source manifest
        - Check cache for hypotheses with same sources
        - Generate only if cache miss
        """
        print(f"\n{'='*70}")
        print("PHASE 2: HYPOTHESIS GENERATION (with caching)")
        print(f"{'='*70}")
        
        # Generate hash of source manifest for cache key
        sources_hash = hashlib.sha256(
            json.dumps(source_manifest, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        # Check cache
        cached_hypotheses = self.cache.get_hypotheses(self.research_topic, sources_hash)
        
        if cached_hypotheses:
            self.hypotheses = cached_hypotheses
            print(f"✓ Using cached Hypotheses ({len(cached_hypotheses)} hypotheses)")
            return cached_hypotheses
        
        # Cache miss - generate new hypotheses
        print("Generating new Hypotheses (cache miss)...")
        
        # Mock LLM call (replace with actual Vertex AI call)
        self.hypotheses = [
            "User engagement increases with personalized content recommendations",
            "Churn rate is negatively correlated with feature adoption rate",
            "Premium users have 2x higher retention than free users"
        ]
        
        # Cache the result
        self.cache.set_hypotheses(self.research_topic, sources_hash, self.hypotheses)
        
        # Save to Cloud Storage
        self.storage.save_artifact(
            self.session_id,
            "hypotheses.json",
            json.dumps(self.hypotheses, indent=2)
        )
        
        return self.hypotheses
    
    def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Router Agent interface with memory and caching.
        
        Args:
            prompt: System prompt from Meta-Reviewer
            context: Context including PREVIOUS_KILL_LIST
            
        Returns:
            Generated document
        """
        print(f"\n{'='*70}")
        print("AUTHOR AGENT - Invoke (with Memory)")
        print(f"{'='*70}")
        
        # Extract previous kill list
        previous_kill_list = ""
        if context and "PREVIOUS_KILL_LIST" in context:
            previous_kill_list = context["PREVIOUS_KILL_LIST"]
        
        # Increment iteration
        self.iteration_count += 1
        
        # Phase 1: Research (with cache)
        source_manifest = self.phase_1_research_with_cache(previous_kill_list)
        
        # Phase 2: Hypotheses (with cache)
        hypotheses = self.phase_2_hypotheses_with_cache(source_manifest)
        
        # Phase 3: DS-STAR (would check cache here too)
        print(f"\nPhase 3: DS-STAR execution (skipped in this example)")
        
        # Phase 4: Drafting
        print(f"\nPhase 4: Drafting final document...")
        document = f"# Research Document\n\n{len(source_manifest)} sources, {len(hypotheses)} hypotheses"
        
        # Save iteration to session
        self.sessions.add_iteration(
            self.session_id,
            self.iteration_count,
            previous_kill_list,
            document
        )
        
        # Save final document
        self.storage.save_artifact(
            self.session_id,
            f"document_iteration_{self.iteration_count}.md",
            document
        )
        
        print(f"\n✓ Document generated (iteration {self.iteration_count})")
        return document


# --- Example Usage ---
def main():
    """Demonstrates the Author Agent with memory and caching."""
    
    print("\n" + "="*70)
    print("AUTHOR AGENT WITH MEMORY - DEMONSTRATION")
    print("="*70)
    
    # Create new session
    agent = AuthorAgentWithMemory(
        research_topic="Mobile App Retention Using AI Personalization"
    )
    
    # First invocation (cache miss)
    print("\n=== ITERATION 1 (Cache Miss) ===")
    doc1 = agent.invoke(
        prompt="Generate comprehensive research document",
        context={"PREVIOUS_KILL_LIST": ""}
    )
    
    # Second invocation (cache hit for phases 1-2)
    print("\n=== ITERATION 2 (Cache Hit) ===")
    doc2 = agent.invoke(
        prompt="Refine based on feedback",
        context={"PREVIOUS_KILL_LIST": "Fix citation formatting"}
    )
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print(f"Session ID: {agent.session_id}")
    print(f"Total iterations: {agent.iteration_count}")
    print("="*70)


if __name__ == '__main__':
    main()
