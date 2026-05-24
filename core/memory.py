"""
REX Memory System - Episodic, Semantic, and Procedural Memory
"""
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
from collections import deque

import numpy as np
from loguru import logger

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

try:
    import networkx as nx
except ImportError:
    nx = None

from config.settings import MEMORY_CONFIG, DATA_DIR


class REXMemory:
    """
    Advanced Memory System with:
    - Episodic Memory (past interactions)
    - Semantic Memory (facts and knowledge)
    - Procedural Memory (learned procedures)
    - Knowledge Graph
    - Vector Database
    """
    
    def __init__(self):
        self.episodic_memory = deque(maxlen=MEMORY_CONFIG["max_episodic_memory"])
        self.semantic_memory = {}
        self.procedural_memory = {}
        self.knowledge_graph = None
        self.vector_client = None
        self.vector_collection = None
        
        # Initialize storage
        self._init_vector_db()
        self._init_knowledge_graph()
        self._load_persistent_memory()
        
        logger.info("🧠 Memory system initialized")
    
    def _init_vector_db(self):
        """Initialize vector database for semantic search"""
        if chromadb is None:
            logger.warning("ChromaDB not available, using fallback memory")
            self._fallback_vectors = {}
            return
        
        try:
            self.vector_client = chromadb.PersistentClient(
                path=MEMORY_CONFIG["vector_db_path"]
            )
            self.vector_collection = self.vector_client.get_or_create_collection(
                name="rex_memories",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("✅ Vector database initialized")
        except Exception as e:
            logger.error(f"Vector DB init error: {e}")
            self._fallback_vectors = {}
    
    def _init_knowledge_graph(self):
        """Initialize knowledge graph"""
        if nx is None:
            logger.warning("NetworkX not available, knowledge graph disabled")
            return
        
        kg_path = Path(MEMORY_CONFIG["knowledge_graph_path"])
        if kg_path.exists():
            try:
                with open(kg_path, 'r') as f:
                    data = json.load(f)
                self.knowledge_graph = nx.node_link_graph(data)
                logger.info(f"✅ Knowledge graph loaded: {self.knowledge_graph.number_of_nodes()} nodes")
            except Exception as e:
                logger.error(f"KG load error: {e}")
                self.knowledge_graph = nx.DiGraph()
        else:
            self.knowledge_graph = nx.DiGraph()
            self._init_base_knowledge()
    
    def _init_base_knowledge(self):
        """Initialize base knowledge graph with fundamental concepts"""
        if self.knowledge_graph is None:
            return
        
        # Add base concepts
        concepts = {
            "rex": {"type": "ai_assistant", "name": "REX"},
            "user": {"type": "human", "role": "primary_user"},
            "conversation": {"type": "interaction", "category": "communication"},
            "task": {"type": "action", "category": "work"},
            "learning": {"type": "process", "category": "improvement"},
        }
        
        for node, attrs in concepts.items():
            self.knowledge_graph.add_node(node, **attrs)
        
        # Add relationships
        relationships = [
            ("rex", "user", "assists"),
            ("rex", "conversation", "participates_in"),
            ("rex", "task", "executes"),
            ("rex", "learning", "performs"),
        ]
        
        for source, target, relation in relationships:
            self.knowledge_graph.add_edge(source, target, relation=relation)
    
    def _load_persistent_memory(self):
        """Load persistent memory from disk"""
        memory_file = DATA_DIR / "persistent_memory.json"
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                self.semantic_memory = data.get("semantic", {})
                self.procedural_memory = data.get("procedural", {})
                logger.info(f"✅ Loaded persistent memory: {len(self.semantic_memory)} semantic entries")
            except Exception as e:
                logger.error(f"Memory load error: {e}")
    
    def _save_persistent_memory(self):
        """Save persistent memory to disk"""
        memory_file = DATA_DIR / "persistent_memory.json"
        try:
            data = {
                "semantic": self.semantic_memory,
                "procedural": self.procedural_memory,
                "saved_at": datetime.now().isoformat(),
            }
            with open(memory_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Memory save error: {e}")
    
    async def store_interaction(self, user_input: str, response: Dict,
                                intent: str, entities: List, sentiment: str,
                                processing_time: float):
        """Store an interaction in episodic memory"""
        memory_entry = {
            "id": hashlib.md5(f"{user_input}{time.time()}".encode()).hexdigest()[:12],
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response.get("text", ""),
            "intent": intent,
            "entities": entities,
            "sentiment": sentiment,
            "processing_time": processing_time,
        }
        
        self.episodic_memory.append(memory_entry)
        
        # Store in vector DB
        if self.vector_collection:
            try:
                self.vector_collection.add(
                    ids=[memory_entry["id"]],
                    documents=[f"{user_input} {response.get('text', '')}"],
                    metadatas=[{
                        "intent": intent,
                        "sentiment": sentiment,
                        "timestamp": memory_entry["timestamp"],
                    }]
                )
            except Exception as e:
                logger.error(f"Vector store error: {e}")
        
        # Update knowledge graph
        self._update_knowledge_graph(user_input, entities, intent)
        
        # Extract and store semantic facts
        self._extract_facts(user_input, response, entities)
    
    def _update_knowledge_graph(self, text: str, entities: List, intent: str):
        """Update knowledge graph with new information"""
        if self.knowledge_graph is None:
            return
        
        for entity in entities:
            entity_text = entity.get("text", "")
            entity_type = entity.get("type", "unknown")
            
            if entity_text:
                if not self.knowledge_graph.has_node(entity_text):
                    self.knowledge_graph.add_node(
                        entity_text, type=entity_type, first_seen=datetime.now().isoformat()
                    )
                self.knowledge_graph.add_edge(
                    "rex", entity_text, relation=f"knows_{entity_type}",
                    weight=1.0, last_interaction=datetime.now().isoformat()
                )
    
    def _extract_facts(self, user_input: str, response: Dict, entities: List):
        """Extract facts from interaction and store in semantic memory"""
        # Simple fact extraction based on patterns
        patterns = {
            "name_is": r"(?:my name is|i am|i'm) (\w+)",
            "likes": r"(?:i like|i love|i enjoy) (.+)",
            "location": r"(?:i live in|i'm from|i'm in) (.+)",
            "preference": r"(?:i prefer|i want) (.+)",
        }
        
        import re
        for fact_type, pattern in patterns.items():
            match = re.search(pattern, user_input.lower())
            if match:
                fact_key = f"{fact_type}_{hashlib.md5(match.group(1).encode()).hexdigest()[:8]}"
                self.semantic_memory[fact_key] = {
                    "type": fact_type,
                    "value": match.group(1),
                    "confidence": 0.9,
                    "timestamp": datetime.now().isoformat(),
                    "source": "user_statement",
                }
    
    async def retrieve_relevant(self, query: str, intent: str, entities: List) -> List[Dict]:
        """Retrieve relevant memories for the current query"""
        results = []
        
        # Vector similarity search
        if self.vector_collection:
            try:
                vector_results = self.vector_collection.query(
                    query_texts=[query],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
                
                if vector_results and vector_results["documents"]:
                    for i, doc in enumerate(vector_results["documents"][0]):
                        results.append({
                            "text": doc,
                            "metadata": vector_results["metadatas"][0][i] if vector_results["metadatas"] else {},
                            "relevance": 1 - (vector_results["distances"][0][i] if vector_results["distances"] else 0),
                            "source": "vector_db",
                        })
            except Exception as e:
                logger.error(f"Vector query error: {e}")
        
        # Episodic memory search (recent interactions)
        for memory in list(self.episodic_memory)[-20:]:
            if any(word in memory.get("user_input", "").lower() 
                   for word in query.lower().split() if len(word) > 3):
                results.append({
                    "text": memory["user_input"],
                    "response": memory["response"],
                    "timestamp": memory["timestamp"],
                    "relevance": 0.7,
                    "source": "episodic",
                })
        
        # Semantic memory search
        for key, fact in self.semantic_memory.items():
            if any(word in str(fact.get("value", "")).lower() 
                   for word in query.lower().split() if len(word) > 3):
                results.append({
                    "text": str(fact["value"]),
                    "type": fact["type"],
                    "confidence": fact["confidence"],
                    "relevance": 0.8,
                    "source": "semantic",
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return results[:10]
    
    async def consolidate(self):
        """Consolidate memories - merge, prune, strengthen"""
        # Save persistent memory
        self._save_persistent_memory()
        
        # Save knowledge graph
        if self.knowledge_graph and nx:
            kg_path = Path(MEMORY_CONFIG["knowledge_graph_path"])
            try:
                data = nx.node_link_data(self.knowledge_graph)
                with open(kg_path, 'w') as f:
                    json.dump(data, f, default=str)
            except Exception as e:
                logger.error(f"KG save error: {e}")
        
        # Prune low-relevance semantic memories
        current_time = datetime.now()
        keys_to_remove = []
        for key, fact in self.semantic_memory.items():
            if fact.get("confidence", 1.0) < 0.3:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.semantic_memory[key]
        
        if keys_to_remove:
            logger.info(f"Pruned {len(keys_to_remove)} low-confidence memories")
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "episodic_count": len(self.episodic_memory),
            "semantic_count": len(self.semantic_memory),
            "procedural_count": len(self.procedural_memory),
            "knowledge_graph_nodes": self.knowledge_graph.number_of_nodes() if self.knowledge_graph else 0,
            "knowledge_graph_edges": self.knowledge_graph.number_of_edges() if self.knowledge_graph else 0,
            "vector_db_count": self.vector_collection.count() if self.vector_collection else 0,
        }
    
    def add_knowledge(self, subject: str, predicate: str, obj: str, confidence: float = 1.0):
        """Add a knowledge triple to the graph"""
        if self.knowledge_graph is None:
            return
        
        self.knowledge_graph.add_node(subject, type="entity")
        self.knowledge_graph.add_node(obj, type="entity")
        self.knowledge_graph.add_edge(subject, obj, relation=predicate, 
                                       confidence=confidence,
                                       timestamp=datetime.now().isoformat())
    
    def query_knowledge(self, subject: str = None, predicate: str = None, 
                        obj: str = None) -> List[Dict]:
        """Query the knowledge graph"""
        if self.knowledge_graph is None:
            return []
        
        results = []
        for u, v, data in self.knowledge_graph.edges(data=True):
            match = True
            if subject and u != subject:
                match = False
            if predicate and data.get("relation") != predicate:
                match = False
            if obj and v != obj:
                match = False
            if match:
                results.append({"subject": u, "predicate": data.get("relation"), 
                              "object": v, **data})
        return results
