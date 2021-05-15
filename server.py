
# pip3 install cherrypy
# pip3 install pishiftpy

import cherrypy
import PiShiftPy as shift
from cherrypy.lib import auth_basic

USERS = {'hello': 'world'}

def validate_password(realm, username, password):
    if username in USERS and USERS[username] == password:
        return True
    return False

class RelayControl(object):

    relay_state = 0

    def __init__(self):
        shift.init(17, 27, 22, 1) # data, clock, latch, count of shift registers

    def get_pin_mask(self, pin):
        return 0x1 << (int(pin) - 1)

    def set_pin_state(self, pin, state):
        """
        Parameters
        ----------
        pin : int
            Number of the pin to toggle, between 1 and 8
        state : bool
            Determines if the relay should be closed (they're all "normally open" by default)
        """
        mask = self.get_pin_mask(pin)
        if (state == 0):
            self.relay_state = self.relay_state & ~mask
        else:
            self.relay_state = self.relay_state | mask
        shift.write(self.relay_state)
    
    def get_pin_state(self, pin):
        mask = self.get_pin_mask(pin)
        pin_state = (self.relay_state & mask) >> int(pin) - 1
        return pin_state

    def toggle_pin_state(self, pin):
        """
        Parameters
        ----------
        pin : int
            Number of the pin to toggle, between 1 and 8
        """
        mask = self.get_pin_mask(pin)
        self.relay_state = self.relay_state ^ mask
        shift.write(self.relay_state)

    def clear_all_pins(self):
        self.relay_state = 0
        shift.write(self.relay_state)
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def set(self, pin, on=False):
        self.set_pin_state(pin, on)
        return { "result": "ok", "new_state": self.get_pin_state(pin) }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def toggle(self, pin):
        self.toggle_pin_state(pin)
        return { "result": "ok", "new_state": self.get_pin_state(pin) }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def clear(self):
        self.clear_all_pins()
        return { "result": "ok" }
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def state(self, pin):
        return { "result": "ok", "current_state": self.get_pin_state(pin) }

if __name__ == '__main__':
    conf = {
        'global': {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 8080,
        },
        '/': {
            'tools.auth_basic.on': True,
            'tools.auth_basic.realm': 'localhost',
            'tools.auth_basic.checkpassword': validate_password
        }
    }
    cherrypy.quickstart(RelayControl(), '/', conf)
    
