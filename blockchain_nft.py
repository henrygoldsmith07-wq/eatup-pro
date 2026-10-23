"""
EatUp Pro - Blockchain & NFT Achievement System v6.0

Revolutionary web3 integration with immutable audit trails, 
blockchain-backed achievements, and decentralized storage optimization.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from collections import deque
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Types of blockchain transactions"""
    CLEANUP_OPERATION = "cleanup_operation"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    SPACE_REDEEMED = "space_redeemed"
    GAME_OPTIMIZED = "game_optimized"
    SYSTEM_BACKUP = "system_backup"


@dataclass
class MerkleNode:
    """Merkle tree node for cryptographic verification"""
    hash: str
    left_child: Optional['MerkleNode'] = None
    right_child: Optional['MerkleNode'] = None
    data: bytes = b''


@dataclass
class Block:
    """Blockchain block structure"""
    block_number: int
    timestamp: datetime
    transactions: List[Dict]
    previous_hash: str
    merkle_root: str
    nonce: int  # For proof-of-work
    miner: str  # Device that mined this block
    
    def calculate_merkle_root(self):
        """Calculate Merkle root from transactions"""
        if not self.transactions:
            return hashlib.sha256(b'').hexdigest()
        
        leaves = [MerkleNode(hashlib.sha256(json.dumps(t, sort_keys=True).encode()).hexdigest())
                 for t in self.transactions]
        
        while len(leaves) > 1:
            if len(leaves) % 2 == 1:
                leaves.append(leaves[-1])  # Duplicate last if odd
            
            new_layer = []
            for i in range(0, len(leaves), 2):
                combined = leaves[i].hash + leaves[i+1].hash
                new_layer.append(MerkleNode(hashlib.sha256(combined.encode()).hexdigest()))
            
            leaves = new_layer
        
        self.merkle_root = leaves[0].hash
        return self.merkle_root
    
    def to_dict(self) -> Dict:
        return {
            'block_number': self.block_number,
            'timestamp': self.timestamp.isoformat(),
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce,
            'miner': self.miner
        }


@dataclass
class NFTAchievement:
    """Non-fungible token representing an achievement"""
    nft_id: str
    token_id: int
    owner_address: str
    achievement_type: str
    metadata: Dict[str, Any]
    minted_at: datetime
    block_number: int
    ipfs_hash: str  # Decentralized storage reference
    
    def to_dict(self) -> Dict:
        return {
            'nft_id': self.nft_id,
            'token_id': self.token_id,
            'owner': self.owner_address,
            'type': self.achievement_type,
            'metadata': self.metadata,
            'minted_at': self.minted_at.isoformat(),
            'block_number': self.block_number,
            'ipfs_hash': self.ipfs_hash
        }


class BlockchainLedger:
    """
    Immutable blockchain ledger for audit trails.
    Records every cleanup operation cryptographically.
    """
    
    def __init__(self, genesis_block: bool = True):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.mining_difficulty = 2  # Leading zeros required
        self.node_address = f"{os.getlogin()}_{time.time()}"[:20]
        
        # Genesis block setup
        if genesis_block:
            genesis = self._create_genesis_block()
            self.chain.append(genesis)
            logger.info("⛏️  Created genesis block")
        
        print("🔗 Blockchain Ledger initialized")
    
    def _create_genesis_block(self) -> Block:
        """Create genesis (first) block"""
        return Block(
            block_number=0,
            timestamp=datetime.now(),
            transactions=[{'type': 'genesis', 'data': 'EatUp Pro Blockchain'}],
            previous_hash='0' * 64,
            merkle_root='',
            nonce=0,
            miner=self.node_address
        )
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1] if self.chain else None
    
    def add_transaction(self, tx_type: str, data: Dict):
        """Add transaction to pending pool"""
        transaction = {
            'tx_id': hashlib.sha256(f"{data}{time.time()}".encode()).hexdigest()[:16],
            'type': tx_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'signer': self.node_address
        }
        
        self.pending_transactions.append(transaction)
        logger.info(f"➕ Added {tx_type} transaction: {transaction['tx_id']}")
    
    def mine_block(self, miner_reward: float = 1000000) -> Optional[int]:
        """
        Mine next block using proof-of-work.
        Returns block number or None if mining fails.
        """
        if not self.pending_transactions:
            return None
        
        latest_block = self.get_latest_block()
        
        # Prepare block
        new_block = Block(
            block_number=len(self.chain),
            timestamp=datetime.now(),
            transactions=list(self.pending_transactions),
            previous_hash=latest_block.merkle_root,
            merkle_root='',
            nonce=0,
            miner=self.node_address
        )
        
        # Calculate target hash
        target = '0' * self.mining_difficulty
        
        # Proof-of-work mining
        start_time = time.time()
        
        while True:
            new_block.nonce += 1
            block_string = json.dumps(new_block.to_dict(), sort_keys=True)
            block_hash = hashlib.sha256(block_string.encode()).hexdigest()
            
            if block_hash.startswith(target):
                break
            
            # Prevent infinite loops
            if time.time() - start_time > 30:
                logger.warning("Mining timeout - reducing difficulty")
                self.mining_difficulty = max(1, self.mining_difficulty - 1)
                return None
        
        # Add rewards transaction
        reward_tx = {
            'tx_id': 'reward',
            'type': 'mining_reward',
            'amount': miner_reward,
            'recipient': self.node_address,
            'block': new_block.block_number
        }
        
        new_block.transactions.insert(0, reward_tx)
        new_block.calculate_merkle_root()
        
        # Validate and add to chain
        if self._is_chain_valid():
            self.chain.append(new_block)
            self.pending_transactions = []
            
            mining_time = time.time() - start_time
            logger.info(f"⛏️  Mined block #{new_block.block_number} in {mining_time:.2f}s")
            
            return new_block.block_number
        
        return None
    
    def _is_chain_valid(self) -> bool:
        """Validate entire blockchain integrity"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check previous hash linkage
            prev_hash = hashlib.sha256(
                json.dumps(previous.to_dict(), sort_keys=True).encode()
            ).hexdigest()
            
            if current.previous_hash != prev_hash:
                return False
            
            # Verify merkle root
            calculated_merkle = current.calculate_merkle_root()
            if current.merkle_root != calculated_merkle:
                return False
        
        return True
    
    def verify_integrity(self) -> bool:
        """Verify complete blockchain integrity"""
        is_valid = self._is_chain_valid()
        
        if is_valid:
            logger.info("✅ Blockchain integrity verified - all blocks valid")
        else:
            logger.error("❌ Blockchain corruption detected!")
        
        return is_valid
    
    def get_audit_trail(self, limit: int = 100) -> List[Dict]:
        """Get recent audit trail"""
        transactions = []
        
        for block in self.chain[-limit:]:
            for tx in block.transactions:
                tx['block_number'] = block.block_number
                transactions.append(tx)
        
        return sorted(transactions, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        total_transactions = sum(len(b.transactions) for b in self.chain)
        total_blocks = len(self.chain)
        total_mined = sum(
            sum(tx.get('amount', 0) for tx in b.transactions if tx.get('type') == 'mining_reward')
            for b in self.chain
        )
        
        return {
            'total_blocks': total_blocks,
            'total_transactions': total_transactions,
            'current_difficulty': self.mining_difficulty,
            'node_address': self.node_address,
            'chain_age_hours': (datetime.now() - self.chain[0].timestamp).total_seconds() / 3600,
            'total_rewards_miners': total_mined
        }


class NFTEcosystem:
    """NFT marketplace for achievements and achievements"""
    
    def __init__(self, blockchain: BlockchainLedger):
        self.blockchain = blockchain
        self.nfts: Dict[str, NFTAchievement] = {}
        self.token_counter = 0
        self.achievements_db = {
            'gigabyte_hero': {
                'name': 'Gigabyte Hero',
                'description': 'Freed 1+ GB of disk space',
                'tier': 'silver',
                'image_uri': 'ipfs://QmGigabyteHero'
            },
            'terabyte_master': {
                'name': 'Terabyte Master',
                'description': 'Cleaned 1+ TB total over lifetime',
                'tier': 'platinum',
                'image_uri': 'ipfs://QmTerabyteMaster'
            },
            'quantum_optimizer': {
                'name': 'Quantum Optimizer',
                'description': 'Used quantum-powered cleanup algorithm',
                'tier': 'gold',
                'image_uri': 'ipfs://QmQuantumOptimizer'
            },
            'distributed_champion': {
                'name': 'Distributed Champion',
                'description': 'Optimized 10+ devices simultaneously',
                'tier': 'platinum',
                'image_uri': 'ipfs://QmDistributedChampion'
            },
            'edge_computing_pioneer': {
                'name': 'Edge Computing Pioneer',
                'description': 'Managed edge/IoT devices',
                'tier': 'gold',
                'image_uri': 'ipfs://QmEdgePioneer'
            }
        }
        
        print("🎫 NFT Ecosystem initialized")
    
    def mint_achievement_nft(self, user_id: str, achievement_type: str, 
                            metadata: Dict) -> Optional[NFTAchievement]:
        """Mint new NFT for unlocked achievement"""
        
        if achievement_type not in self.achievements_db:
            logger.warning(f"Achievement {achievement_type} not found")
            return None
        
        # Mine block first to include NFT creation transaction
        self.blockchain.add_transaction('nft_mint', {
            'user': user_id,
            'achievement': achievement_type,
            'metadata': metadata
        })
        
        block_num = self.blockchain.mine_block()
        
        if block_num is None:
            return None
        
        # Create NFT
        self.token_counter += 1
        
        nft = NFTAchievement(
            nft_id=f"nft_{user_id}_{self.token_counter}",
            token_id=self.token_counter,
            owner_address=user_id,
            achievement_type=achievement_type,
            metadata={
                **self.achievements_db[achievement_type],
                **metadata
            },
            minted_at=datetime.now(),
            block_number=block_num,
            ipfs_hash=f"Qm{achievement_type}_{self.token_counter}"[:46]
        )
        
        self.nfts[nft.nft_id] = nft
        
        logger.info(f"🎫 Minted NFT #{self.token_counter} for {achievement_type}")
        
        return nft
    
    def get_user_nfts(self, user_id: str) -> List[Dict]:
        """Get all NFTs owned by user"""
        user_nfts = [
            nft.to_dict() for nft in self.nfts.values()
            if nft.owner_address == user_id
        ]
        
        # Sort by minted date descending
        return sorted(user_nfts, key=lambda x: x['minted_at'], reverse=True)
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get NFT marketplace statistics"""
        total_minted = len(self.nfts)
        unique_owners = len(set(nft.owner_address for nft in self.nfts.values()))
        tier_distribution = {}
        
        for nft in self.nfts.values():
            tier = nft.metadata.get('tier', 'unknown')
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        return {
            'total_nfts_minted': total_minted,
            'unique_collectors': unique_owners,
            'tier_distribution': tier_distribution,
            'achievements_available': len(self.achievements_db)
        }
    
    def create_community_challenge(self, challenge_name: str, 
                                  target_space_gb: float,
                                  deadline_days: int) -> Dict:
        """Create community-wide cleanup challenge"""
        
        challenge_id = f"challenge_{int(time.time())}"
        
        challenge = {
            'challenge_id': challenge_id,
            'name': challenge_name,
            'target_space_gb': target_space_gb,
            'deadline': datetime.now() + timedelta(days=deadline_days),
            'reward_nft': 'community_champion_badge',
            'participants': [],
            'status': 'active'
        }
        
        logger.info(f"🏆 Created challenge '{challenge_name}'")
        
        return challenge


class SecureAuditSystem:
    """Cryptographic audit trail system"""
    
    def __init__(self, blockchain: BlockchainLedger):
        self.blockchain = blockchain
        self.audit_events: deque = deque(maxlen=1000)
    
    def log_cleanup_event(self, event_data: Dict):
        """Log cleanup operation to blockchain"""
        self.blockchain.add_transaction('cleanup_operation', event_data)
        
        # Log locally for quick access
        audit_entry = {
            'event_type': 'cleanup',
            'data': event_data,
            'timestamp': datetime.now().isoformat(),
            'hash': hashlib.sha256(json.dumps(event_data).encode()).hexdigest()[:16]
        }
        
        self.audit_events.append(audit_entry)
    
    def log_game_optimization(self, game_info: Dict):
        """Log game cache optimization"""
        self.blockchain.add_transaction('game_optimized', game_info)
        
        audit_entry = {
            'event_type': 'game_optimization',
            'data': game_info,
            'timestamp': datetime.now().isoformat(),
            'hash': hashlib.sha256(json.dumps(game_info).encode()).hexdigest()[:16]
        }
        
        self.audit_events.append(audit_entry)
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        events = list(self.audit_events)[-100:]
        
        return {
            'generated_at': datetime.now().isoformat(),
            'total_events': len(events),
            'events_last_hour': len([e for e in events if (datetime.now() - datetime.fromisoformat(e['timestamp'])).hours < 1]),
            'blockchain_verification': self.blockchain.verify_integrity(),
            'recent_blocks': len(self.blockchain.chain),
            'event_types': self._categorize_events(events)
        }
    
    def _categorize_events(self, events: List) -> Dict[str, int]:
        """Categorize events by type"""
        categories = {}
        
        for event in events:
            evt_type = event['event_type']
            categories[evt_type] = categories.get(evt_type, 0) + 1
        
        return categories


# Utility classes
class IPFSClient:
    """Simulated IPFS client for decentralized storage"""
    
    def __init__(self):
        self.files: Dict[str, bytes] = {}
        self.pin_count = 0
    
    def add_file(self, content: bytes, filename: str = "data") -> str:
        """Add file to IPFS network, returns hash"""
        file_hash = hashlib.sha256(content).hexdigest()
        
        self.files[file_hash] = content
        self.pin_count += 1
        
        return f"Qm{file_hash[:46]}"
    
    def get_file(self, cid: str) -> Optional[bytes]:
        """Retrieve file from IPFS by content identifier"""
        for hash_key, content in self.files.items():
            if f"Qm{hash_key[:46]}" == cid:
                return content
        return None


class CryptoWallet:
    """Cryptocurrency wallet for ecosystem tokens"""
    
    def __init__(self, address: str):
        self.address = address
        self.balance = 0  # EatUp tokens
        self.transactions = []
    
    def receive_payment(self, amount: int, sender: str, tx_hash: str):
        """Receive token payment"""
        self.balance += amount
        self.transactions.append({
            'type': 'receive',
            'amount': amount,
            'sender': sender,
            'tx_hash': tx_hash,
            'timestamp': datetime.now().isoformat()
        })
    
    def send_payment(self, amount: int, recipient: str) -> bool:
        """Send tokens to another address"""
        if amount <= self.balance:
            self.balance -= amount
            self.transactions.append({
                'type': 'send',
                'amount': amount,
                'recipient': recipient,
                'tx_hash': hashlib.sha256(f"{recipient}{time.time()}".encode()).hexdigest()[:16],
                'timestamp': datetime.now().isoformat()
            })
            return True
        return False
    
    def get_balance(self) -> int:
        """Get current token balance"""
        return self.balance


# Main CLI interface
if __name__ == "__main__":
    print("="*80)
    print("🔗 EATUP PRO BLOCKCHAIN & NFT ECOSYSTEM v6.0")
    print("Decentralized Storage Optimization Platform")
    print("="*80)
    
    # Initialize blockchain
    blockchain = BlockchainLedger()
    
    # Initialize NFT ecosystem
    nft_ecosystem = NFTEcosystem(blockchain)
    
    # Initialize audit system
    audit_system = SecureAuditSystem(blockchain)
    
    # Simulate operations
    print("\n📝 Logging cleanup operations...")
    
    for i in range(5):
        audit_system.log_cleanup_event({
            'operation': 'smart_cleanup',
            'space_freed_mb': 500 + i * 100,
            'files_removed': 100 + i * 20
        })
        
        # Mine block periodically
        if i % 2 == 0:
            blockchain.mine_block()
    
    # Mint some achievements
    print("\n🎫 Minting NFT achievements...")
    
    achievements_to_mint = ['gigabyte_hero', 'quantum_optimizer', 'terabyte_master']
    minted_nfts = []
    
    for achievement in achievements_to_mint:
        nft = nft_ecosystem.mint_achievement_nft(
            user_id="henry",
            achievement_type=achievement,
            metadata={'difficulty': 'high', 'verified': True}
        )
        if nft:
            minted_nfts.append(nft)
    
    # Show results
    print("\n📊 System Statistics:")
    
    stats = blockchain.get_statistics()
    print(f"\n🔗 Blockchain:")
    print(f"  Total Blocks: {stats['total_blocks']}")
    print(f"  Transactions: {stats['total_transactions']}")
    print(f"  Mining Difficulty: {stats['current_difficulty']}")
    
    nft_stats = nft_ecosystem.get_marketplace_stats()
    print(f"\n🎫 NFT Marketplace:")
    print(f"  Total Minted: {nft_stats['total_nfts_minted']}")
    print(f"  Unique Collectors: {nft_stats['unique_collectors']}")
    
    # Verify integrity
    print("\n✅ Verifying blockchain integrity...")
    if blockchain.verify_integrity():
        print("   Blockchain is cryptographically secure!")
    
    # Generate audit report
    print("\n📋 Audit Report:")
    audit_report = audit_system.generate_audit_report()
    print(json.dumps(audit_report, indent=2))
