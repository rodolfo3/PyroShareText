'''
A server of pyto methods.
Sincronize texts between clients and avoid concurrency problems.
'''
HOST = '0.0.0.0'
PORT = 4567
VERBOSE = True

import uuid

class Lock:
    def __init__(self, client_uid):
        self._client_uid = client_uid

    def can_unlock(self, client_uid):
        return self._client_uid == client_uid

class Document:
    class DoesNotExist(Exception): # cannot find a document
        pass

    class LockDenied(Exception): # cannot get a lock
        pass

    def __init__(self, uid):
        self._uid = uid
        self.rows = []
        self._lock_rows = []

    def write(self, row, text):
        rows = text.strip().split('\n')
        lock_rows = [None] * len(rows) # new lines are unlocked

        # replace 1 line and add in the middle, if needed
        all_rows = self.rows
        self.rows = all_rows[:row] + rows + all_rows[row+1:]

        # do tha same to locks
        all_lock_rows = self._lock_rows
        self._lock_rows = \
            all_lock_rows[:row] + lock_rows + all_lock_rows[row+1:]

    def lock(self, client_uid, row):
        if self._lock_rows[row] is not None:
            raise self.LockDenied()
        self._lock_rows[row] = Lock(client_uid)

    def unlock(self, client_uid, row):
        if self._lock_rows[row] is None:
            # no lock?! ok, just write - no one care
            return True
        if not self._lock_rows[row].can_unlock(client_uid):
            assert False
        self._lock_rows[row] = None

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

    def _get_document(self, uid):
        if uid in self._documents:
            return self._documents[uid]
        raise Document.DoesNotExist()

    def new_document(self, client_uid):
        document_uid = u'D%s' % uuid.uuid4()
        self._documents[document_uid] = Document(document_uid)
        return document_uid

    def open_document(self, client_uid, document_uid):
        document = self._get_document(document_uid)
        return document_uid

    def write_document(self, client_uid, document_uid, row, text):
        document = self._get_document(document_uid)
        document.write(row, text)
        document.unlock(client_uid, row)
        return document_uid

    def lock_document(self, client_uid, document_uid, row):
        document = self._get_document(document_uid)
        document.lock(client_uid, row)


if __name__ == '__main__':
    import Pyro4
    daemon = Pyro4.Daemon(host=HOST, port=PORT)
    server = Server()
    Pyro4.Daemon.serveSimple({
            server: 'documents.server',
        }, daemon=daemon, ns=False, verbose=VERBOSE)

