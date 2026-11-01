"""Start only the hash-verified private loopback test database."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/delivery/isolated-neo4j'
sys.path.insert(0,str(BASE/'packages'))
from neo4j import GraphDatabase


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    version='5.26.32';home=Path('C:/Windows/Temp/openharmony-neo4j-distribution-v4')/('neo4j-community-'+version)
    setup=json.loads((ROOT/'docs/official-data-delivery/isolated-neo4j-setup.json').read_text(encoding='utf-8'))
    archive=BASE/('neo4j-community-'+version+'-windows.zip')
    h=hashlib.sha256()
    with archive.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    if h.hexdigest()!=setup['archive_sha256'] or setup['version']!=version:raise ValueError('Distribution receipt mismatch')
    instance=Path('C:/Windows/Temp/openharmony-neo4j-test-v4');instance.mkdir(exist_ok=False)
    conf=instance/'conf';conf.mkdir()
    for name in ['data','logs','run','plugins','import','transactions']:(instance/name).mkdir()
    lines=['server.default_listen_address=127.0.0.1','server.default_advertised_address=127.0.0.1',
       'server.bolt.enabled=true','server.bolt.listen_address=127.0.0.1:17687','server.bolt.advertised_address=127.0.0.1:17687',
       'server.http.enabled=true','server.http.listen_address=127.0.0.1:17474','server.http.advertised_address=127.0.0.1:17474',
       'server.https.enabled=false','dbms.security.auth_enabled=true','dbms.usage_report.enabled=false',
       'server.memory.heap.initial_size=256m','server.memory.heap.max_size=512m','server.memory.pagecache.size=256m']
    for key,name in [('data','data'),('logs','logs'),('run','run'),('plugins','plugins'),('import','import'),('transaction.logs.root','transactions')]:
        lines.append('server.directories.'+key+'='+(instance/name).as_posix())
    (conf/'neo4j.conf').write_text(('\n'.join(lines)+'\n').encode('ascii','backslashreplace').decode('ascii'),encoding='ascii',newline='\n')
    for port in [17687,17474]:
        with socket.socket() as s:s.bind(('127.0.0.1',port))
    java_home=Path('C:/Program Files/Huawei/DevEco Studio/jbr');java=java_home/'bin/java.exe'
    env={**os.environ,'JAVA_HOME':str(java_home),'NEO4J_HOME':str(home),'NEO4J_CONF':str(conf)}
    prefix=[str(java),'-cp',str(home/'lib/*'),'-Dbasedir='+str(home)]
    password=secrets.token_urlsafe(24)
    private={'uri':'bolt://127.0.0.1:17687','username':'neo4j','password':password,'database':'neo4j','version':version,'scope':'Private test instance only'}
    write(instance/'connection-private.json',private)
    initialized=subprocess.run(prefix+['org.neo4j.server.startup.Neo4jAdminCommand','dbms','set-initial-password',password],env=env,cwd=instance,capture_output=True,timeout=60)
    if initialized.returncode:raise RuntimeError('Private initial authentication setup failed; see local setup context')
    with (instance/'server-output.log').open('ab') as log:
        process=subprocess.Popen(prefix+['org.neo4j.server.startup.Neo4jCommand','console'],env=env,cwd=instance,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    write(instance/'process.json',{'pid':process.pid,'home':str(home),'conf':str(conf),'scope':'Only this isolated launcher'})
    deadline=time.monotonic()+90;last_error=None
    while time.monotonic()<deadline:
        if process.poll() is not None:raise RuntimeError('Isolated database launcher exited; inspect its local log')
        try:
            with GraphDatabase.driver(private['uri'],auth=(private['username'],password),connection_timeout=2,max_transaction_retry_time=0) as driver:
                driver.verify_connectivity()
                with driver.session(database='neo4j') as session:
                    components=session.run('CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition').data()
                    count=session.run('MATCH (n) RETURN count(n) AS total').single()['total']
            if not any(version in c['versions'] for c in components) or count!=0:raise ValueError('Unexpected server version or nonempty test instance')
            report={'version':version,'components':components,'bolt':'127.0.0.1:17687','http':'127.0.0.1:17474',
                    'server_started':True,'authenticated_connection_verified':True,'initial_node_count':count,
                    'private_credentials_published':False,'shared_database_updated':False,'sample_import_verified':False,
                    'configuration_sha256':hashlib.sha256((conf/'neo4j.conf').read_bytes()).hexdigest()}
            write(ROOT/'docs/official-data-delivery/isolated-neo4j-startup.json',report)
            print(json.dumps(report));return
        except ValueError:raise
        except Exception as exc:last_error=type(exc).__name__;time.sleep(2)
    raise RuntimeError('Isolated startup timed out; last error type='+str(last_error))


if __name__=='__main__':main()
