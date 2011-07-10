'''
A server of pyto methods.
Sincronize texts between clients and avoid concurrency problems.
'''
HOST = '0.0.0.0'
PORT = 4567
VERBOSE = True

import uuid

class Document:
    class DoesNotExist(Exception):
        pass

    def __init__(self, uid):
        self._uid = uid

class Server(object):

    def __init__(self):
        self._documents = {}

    def register_client(self):
        '''
        First of all, every client need an identification.
        '''
        # TODO save client uid internaly
        client_uid = u'C%s' % uuid.uuid4()
        return client_uid

    def new_document(self, client_uid):
        document_uid = u'D%s' % uuid.uuid4()
        self._documents[document_uid] = Document(document_uid)
        return document_uid

    def open_document(self, client_uid, document_uid):
        if document_uid in self._documents:
            return document_uid
        raise Document.DoesNotExist()


if __name__ == '__main__':
    import Pyro4
    daemon = Pyro4.Daemon(host=HOST, port=PORT)
    server = Server()
    Pyro4.Daemon.serveSimple({
            server: 'documents.server',
        }, daemon=daemon, ns=False, verbose=VERBOSE)

