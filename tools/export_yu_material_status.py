"""Export only Yu's document/sample provenance, without raw data or machine paths."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from collect_official_sources import write_json

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'data/delivery')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/official-data-delivery/yu-source-lock.json')
    args=parser.parse_args()
    sources=json.loads((args.root/'sources.json').read_text(encoding='utf-8'))['sources']
    fields=('source_id','kind','platform','release_id','official_release_name','api_level','repository',
            'ref','commit','snapshot_kind','sdk_package_version','mapping_status','resolved_at','status',
            'body_status','body_storage','archive_url','archive_transport','archive_normalization',
            'archive_sha256','archive_size','file_count','excluded_files','lfs_pointers','lfs_expanded_files_verified','submodules',
            'license_files','license_evidence','collected_at')
    records=[]
    for source in sources:
        if source['kind'] not in ('docs','samples'): continue
        record={k:source[k] for k in fields if k in source}
        inventory_path=args.root/'sources'/source['source_id']/'inventory.json'
        if inventory_path.exists():
            raw=inventory_path.read_bytes(); inventory=json.loads(raw)
            matched=inventory.get('complete') and inventory['commit']==source['commit']
            record.update(inventory_status='complete' if matched else 'commit_mismatch',
                          inventory_file_count=len(inventory['files']),
                          inventory_sha256=hashlib.sha256(raw).hexdigest())
        else: record['inventory_status']='not_obtained_for_exact_commit'
        if source['status']!='collected':
            error=source.get('error','').lower()
            record['error_class']='connection_interrupted' if any(s in error for s in ('eof','disconnect','ssl','curl 56')) else 'previous_attempt_failed_or_pending'
        records.append(record)
    complete=len(records)==10 and all(r['status']=='collected' and r.get('body_status')=='complete' for r in records)
    write_json(args.output,{'schema_version':1,'as_of':datetime.now(timezone.utc).isoformat(),
                           'sources':records,'all_target_bodies_collected':complete,
                           'cross_repository_pairing':'candidate_only_sdk_pairing_not_verified',
                           'scope':'Five initial named releases, all Chinese documentation domains and complete sample repositories. No master fallback; historical patch/LTS identities preserved.'})
    print('Document/sample locks:',len(records),'collected:',sum(r['status']=='collected' for r in records),flush=True)

if __name__=='__main__':main()
