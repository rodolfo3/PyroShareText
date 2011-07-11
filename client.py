'''
A client
'''

# client x server
import Pyro4

# gui
import gtk, gtk.glade

# log
import logging
import sys
LOG = logging.Logger(name="server")
## LOG.level = logging.CRITICAL # omit debug()


class LockDenied(Exception):
    pass


class ClientGui(object):
    '''
    GUI part
    '''
    GLADE_FILE = 'interface.glade'

    def __init__(self):
        gui = gtk.glade.XML(self.GLADE_FILE)
        window = gui.get_widget("MainWindow")
        window.connect("destroy", self.quit)
        text_box = gui.get_widget("TextBox")

        window.show()

        text_box.connect('key-press-event', self.key_press)
        text_box.connect('key-release-event', self.key_release)
        text_box.connect('move-cursor', self.move_cursor)

        self._text_box = text_box

    def move_cursor(self, widget, event, direction, shift):
        '''
        Unlock when change line
        '''
        if event.value_name == 'GTK_MOVEMENT_DISPLAY_LINES':
            self.change_row()

    def _event_key_abort(self, event):
        event.keyval = 0

    def _get_cursor_row(self, widget):
        '''
        Get the line where the cursor is
        '''
        buff = widget.get_buffer()
        cursor_pos = buff.get_property('cursor-position')
        # interval between the beggining and the actual position
        initial = buff.get_iter_at_line(0)
        final = buff.get_iter_at_offset(char_offset=cursor_pos)
        text = buff.get_text(initial, final)
        # count the number of linebreaks
        return text.count('\n')

    def key_press(self, widget, event):
        line = self._get_cursor_row(widget)
        # just ASCII
        if event.keyval >= 32 and event.keyval <= 128 and \
                not self.typing(line):
            self._event_key_abort(event)

    def key_release(self, widget, event):
        pass # to overwrite

    def quit(self, window):
        gtk.main_quit(window)

    def run(self):
        gtk.main()

from threading import Timer
from threading import Thread

class Client(ClientGui):
    '''
    Client x Server methods
    '''
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 4567

    def __init__(self):
        server = Pyro4.Proxy('PYRO:documents.server@%(host)s:%(port)i' % {
                'host': self.SERVER_HOST,
                'port': self.SERVER_PORT,
            })
        self._uid = server.register_client()
        self._server = server
        self._opened_document = None
        self._timer = None

        self._edit_line = None
        super(Client, self).__init__()

    def _get_buffer(self):
        return self._text_box.get_buffer()

    def _get_text(self, line):
        buff = self._get_buffer()
        initial = buff.get_iter_at_line(line)
        if line+1 >= buff.get_line_count():
            final = buff.get_end_iter()
        else:
            final = buff.get_iter_at_line(line+1)
        return buff.get_text(initial, final)

    def _timer_update_row(self, line):
        LOG.debug('Waiting to send row %i to server...' % line)
        if self._timer:
            self._timer.cancel()
        timer = Timer(interval=1, function=self.update_row, args=[line])
        timer.start()
        self._timer = timer

    def new_document(self):
        '''
        Create a new document in the server
        '''
        server = self._server
        document_uid = server.new_document(self._uid)
        self._opened_document = document_uid

    def open_document(self, document_uid):
        '''
        Create a new document in the server
        '''
        server = self._server
        document_uid = server.open_document(self._uid, document_uid)
        self._opened_document = document_uid

        # load document content
        buff = self._get_buffer()
        all_text = []
        for i in xrange(server.get_document_row_count(self._uid, document_uid)):
            text = \
                server.get_document_row(self._uid, self._opened_document, i)
            all_text.append(text)
        buff.set_text('\n'.join(all_text))

    def typing(self, line):
        '''
        Verify if user can edit current line in the buffer
        Create a lock if user can edit
        '''
        server = self._server
        lock = server.lock_document(self._uid, self._opened_document, line)
        if lock:
            self._edit_line = line
        else:
            LOG.debug('Unable to get a lock into line %i' % line)
        return lock

    def update_row(self, line):
        '''
        Update a line into a server
        '''
        LOG.debug('Sending row %i to server...' % line)
        server = self._server
        text = self._get_text(line)
        LOG.debug(repr(text))
        doc_id = server.write_document(self._uid, self._opened_document, line, \
            text)
        self._edit_line = None

    def release_lock(self, line):
        '''
        Release lock into the server
        '''
        LOG.debug('Sending unlock row %i to server...' % line)
        server = self._server
        server.unlock_document(self._uid, self._opened_document, line)

    def close_document(self):
        '''
        Flush document and release internal refs
        '''
        if self._edit_line:
            self.update_row(self._edit_line)

        if self._timer:
            timer = self._timer
            timer.cancel()

        self._server.close_document(self._uid, self._opened_document)
        self._opened_document = None

    def key_release(self, widget, event):
        '''
        Wait same seconds and update!
        '''
        super(Client, self).key_release(widget, event)
        line = self._get_cursor_row(widget)

        if gtk.gdk.keyval_name(event.keyval) == 'Return':
            # if create a new line, update a line immediatly and release a lock
            self.update_row(line-1)
            self.release_lock(line-1)
        elif event.keyval >= 32 and event.keyval <= 128: # just ASCII
            if self._edit_line:
                self._timer_update_row(line)
        else:
            pass
            # do not send "ivisible" keys

    def change_row(self):
        line = self._edit_line
        if line:
            self.update_row(line)
            self.release_lock(line)

    def quit(self, *args):
        if self._opened_document:
            self.close_document()
        super(Client, self).quit(*args)

if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    LOG.addHandler(logging.StreamHandler(sys.stdout))

    client = Client()
    if args and args[0]:
        doc_id = args[0].strip()
        client.open_document(doc_id)
    else:
        client.new_document()
    client.run()
else:
     LOG.addHandler(logging.NullHandler()) # run tests
