#!/usr/bin/env python3
"""
EatUp Pro v8.2+ - Blockchain Achievement & NFT System
Mint achievements as NFTs, track crypto-style rewards
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Set
import secrets


@dataclass
class Achievement:
    """Achievement definition"""
    id: str
    name: str
    description: str
    icon: str
    xp_reward: int
    rarity: str  # common, uncommon, rare, epic, legendary
    requirements: Dict[str, Any]
    unlocked_at: Optional[str] = None
    
    def is_unlocked(self, user_stats: Dict) -> bool:
        """Check if achievement should be unlocked"""
        for metric, threshold in self.requirements.items():
            if isinstance(threshold, dict):
                # Complex condition
                if metric in threshold:
                    action = threshold[metric]
                    value = user_stats.get(metric.split('.')[-1], 0)
                    
                    if action == 'greater_than' and not (value > threshold.get('value', 0)):
                        return False
                    elif action == 'less_than' and not (value < threshold.get('value', 0)):
                        return False
                    elif action == 'exact' and not (value == threshold.get('value')):
                        return False
            else:
                # Simple comparison
                parts = metric.split('_')
                stat_name = parts[0].replace('total_', '')
                
                if stat_name in user_stats:
                    if not (user_stats[stat_name] >= threshold):
                        return False
        
        return True


@dataclass
class MintedNFT:
    """NFT minting record"""
    nft_id: str
    achievement_id: str
    owner_address: str
    token_uri: str
    mint_timestamp: str
    transaction_hash: str
    ipfs_cid: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class BlockChainLedger:
    """Simulated blockchain for immutable audit trail"""
    
    def __init__(self):
        self.chain: List[Dict] = []
        self.pending_transactions: List[Dict] = []
        self.difficulty = 2  # Mining difficulty
        self.nonce = 0
        
        # Initialize genesis block
        self._create_genesis_block()
        
        print("🔗 Blockchain Ledger Initialized")
    
    def _create_genesis_block(self):
        """Create initial genesis block"""
        genesis_block = {
            'index': 0,
            'timestamp': datetime.now().isoformat(),
            'transactions': [],
            'previous_hash': '0' * 64,
            'hash': self._generate_hash({}),
            'nonce': 0
        }
        
        self.chain.append(genesis_block)
    
    def _generate_hash(self, block_data: Dict) -> str:
        """Generate SHA-256 hash of block"""
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def proof_of_work(self, previous_hash: str) -> int:
        """Mining proof-of-work algorithm"""
        target = '0' * (self.difficulty * 2)
        
        while True:
            nonce = self.nonce
            nonce += 1
            
            block_data = {
                'previous_hash': previous_hash,
                'nonce': nonce,
                'timestamp': datetime.now().isoformat()
            }
            
            current_hash = self._generate_hash(block_data)
            
            if current_hash.startswith(target):
                self.nonce = nonce
                return nonce
    
    def add_transaction(self, tx_type: str, **kwargs):
        """Add transaction to pending pool"""
        tx = {
            'type': tx_type,
            'timestamp': datetime.now().isoformat(),
            'data': kwargs,
            'id': f"tx_{secrets.token_hex(8)}"
        }
        
        self.pending_transactions.append(tx)
        
        # Auto-mine when enough transactions accumulate
        if len(self.pending_transactions) >= 3:
            self._mine_block()
    
    def _mine_block(self):
        """Mine pending transactions into block"""
        if not self.pending_transactions:
            return
        
        previous_hash = self.chain[-1]['hash']
        nonce = self.proof_of_work(previous_hash)
        
        new_block = {
            'index': len(self.chain),
            'timestamp': datetime.now().isoformat(),
            'transactions': self.pending_transactions.copy(),
            'previous_hash': previous_hash,
            'hash': self._generate_hash({
                'previous_hash': previous_hash,
                'nonce': nonce,
                'transactions': self.pending_transactions
            }),
            'nonce': nonce
        }
        
        self.chain.append(new_block)
        self.pending_transactions.clear()
        
        print(f"⛏️  Mined block #{new_block['index']} with {len(new_block['transactions'])} transactions")
    
    def get_chain_info(self) -> Dict:
        """Get blockchain information"""
        return {
            'chain_length': len(self.chain),
            'latest_block': self.chain[-1]['index'],
            'latest_hash': self.chain[-1]['hash'],
            'pending_transactions': len(self.pending_transactions),
            'difficulty': self.difficulty
        }


class NFTEcosystem:
    """NFT minting and trading system for achievements"""
    
    def __init__(self):
        self.minted_nfts: List[MintedNFT] = []
        self.ipfs_store: Dict[str, Any] = {}  # Simulated IPFS storage
        self.marketplace_listings: Dict[str, Dict] = {}
        
        print("🎨 NFT Ecosystem Initialized")
    
    def calculate_rarity_score(self, achievement: Achievement) -> float:
        """Calculate rarity based on requirement difficulty"""
        base_scores = {
            'common': 1.0,
            'uncommon': 2.5,
            'rare': 5.0,
            'epic': 10.0,
            'legendary': 25.0
        }
        
        complexity_bonus = len(achievement.requirements) * 0.5
        
        return base_scores.get(achievement.rarity, 1.0) + complexity_bonus
    
    def mint_achievement_nft(self, achievement: Achievement, 
                            owner_address: str, 
                            user_stats: Dict) -> MintedNFT:
        """Mint NFT for newly unlocked achievement"""
        nft_id = f"nft_{secrets.token_hex(16)}"
        mint_time = datetime.now().isoformat()
        
        # Create metadata
        metadata = {
            'name': f"{achievement.name} Badge",
            'description': achievement.description,
            'image': f"ipfs://achievements/{achievement.icon}.png",
            'attributes': [
                {'trait_type': 'Rarity', 'value': achievement.rarity},
                {'trait_type': 'XP Value', 'value': achievement.xp_reward},
                {'trait_type': 'Unlock Date', 'value': mint_time},
                {'trait_type': 'Type', 'value': 'achievement'}
            ]
        }
        
        # Store in "IPFS" (simulated)
        ipfs_cid = hashlib.sha256(json.dumps(metadata).encode()).hexdigest()[:64]
        self.ipfs_store[ipfs_cid] = metadata
        
        # Create transaction record
        nft = MintedNFT(
            nft_id=nft_id,
            achievement_id=achievement.id,
            owner_address=owner_address,
            token_uri=f"ipfs://{ipfs_cid}",
            mint_timestamp=mint_time,
            transaction_hash=secrets.token_hex(32),
            ipfs_cid=ipfs_cid,
            metadata=metadata
        )
        
        self.minted_nfts.append(nft)
        
        print(f"✨ Minted NFT #{nft_id[-8:]} for {achievement.name}")
        
        return nft
    
    def list_on_marketplace(self, nft_id: str, price_eth: float):
        """List NFT for sale"""
        nft = next((n for n in self.minted_nfts if n.nft_id == nft_id), None)
        
        if not nft:
            raise ValueError("NFT not found")
        
        self.marketplace_listings[nft_id] = {
            'seller': nft.owner_address,
            'price_eth': price_eth,
            'listing_time': datetime.now().isoformat(),
            'status': 'active'
        }
        
        print(f"🏪 Listed NFT #{nft_id[-8:]} on marketplace")
    
    def buy_nft(self, buyer_address: str, nft_id: str):
        """Purchase NFT from marketplace"""
        if nft_id not in self.marketplace_listings:
            raise ValueError("NFT not listed for sale")
        
        listing = self.marketplace_listings[nft_id]
        
        if listing['status'] != 'active':
            raise ValueError("NFT no longer available")
        
        # Update ownership
        nft = next((n for n in self.minted_nfts if n.nft_id == nft_id))
        old_owner = nft.owner_address
        nft.owner_address = buyer_address
        
        # Update listing status
        listing['status'] = 'sold'
        listing['buyer'] = buyer_address
        listing['sale_price'] = listing['price_eth']
        
        print(f"💰 Sold NFT #{nft_id[-8:]} from {old_owner[:8]} to {buyer_address[:8]}")


class SecureAuditSystem:
    """Cryptographically secure audit logging"""
    
    def __init__(self):
        self.audit_log: List[Dict] = []
        self.merkle_tree: Dict[str, Any] = None
        
        print("🛡️  Secure Audit System Initialized")
    
    def _compute_merkle_root(self, transactions: List[Dict]) -> str:
        """Compute Merkle root for transaction verification"""
        if not transactions:
            return '0' * 64
        
        hashes = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() 
                 for tx in transactions]
        
        # Build Merkle tree
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            
            hashes = [
                hashlib.sha256(
                    (hashes[i] + hashes[i+1]).encode()
                ).hexdigest()
                for i in range(0, len(hashes), 2)
            ]
        
        return hashes[0]
    
    def log_action(self, action_type: str, actor: str, 
                   details: Dict, security_level: str = 'normal'):
        """Log action with cryptographic verification"""
        audit_entry = {
            'action': action_type,
            'actor': actor,
            'details': details,
            'security_level': security_level,
            'timestamp': datetime.now().isoformat(),
            'id': f"audit_{secrets.token_hex(12)}"
        }
        
        self.audit_log.append(audit_entry)
        
        # Compute Merkle root periodically
        if len(self.audit_log) % 10 == 0:
            self.merkle_tree = {
                'root': self._compute_merkle_root(self.audit_log[-100:]),
                'block_size': 100,
                'created_at': datetime.now().isoformat()
            }
        
        print(f"📝 Audit logged: {action_type} by {actor}")
        
        return audit_entry


def main():
    """Demo NFT Achievement System"""
    print("="*60)
    print("EatUp Pro NFT Achievement System v8.2+")
    print("="*60)
    
    # Create achievements catalog
    achievements = [
        Achievement(
            id="first_cleanup",
            name="First Step",
            description="Performed your first disk cleanup",
            icon="boot.png",
            xp_reward=10,
            rarity="common",
            requirements={"total_cleanups": {"greater_than": 0}}
        ),
        Achievement(
            id="space_saver",
            name="Storage Wizard",
            description="Saved 1GB of disk space",
            icon="wizard.png",
            xp_reward=50,
            rarity="uncommon",
            requirements={"total_space_saved_mb": {"greater_than": 1024}}
        ),
        Achievement(
            id="detection_expert",
            name="Duplicate Hunter",
            description="Found and removed 100 duplicate files",
            icon="hunter.png",
            xp_reward=100,
            rarity="rare",
            requirements={"total_duplicates_removed": {"greater_than": 100}}
        ),
        Achievement(
            id="consistent",
            name="Daily Cleaner",
            description="Cleaned for 7 consecutive days",
            icon="streak.png",
            xp_reward=150,
            rarity="epic",
            requirements={"consecutive_days": {"greater_than": 7}}
        ),
        Achievement(
            id="mega_master",
            name="Disk Master",
            description="Saved 10GB total and cleaned 1000+ files",
            icon="master.png",
            xp_reward=500,
            rarity="legendary",
            requirements={
                "total_space_saved_gb": {"greater_than": 10},
                "total_files_cleaned": {"greater_than": 1000}
            }
        )
    ]
    
    # Initialize systems
    ledger = BlockChainLedger()
    nft_system = NFTEcosystem()
    audit = SecureAuditSystem()
    
    # Simulate user activity
    print("\n🎮 Simulating User Activity...")
    
    # Log some cleanup actions
    for i in range(5):
        ledger.add_transaction(
            type='cleanup_operation',
            space_saved_mb=i*100,
            files_cleaned=i*50
        )
    
    # User completes first cleanup
    user_stats = {
        'total_space_saved_mb': 500,
        'total_files_cleaned': 250,
        'total_cleanup_ops': 5
    }
    
    user_address = "0x" + secrets.token_hex(20)
    
    # Check achievements
    print("\n🏆 Checking Achievements...")
    for achievement in achievements:
        if achievement.is_unlocked(user_stats):
            print(f"\n🎉 ACHIEVEMENT UNLOCKED: {achievement.name}")
            
            # Log audit entry
            audit.log_action(
                action_type='achievement_unlocked',
                actor=user_address,
                details={'achievement_id': achievement.id, 'name': achievement.name}
            )
            
            # Mint NFT
            nft = nft_system.mint_achievement_nft(
                achievement=achievement,
                owner_address=user_address,
                user_stats=user_stats
            )
            
            # List on marketplace
            nft_system.list_on_marketplace(
                nft_id=nft.nft_id,
                price_eth=0.1 * achievement.xp_reward / 100
            )
    
    # Show blockchain info
    print("\n📊 Blockchain Status:")
    chain_info = ledger.get_chain_info()
    print(json.dumps(chain_info, indent=2))
    
    print(f"\n🎨 Total NFTs Minted: {len(nft_system.minted_nfts)}")
    print(f"📃 Audit Entries: {len(audit.audit_log)}")
    
    if audit.merkle_tree:
        print(f"\t🌳 Merkle Root: {audit.merkle_tree['root'][:32]}...")


if __name__ == '__main__':
    main()
