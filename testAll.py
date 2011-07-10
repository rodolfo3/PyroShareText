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
        '''
        Create a new document
        '''
        server = self.server
        client0 = self.client0
        document0 = server.new_document(client0)
        self.assertTrue(document0 in server._documents)

    def test_open_document(self):
        '''
        Open a document
        '''
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
        '''
        Open a inexistent document
        '''
        server = self.server
        client0 = self.client0
        client1 = self.client1
        document0 = 'D_invalid'
        try:
            document1 = server.open_document(client1, document0)
            self.failIf(True)
        except Document.DoesNotExist:
            pass

    def test_document_write(self):
        '''
        Write in a document using the server interface
        '''
        server = self.server
        client0 = self.client0
        document0 = server.new_document(client0)
        server.write_document(client0, document0, 0, 'row 000\nrow 001')

class TestDocument(unittest.TestCase):
    '''
    Test document internal methods
    '''
    def setUp(self):
        server = Server()
        self.client0 = server.register_client()
        self.client1 = server.register_client()
        self.document = Document('uid')

    def test_write(self):
        '''
        Write into a document
        '''
        client0 = self.client0
        document = self.document
        document.write(row=0, text='row 000\nrow 001')
        self.assertEqual(document.rows, ['row 000', 'row 001'])

    def test_second_write(self):
        '''
        2 sequencial writes
        '''
        client0 = self.client0
        document = self.document
        document.rows = ['row 000', 'row 001']
        document.write(row=2, text='row 002\nrow 003')
        self.assertEqual(document.rows,
            ['row 000', 'row 001', 'row 002', 'row 003'])

    def test_write_replace(self):
        '''
        Overwrite 1 line
        '''
        client0 = self.client0
        document = self.document
        document.rows = ['row 000', 'row 001']

        document.write(row=0, text='r0')
        self.assertEqual(document.rows, ['r0', 'row 001'])

    def test_write_addline(self):
        '''
        Write 2 lines, adding a new paragraph
        '''
        client0 = self.client0
        document = self.document
        document.rows = ['r0', 'r1', 'r4', 'r4']

        document.write(row=2, text='r2\nr3')
        self.assertEqual(document.rows, ['r0', 'r1', 'r2', 'r3', 'r4'])


    def test_lock_write(self):
        '''
        When write more than 1 line in the middle of the document, the locks
        in botton of the new paragraphs need to be moved
        '''
        client0 = self.client0
        client1 = self.client1
        document = self.document
        document.rows = ['r0', 'r1', 'r4', 'r4']

        document.lock(client0, 3)
        document.write(row=2, text='r2\nr3')

        # 1 line changed, 1 line added = +1 in the lock line
        try:
            document.lock(client1, 4)
            self.failIf(True)
        except Document.LockDenied:
            pass # ok


class TestDocumentEdit(unittest.TestCase):
    '''
    Test document's editor methods
    '''

    def setUp(self):
        server = Server()
        server = server
        client0 = server.register_client()
        client1 = server.register_client()

        # document with 2 lines
        document0 = server.new_document(client0)
        server.write_document(client0, document0, 0, 'row 000\nrow 001')

        server.open_document(client1, document0)

        self.server = server
        self.client0 = client0
        self.client1 = client1
        self.document = document0

    def test_edit_different_paragraphs(self):
        '''
        Lock different paragraphs to update, by 2 different users
        '''
        server = self.server
        client0 = self.client0
        client1 = self.client1
        document0 = self.document

        server.lock_document(client0, document0, 0) # lock document0, row 0
        server.lock_document(client0, document0, 1) # lock document0, row 1

        server.write_document(client0, document0, 0, 'changed row 0')
        server.write_document(client1, document0, 1, 'changed row 1')

        # write clear the lock, let's check
        server.lock_document(client0, document0, 1) # ok, no exception

    def test_edit_same_paragraph(self):
        '''
        2 users try to edit the same paragraph, at same time
        '''
        server = self.server
        client0 = self.client0
        client1 = self.client1
        document0 = self.document

        server.lock_document(client0, document0, 0) # lock document0, row 0
        self.failIf(
            # lock document0, row 0
            server.lock_document(client1, document0, 0)
        )

    def test_edit_same_paragraph_same_user(self):
        '''
        1 users try to get 2x the same paragraph
        '''
        server = self.server
        client0 = self.client0
        document0 = self.document

        server.lock_document(client0, document0, 0) # lock document0, row 0
        self.assertTrue(
            # lock document0, row 0
            server.lock_document(client0, document0, 0)
        )

if __name__ == '__main__':
    unittest.main()
