import importlib
import sys
from starlette.testclient import TestClient
import pytest

class FakeCategory:
    def __init__(self, name):
        self.name = name

class FakePage:
    def __init__(self, title, text='text', exists=True):
        self.title = title
        self._text = text
        self.exists = exists
        self.namespace = 0
        self.length = len(text)
        self.protection = {}
        self._categories = [FakeCategory('Category')]
        self._revisions = [
            {'revid': 1, 'user': 'u1', 'timestamp': 't1', 'comment': 'c1'},
            {'revid': 2, 'user': 'u2', 'timestamp': 't2', 'comment': 'c2'},
        ]
        self.saved = []

    def text(self):
        return self._text

    def categories(self):
        return self._categories

    def revisions(self, limit=None):
        for r in self._revisions[:limit]:
            yield r

    def save(self, text, summary):
        self.saved.append((text, summary))
        self._text = text

class FakeSite:
    def __init__(self):
        class PageDict(dict):
            def __missing__(self, key):
                return FakePage(key, exists=False)

        self.pages = PageDict({'Existing': FakePage('Existing')})
        self.search_queries = []
        self.site_info = {'generator': 'FakeWiki 1.0'}

    def search(self, query, limit=5):
        self.search_queries.append((query, limit))
        return [
            {'title': 'Page1', 'snippet': 'Snippet1'},
            {'title': 'Page2', 'snippet': 'Snippet2'},
        ][:limit]

@pytest.fixture
def server(monkeypatch):
    fake_site = FakeSite()
    monkeypatch.setattr('mwclient.Site', lambda *a, **k: fake_site)
    if 'mcp_mediawiki' in sys.modules:
        del sys.modules['mcp_mediawiki']
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    module = importlib.import_module('mcp_mediawiki')
    module.site = fake_site
    return module

def test_root_endpoint(server):
    with TestClient(server.app) as client:
        res = client.get('/')
        assert res.status_code == 200
        assert res.json()['status'] == 'ok'


def test_get_page_success(server):
    result = server.get_page('Existing')
    assert result['name'] == 'Existing'
    assert result['metadata']['namespace'] == 0


def test_get_page_not_found(server):
    result = server.get_page('Missing')
    assert 'error' in result


def test_update_page_dry_run(server):
    result = server.update_page('Existing', 'new', 's', dry_run=True)
    assert result['status'] == 'dry-run'


def test_update_page_save(server):
    result = server.update_page('Existing', 'updated', 'sum')
    assert result['status'] == 'success'
    page = server.site.pages['Existing']
    assert page.saved and page.saved[-1] == ('updated', 'sum')


def test_search_pages(server):
    results = server.search_pages('abc')
    assert len(results) == 2
    assert results[0]['title'] == 'Page1'


def test_server_status(server):
    status = server.server_status()
    assert status['mediawiki_version'] == 'FakeWiki 1.0'


def test_get_page_history(server):
    history = server.get_page_history('Existing', limit=1)
    assert len(history) == 1
    assert history[0]['revid'] == 1
