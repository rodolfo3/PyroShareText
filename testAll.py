import unittest
from server import Server

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

if __name__ == '__main__':
    unittest.main()
