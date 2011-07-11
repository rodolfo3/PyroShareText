'''
A server of pyto methods.
Sincronize texts between clients and avoid concurrency problems.
'''
HOST = '0.0.0.0'
PORT = 4567
VERBOSE = True

import uuid

# to LOG
import logging
import sys
LOG = logging.Logger(name="server")
## LOG.level = logging.CRITICAL # omit debug()

class Lock:
    def __init__(self, client_uid):
        self._client_uid = client_uid

    def can_unlock(self, client_uid):
        return self._client_uid == client_uid

class Document(object):
    PATH = '/tmp/docs'

    class DoesNotExist(Exception): # cannot find a document
        pass

    class LockDenied(Exception): # cannot get a lock
        pass

    def __init__(self, uid):
        self._uid = uid
        self._rows = ['']
        self._lock_rows = [None]

    def set_rows(self, rows):
        self._lock_rows = [None] * len(rows)
        self._rows = list(rows)

    def write_file(self):
        filename = '%s/%s' % (self.PATH, self._uid)
        file_ = file(filename, 'w')
        file_.write('\n'.join(self._rows))
        file_.close()

    def get_rows(self):
        return self._rows

    # property - just to external use
    rows = property(get_rows, set_rows)

    def write(self, row, text):
        LOG.debug('Writing line %i into %s...' % (
            row, self._uid))

        rows = text.strip().split('\n')
        lock_rows = [None] * (len(rows)-1) # new lines are unlocked

        # replace 1 line and add in the middle, if needed
        all_rows = self._rows
        print "***", all_rows
        self._rows = all_rows[:row] + rows + all_rows[row+1:]
        print '###', self._rows

        # do tha same to locks
        all_lock_rows = self._lock_rows
        self._lock_rows = \
            all_lock_rows[:row] + lock_rows + all_lock_rows[row:]

        LOG.debug('Writed!')

    def lock(self, client_uid, row):
        if len(self._lock_rows) <= row:
            # if create a new line, lock it
            self._lock_rows.append(None)

        if self._lock_rows[row] is not None and \
                not self._lock_rows[row].can_unlock(client_uid):
            LOG.debug("client %s try to replace a lock by %s" % (
                    client_uid, self._lock_rows[row]._client_uid,
                ))
            raise self.LockDenied()

        # update the lock
        if self._lock_rows[row]:
            LOG.debug('Update lock line %i from %s to %s' % (
                    row,
                    self._lock_rows[row]._client_uid,
                    client_uid,))
        else:
            LOG.debug('Lock line %i' % row)
        self._lock_rows[row] = Lock(client_uid)
        LOG.debug('Lock status from %s: %s' % (
            self._uid, self._lock_rows))

    def unlock(self, client_uid, row):
        if self._lock_rows[row] is None:
            # no lock?! ok, no one care
            LOG.warning('Unlocking a non-locked line: %s:%s' % (
                self._uid, row))
            return True
        if not self._lock_rows[row].can_unlock(client_uid):
            assert False
        self._lock_rows[row] = None

        LOG.debug('Lock status from %s: %s' % (
            self._uid, self._lock_rows))

    def unlock_all(self, client_uid):
        for row in xrange(len(self._lock_rows)):
            if self._lock_rows[row] and \
                    self._lock_rows[row].can_unlock(client_uid):
                self.unlock(client_uid, row)

    def is_locked_by(self, client_uid, row):
        if self._lock_rows[row] is None:
            return False
        return self._lock_rows[row]._client_uid == client_uid


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
        LOG.warning("Trying to open a nonexistent %s document (%s)" % (
                uid,
                self._documents.keys(),
            ))
        raise Document.DoesNotExist()

    def new_document(self, client_uid):
        document_uid = u'D%s' % uuid.uuid4()
        self._documents[document_uid] = Document(document_uid)
        LOG.debug("New document: %s (by %s)" % (
                document_uid,
                client_uid,
            ))
        LOG.debug('Document %s created!' % document_uid)
        return document_uid

    def open_document(self, client_uid, document_uid):
        LOG.debug('Client %s open document %s' % (
            client_uid, document_uid))
        document = self._get_document(document_uid)
        return document_uid

    def close_document(self, client_uid, document_uid):
        document = self._get_document(document_uid)
        document.write_file()
        document.unlock_all(client_uid)
        LOG.debug('Document %s closed' % document_uid)

    def unlock_document(self, client_uid, document_uid, row):
        LOG.debug('try unlock %s(%s) by %s' % (document_uid, row, client_uid))
        document = self._get_document(document_uid)
        try:
            document.unlock(client_uid, row)
            LOG.debug('unlocked')
        except Document.LockDenied:
            LOG.debug('unlock denied!')
            return False
        return False

    def lock_document(self, client_uid, document_uid, row):
        LOG.debug('try lock %s(%s) by %s' % (document_uid, row, client_uid))
        document = self._get_document(document_uid)
        try:
            document.lock(client_uid, row)
            LOG.debug('locked')
        except Document.LockDenied:
            LOG.debug('locked denied!')
            return False
        return True

    def write_document(self, client_uid, document_uid, row, text):
        LOG.debug('Writing %s by %s: %s' % (document_uid, client_uid, text))
        document = self._get_document(document_uid)
        document.write(row, text)
        return document_uid

    def get_document_row_count(self, client_uid, document_uid):
        LOG.debug('Client %s request %s row count' % (
            client_uid, document_uid))
        document = self._get_document(document_uid)
        total = len(document.rows)
        LOG.debug('Result: %i' % total)
        return total

    def get_document_row(self, client_uid, document_uid, row):
        LOG.debug('Client %s request %s %s row' % (
            client_uid, document_uid, row))
        document = self._get_document(document_uid)
        LOG.debug(repr(document.rows[row]))
        return document.rows[row]

    def list_changed_lines(self, client_uid, document_uid):
        ## LOG.debug("Client %s requested changes of %s" % (
        ##     client_uid, document_uid))
        document = self._get_document(document_uid)
        return [i for i in xrange(len(document.rows)) \
            if not document.is_locked_by(client_uid, i)]

if __name__ == '__main__':
    import Pyro4
    daemon = Pyro4.Daemon(host=HOST, port=PORT)
    server = Server()
    LOG.addHandler(logging.StreamHandler(sys.stdout))

    Pyro4.Daemon.serveSimple({
            server: 'documents.server',
        }, daemon=daemon, ns=False, verbose=VERBOSE)
else:
    LOG.addHandler(logging.NullHandler()) # run tests'
