'''
A client
'''

# client x server
import Pyro4

# gui
import gtk, gtk.glade

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
        window.connect("destroy", gtk.main_quit)
        text_box = gui.get_widget("TextBox")

        window.show()

        text_box.connect('key-press-event', self.key_press)
        text_box.connect('key-release-event', self.key_release)

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
        if not self.can_edit(line):
            self._event_key_abort(event)

    def key_release(self, widget, event):
        pass

    def run(self):
        gtk.main()

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
        super(Client, self).__init__()

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

    def close_document(self):
        '''
        Flush document and release internal refs
        '''
        self._opened_document = None

    def can_edit(self, line):
        server = self._server
        lock = server.lock_document(self._uid, self._opened_document, line)
        print lock
        return lock


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]

    client = Client()
    if args and args[0]:
        doc_id = args[0].strip()
        client.open_document(doc_id)
    else:
        client.new_document()
    client.run()
