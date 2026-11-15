"""Service version API and populated-database migration regression tests."""
import csv
import importlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ServiceVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        env = patch.dict(os.environ, {'CMDB_DB': str(Path(self.temp.name) / 'test.db')})
        env.start()
        self.addCleanup(env.stop)
        self.module = importlib.import_module('app')
        self.module.DB_PATH = os.environ['CMDB_DB']
        self.module.init_db()
        self.client = self.module.app.test_client()
        with self.module.get_db() as db:
            self.server_id = db.execute("INSERT INTO servers (hostname) VALUES ('test')").lastrowid
            self.app_id = db.execute("INSERT INTO applications (name, version) VALUES ('product', 'legacy')").lastrowid

    def create(self, **extra):
        response = self.client.post('/api/service/add', json={
            'server_id': self.server_id, 'application_id': self.app_id,
            'service_name': 'example', **extra,
        })
        self.assertEqual(response.status_code, 200)
        return response.get_json()['service_id']

    def rows(self):
        response = self.client.get('/api/export/services')
        self.assertEqual(response.status_code, 200)
        return list(csv.DictReader(io.StringIO(response.get_data(as_text=True))))

    def test_independent_versions_and_detail(self):
        first = self.create(version='1.0')
        self.create(version='2.0')
        self.create()
        self.assertEqual([r['version'] for r in self.rows()], ['1.0', '2.0', ''])
        response = self.client.get(f'/service/{first}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'1.0', response.data)
        with self.module.get_db() as db:
            self.assertEqual(db.execute('SELECT version FROM applications').fetchone()[0], 'legacy')

    def test_partial_update_and_clear(self):
        service_id = self.create(version='1.0')
        for payload, expected in [({'status': 'stopped'}, '1.0'),
                                  ({'version': '2.0'}, '2.0'),
                                  ({'version': None}, '')]:
            response = self.client.put(f'/api/service/{service_id}', json=payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.rows()[0]['version'], expected)
            self.assertEqual(self.rows()[0]['status'], 'stopped')

    def test_populated_legacy_database_upgrade_is_repeatable(self):
        first = self.create()
        second = self.create()
        with self.module.get_db() as db:
            edge = db.execute('INSERT INTO dependencies (source_service_id, target_service_id) VALUES (?, ?)', (first, second)).lastrowid
            db.execute('ALTER TABLE services DROP COLUMN version')
        self.module.init_db()
        self.module.init_db()
        with self.module.get_db() as db:
            rows = db.execute('SELECT id, application_id, version FROM services ORDER BY id').fetchall()
            self.assertEqual([tuple(r) for r in rows], [(first, self.app_id, None), (second, self.app_id, None)])
            relationship = db.execute('SELECT source_service_id, target_service_id FROM dependencies WHERE id = ?', (edge,)).fetchone()
            self.assertEqual(tuple(relationship), (first, second))
        self.assertEqual(self.client.put(f'/api/service/{first}', json={'version': '3.0'}).status_code, 200)
        self.assertEqual(self.rows()[0]['version'], '3.0')


if __name__ == '__main__':
    unittest.main()
