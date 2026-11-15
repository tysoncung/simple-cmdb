"""Regression coverage for application URL fields through the public API."""
import csv
import importlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ApplicationURLTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        env = patch.dict(os.environ, {'CMDB_DB': str(Path(directory.name) / 'test.db')})
        env.start()
        self.addCleanup(env.stop)
        module = importlib.import_module('app')
        module.DB_PATH = os.environ['CMDB_DB']
        module.init_db()
        self.client = module.app.test_client()

    def create(self, **fields):
        response = self.client.post('/api/application/add', json={
            'name': 'example', 'owner': 'platform', 'version': '1.0', **fields,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])
        return response.get_json()['application_id']

    def application(self):
        response = self.client.get('/api/export/applications')
        self.assertEqual(response.status_code, 200)
        return list(csv.DictReader(io.StringIO(response.get_data(as_text=True))))[0]

    def update(self, application_id, fields):
        response = self.client.put(f'/api/application/{application_id}', json=fields)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])

    def test_create_with_urls(self):
        self.create(repository_url='https://github.com/example/project',
                    documentation_url='https://example.org/docs')
        row = self.application()
        self.assertEqual(row['repository_url'], 'https://github.com/example/project')
        self.assertEqual(row['documentation_url'], 'https://example.org/docs')

    def test_create_without_urls_and_add_later(self):
        application_id = self.create()
        self.assertEqual(self.application()['repository_url'], '')
        self.assertEqual(self.application()['documentation_url'], '')
        self.update(application_id, {'repository_url': 'https://example.org/repo',
                                     'documentation_url': 'https://example.org/docs'})
        self.assertEqual(self.application()['repository_url'], 'https://example.org/repo')
        self.assertEqual(self.application()['documentation_url'], 'https://example.org/docs')

    def test_partial_updates_preserve_omitted_fields(self):
        application_id = self.create(repository_url='https://example.org/repo',
                                     documentation_url='https://example.org/docs')
        self.update(application_id, {'repository_url': 'https://example.org/new-repo'})
        self.assertEqual(self.application()['documentation_url'], 'https://example.org/docs')
        self.update(application_id, {'documentation_url': 'https://example.org/new-docs'})
        self.assertEqual(self.application()['repository_url'], 'https://example.org/new-repo')
        self.update(application_id, {'notes': 'Updated independently'})
        row = self.application()
        self.assertEqual(row['documentation_url'], 'https://example.org/new-docs')
        self.assertEqual(row['repository_url'], 'https://example.org/new-repo')
        self.assertEqual(row['owner'], 'platform')
        self.assertEqual(row['version'], '1.0')

    def test_explicit_null_clears_only_selected_url(self):
        application_id = self.create(repository_url='https://example.org/repo',
                                     documentation_url='https://example.org/docs')
        self.update(application_id, {'repository_url': None})
        self.assertEqual(self.application()['repository_url'], '')
        self.assertEqual(self.application()['documentation_url'], 'https://example.org/docs')
        self.update(application_id, {'documentation_url': None})
        self.assertEqual(self.application()['documentation_url'], '')


if __name__ == '__main__':
    unittest.main()
