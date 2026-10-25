import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from marketmix.server import Handler


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def test_report_and_interface(self):
        with urllib.request.urlopen(self.base+'/api/report') as response:
            data=json.load(response);self.assertEqual(data['weeks'],130)
        with urllib.request.urlopen(self.base) as response:
            self.assertIn(b'Planning controls',response.read())

    def test_plan_endpoint_reconciles(self):
        request=urllib.request.Request(self.base+'/api/plan',data=b'{"budget":16000,"movement":0.2}',headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request) as response:
            data=json.load(response);self.assertAlmostEqual(data['plan']['allocated'],16000,places=2)

    def test_cross_origin_request_rejected(self):
        request=urllib.request.Request(self.base+'/api/plan',data=b'{}',headers={'Content-Type':'application/json','Origin':'https://example.com'})
        with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(request)
        self.assertEqual(error.exception.code,403)

    def test_bad_and_nonfinite_budgets_rejected(self):
        for value in ['NaN','-1','"bad"']:
            request=urllib.request.Request(self.base+'/api/plan',data=('{"budget":'+value+'}').encode(),headers={'Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(request)
            self.assertEqual(error.exception.code,400)
