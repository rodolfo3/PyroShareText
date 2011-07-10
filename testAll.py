import unittest
from server import Server, Document

class TestServerClient(unittest.TestCase):
    '''
    Test client's related server functions
    '''
    def setUp(self):
        self.server = Server()

    def test_new_client(self):
        '''
        Test to generate diferent id to clients
        '''
        server = self.server
        client0 = server.register_client()
        client1 = server.register_client()

        self.failIf(client0 == client1)

class TestServerDocument(unittest.TestCase):
    '''
    Test documents' related server functions
    '''
    def setUp(self):
        server = Server()
        self.server = server
        self.client0 = server.register_client()
        self.client1 = server.register_client()

    def test_new_document(self):
        server = self.server
        client0 = self.client0
        document0 = server.new_document(client0)
        self.assertTrue(document0 in server._documents)

    def test_open_document(self):
        server = self.server
        client0 = self.client0
        client1 = self.client1
        document0 = server.new_document(client0)
        document1 = server.open_document(client1, document0)
        # opened same document
        self.assertEqual(document0, document1)
        # and do not create a new document
        self.assertEqual(len(server._documents.keys()), 1)

    def test_open_document_error(self):
        server = self.server
        client0 = self.client0
        client1 = self.client1
        document0 = 'D_invalid'
        try:
            document1 = server.open_document(client1, document0)
            self.failIf(True)
        except Document.DoesNotExist:
            pass

if __name__ == '__main__':
    unittest.main()
