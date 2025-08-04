#!/usr/bin/env python3
"""
Generate a meaningful change log by comparing snapshots from different days.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

def find_snapshots_for_comparison(character_id: int):
    """Find snapshots from different time periods for meaningful comparison."""
    files = []
    
    for root, dirs, filenames in os.walk('character_data'):
        for filename in filenames:
            if f'{character_id}' in filename and filename.endswith('.json') and 'raw' not in filename:
                filepath = Path(root) / filename
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                files.append((filepath, mtime))
    
    # Sort by modification time
    files.sort(key=lambda x: x[1])
    
    if len(files) < 2:
        return None, None
    
    # Get snapshots from different days if possible
    recent_snapshot = files[-1][0]  # Most recent
    
    # Find an older snapshot from a different day
    recent_date = files[-1][1].date()
    older_snapshot = None
    
    for filepath, mtime in reversed(files[:-1]):
        if mtime.date() != recent_date:
            older_snapshot = filepath
            break
    
    # If no different day found, just use the second most recent
    if older_snapshot is None:
        older_snapshot = files[-2][0]
    
    return older_snapshot, recent_snapshot

async def compare_snapshots_detailed(old_file: Path, new_file: Path):
    """Compare two snapshots and detect detailed changes."""
    
    print(f"Comparing:")
    print(f"  Old: {old_file} ({datetime.fromtimestamp(old_file.stat().st_mtime)})")
    print(f"  New: {new_file} ({datetime.fromtimestamp(new_file.stat().st_mtime)})")
    
    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    with open(new_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    changes = []
    
    # Character info changes
    old_info = old_data.get('character_info', {})
    new_info = new_data.get('character_info', {})
    
    if old_info.get('level') != new_info.get('level'):
        changes.append({
            'type': 'level_change',
            'category': 'progression',
            'field': 'character_info.level',
            'old_value': old_info.get('level'),
            'new_value': new_info.get('level'),
            'description': f"Level changed from {old_info.get('level')} to {new_info.get('level')}",
            'priority': 'high'
        })
    
    if old_info.get('experience_points') != new_info.get('experience_points'):
        changes.append({
            'type': 'experience_change',
            'category': 'progression',
            'field': 'character_info.experience_points',
            'old_value': old_info.get('experience_points'),
            'new_value': new_info.get('experience_points'),
            'description': f"Experience changed from {old_info.get('experience_points')} to {new_info.get('experience_points')}",
            'priority': 'medium'
        })
    
    # Spell changes
    old_spells = old_data.get('spells', {}).get('spells', [])
    new_spells = new_data.get('spells', {}).get('spells', [])
    
    old_spell_names = {spell.get('name') for spell in old_spells if isinstance(spell, dict) and spell.get('name')}
    new_spell_names = {spell.get('name') for spell in new_spells if isinstance(spell, dict) and spell.get('name')}
    
    added_spells = new_spell_names - old_spell_names
    removed_spells = old_spell_names - new_spell_names
    
    for spell in added_spells:
        # Find spell details
        spell_details = next((s for s in new_spells if isinstance(s, dict) and s.get('name') == spell), {})
        level = spell_details.get('level', 'Unknown')
        
        changes.append({
            'type': 'spell_added',
            'category': 'spells',
            'field': 'spells.spells',
            'old_value': None,
            'new_value': {'name': spell, 'level': level},
            'description': f"Added spell: {spell} (Level {level})",
            'priority': 'medium'
        })
    
    for spell in removed_spells:
        # Find spell details
        spell_details = next((s for s in old_spells if isinstance(s, dict) and s.get('name') == spell), {})
        level = spell_details.get('level', 'Unknown')
        
        changes.append({
            'type': 'spell_removed',
            'category': 'spells',
            'field': 'spells.spells',
            'old_value': {'name': spell, 'level': level},
            'new_value': None,
            'description': f"Removed spell: {spell} (Level {level})",
            'priority': 'medium'
        })
    
    # Ability score changes
    old_abilities = old_data.get('abilities', {}).get('ability_scores', {})
    new_abilities = new_data.get('abilities', {}).get('ability_scores', {})
    
    for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
        old_score = old_abilities.get(ability, {}).get('score', 0) if isinstance(old_abilities.get(ability), dict) else 0
        new_score = new_abilities.get(ability, {}).get('score', 0) if isinstance(new_abilities.get(ability), dict) else 0
        
        if old_score != new_score:
            changes.append({
                'type': 'ability_score_change',
                'category': 'abilities',
                'field': f'abilities.ability_scores.{ability}.score',
                'old_value': old_score,
                'new_value': new_score,
                'description': f"{ability.title()} score changed from {old_score} to {new_score}",
                'priority': 'high'
            })
    
    # Hit points changes
    old_hp = old_data.get('combat', {}).get('hit_points', {}).get('maximum', 0)
    new_hp = new_data.get('combat', {}).get('hit_points', {}).get('maximum', 0)
    
    if old_hp != new_hp:
        changes.append({
            'type': 'max_hp_change',
            'category': 'combat',
            'field': 'combat.hit_points.maximum',
            'old_value': old_hp,
            'new_value': new_hp,
            'description': f"Maximum HP changed from {old_hp} to {new_hp}",
            'priority': 'high'
        })
    
    # Features changes (simplified)
    old_features = old_data.get('features', {})
    new_features = new_data.get('features', {})
    
    # Check class features
    old_class_features = old_features.get('class_features', [])
    new_class_features = new_features.get('class_features', [])
    
    old_feature_names = {f.get('name') for f in old_class_features if isinstance(f, dict) and f.get('name')}
    new_feature_names = {f.get('name') for f in new_class_features if isinstance(f, dict) and f.get('name')}
    
    added_features = new_feature_names - old_feature_names
    removed_features = old_feature_names - new_feature_names
    
    for feature in added_features:
        changes.append({
            'type': 'class_feature_added',
            'category': 'features',
            'field': 'features.class_features',
            'old_value': None,
            'new_value': feature,
            'description': f"Gained class feature: {feature}",
            'priority': 'high'
        })
    
    for feature in removed_features:
        changes.append({
            'type': 'class_feature_removed',
            'category': 'features',
            'field': 'features.class_features',
            'old_value': feature,
            'new_value': None,
            'description': f"Lost class feature: {feature}",
            'priority': 'high'
        })
    
    return changes

async def create_detailed_change_log(character_id: int):
    """Create a detailed change log with meaningful changes."""
    
    print(f"\n{'='*80}")
    print(f"CREATING DETAILED CHANGE LOG FOR CHARACTER {character_id}")
    print(f"{'='*80}")
    
    # Find snapshots to compare
    old_snapshot, new_snapshot = find_snapshots_for_comparison(character_id)
    
    if not old_snapshot or not new_snapshot:
        print("❌ Could not find suitable snapshots for comparison")
        return False
    
    # Compare snapshots
    changes = await compare_snapshots_detailed(old_snapshot, new_snapshot)
    
    print(f"\n✅ Detected {len(changes)} changes")
    
    if changes:
        print("\nChanges found:")
        for i, change in enumerate(changes, 1):
            print(f"  {i}. {change['description']} (Priority: {change['priority']})")
    
    # Create change log
    change_log_dir = Path('character_data/change_logs') / str(character_id)
    change_log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now()
    
    # Load character name from new snapshot
    with open(new_snapshot, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    character_name = new_data.get('character_info', {}).get('name', 'Unknown')
    
    log_entry = {
        'character_id': character_id,
        'character_name': character_name,
        'log_version': '1.0',
        'log_period': timestamp.strftime('%Y-%m'),
        'created_at': timestamp.isoformat(),
        'last_updated': timestamp.isoformat(),
        'total_entries': len(changes),
        'entries': [],
        'metadata': {
            'source_snapshots': [str(old_snapshot), str(new_snapshot)],
            'comparison_timestamp': timestamp.isoformat(),
            'log_generator': 'generate_meaningful_change_log.py',
            'snapshot_time_diff': str(datetime.fromtimestamp(new_snapshot.stat().st_mtime) - datetime.fromtimestamp(old_snapshot.stat().st_mtime)),
            'log_file_size': 0
        }
    }
    
    # Add detailed entries
    for change in changes:
        entry = {
            'timestamp': timestamp.isoformat(),
            'change_type': change['type'],
            'category': change['category'],
            'field_path': change['field'],
            'old_value': change['old_value'],
            'new_value': change['new_value'],
            'description': change['description'],
            'detailed_description': f"Character progression: {change['description']}",
            'priority': change['priority'],
            'causation': {
                'trigger': 'character_progression',
                'trigger_details': {
                    'change_type': change['type'],
                    'field_changed': change['field']
                },
                'related_changes': [],
                'cascade_depth': 0
            },
            'attribution': {
                'source': 'character_development',
                'source_name': change['type'].replace('_', ' ').title(),
                'source_type': 'progression',
                'impact_summary': change['description']
            },
            'metadata': {
                'detection_method': 'detailed_snapshot_comparison',
                'confidence': 'high',
                'priority_level': change['priority']
            }
        }
        log_entry['entries'].append(entry)
    
    # Write change log
    log_filename = f"detailed_changes_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    log_file_path = change_log_dir / log_filename
    
    with open(log_file_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)
    
    # Update file size
    log_entry['metadata']['log_file_size'] = log_file_path.stat().st_size
    
    with open(log_file_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Detailed change log created: {log_file_path}")
    print(f"📊 Log contains {len(changes)} change entries")
    print(f"💾 File size: {log_file_path.stat().st_size} bytes")
    
    return True

if __name__ == '__main__':
    character_id = 145081718
    
    if len(sys.argv) > 1:
        try:
            character_id = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid character ID provided")
            sys.exit(1)
    
    success = asyncio.run(create_detailed_change_log(character_id))
    
    if success:
        print(f"\n🎉 SUCCESS! Detailed change log generated for character {character_id}")
        print(f"📁 Location: character_data/change_logs/{character_id}/")
    else:
        print(f"\n💥 FAILED to generate change log for character {character_id}")
    
    sys.exit(0 if success else 1)