from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from collect_official_sources import ROOT
from extract_document_semantics import extract,create_index,ingest
from query_document_candidates import open_readonly,search


class QueryTests(unittest.TestCase):
    def test_owner_version_empty_limit_and_actual_write_rejection(self):
        base=ROOT/'data/delivery/test-temp';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as temporary:
            path=Path(temporary)/'candidates.db';facts=[]
            for release in ('fixed-a','fixed-b'):
                for owner,adapter in [('AudioRenderer','audio_renderer'),('AudioCapturer','audio_capturer')]:
                    text='# Interface ('+owner+')\n## 属性\n| 名称 | 类型 |\n| -- | -- |\n| state | AudioState |\n'
                    evidence={'source_id':release+owner,'release_id':release,'path':owner+'.md'}
                    records,_=extract(text,evidence,adapter);facts.extend(records)
            with closing(sqlite3.connect(path)) as writable:create_index(writable);ingest(writable,facts)
            with closing(open_readonly(path)) as connection:
                exact=search(connection,'fixed-a',owner='AudioRenderer',name='state',kind='property')
                self.assertEqual(len(exact),1)
                self.assertEqual(exact[0]['owner'],'AudioRenderer')
                self.assertEqual(exact[0]['evidence']['release_id'],'fixed-a')
                self.assertEqual(search(connection,'unknown',name='state'),[])
                self.assertEqual(len(search(connection,'fixed-a',query='state',limit=1)),1)
                with self.assertRaises(ValueError):search(connection,'fixed-a',name='state',limit=101)
                with self.assertRaises(sqlite3.OperationalError):connection.execute('DELETE FROM entities')
                self.assertEqual(connection.execute('SELECT count(*) FROM entities').fetchone()[0],4)
                self.assertNotIn('raw_content',exact[0])


if __name__=='__main__':unittest.main()
