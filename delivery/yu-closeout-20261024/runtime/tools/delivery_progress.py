"""Content-bound work keys. A historical path-only receipt is never resumable."""
import hashlib
import json


def work_key(source, path, input_sha256, processor_sha256, configuration):
    payload=['delivery-work-v1',source['repository'],source['commit'],source['kind'],
             source['release_id'],path,input_sha256,processor_sha256,configuration]
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,
                                    separators=(',',':'),allow_nan=False).encode()).hexdigest()


def reusable(receipt, key, artifact_sha256):
    return (receipt.get('schema_version')==1 and receipt.get('work_key')==key
            and receipt.get('status')=='verified'
            and receipt.get('artifact_sha256')==artifact_sha256
            and isinstance(artifact_sha256,str) and len(artifact_sha256)==64)
