import datetime
import os
import requests
#import telnetlib
import urllib.parse
import time
import webbrowser


class Kontrol:
    def __init__(self, ip, port, user, password, telnet_conn):
        self.ipaddr = ip
        self.port = port
        self.user = user
        self.password = password
        self.tn = telnet_conn

        self.wait=0.1
        self.connection_timeout = 10
        self.urls = dict()
        self.seqs = dict()
        self.var = 250
        self.eol = b"\r"

        # throttle (0 is off)
        # rudder (1..127) ; 64 middle ; < 64 == LEFT ; > 64 == RIGTH
        # elevation (1..127) ; 64 middle ; < 64 BACK ; > 80 FRONT
        # aileron (1..127), 64 middle ; < 64 == LEFT ; > 64 == RIGTH
        # settings (speed mode, inverted flying)
        self.state = {'time': self.wait, 'throttle': 0, 'rudder': 1, 'elevation': 1, 'aileron': 1, 'settings': 0}

    def opentelnet(self):
        print('url_for', self.url_for('set_params.cgi'))
        res = requests.get(
            self.url_for('set_params.cgi'),
            params=dict(telnetd=1, save=1, reboot=1, **self.auth_params())
        )
        print('-- res', res)

    def init_telnet_connection(self):
        # Will Authentication Option ; IAC + WILL + AUTHENTICATION
        # Do Suppress Go Ahead ; IAC + DO + SGA
        # Will Terminal Type ; IAC + WILL + TTYPE
        # Will Negotiate About Window Size ; IAC + WILL + NAWS
        # Will Terminal Speed ; IAC + WILL + TSPEED
        # Will Remote Flow Control ; IAC + WILL + LFLOW
        # Will Linemode ; IAC + WILL + LINEMODE
        # Will New Environment Option ; IAC + WILL + NEW_ENVIRON
        # Do Status ; IAC + DO + STATUS
        # Will X Display Location ; IAC + WILL + XDISPLOC
        self.tn.sock.send(b"\xff\xfb\x25")
        self.tn.sock.send(b"\xff\xfd\x03")
        self.tn.sock.send(b"\xff\xfb\x18")
        self.tn.sock.send(b"\xff\xfb\x1f")
        self.tn.sock.send(b"\xff\xfb\x20")
        self.tn.sock.send(b"\xff\xfb\x21")
        self.tn.sock.send(b"\xff\xfb\x22")
        self.tn.sock.send(b"\xff\xfb\x27")
        self.tn.sock.send(b"\xff\xfd\x05")
        self.tn.sock.sendall(b"\xff\xfb\x23")

        # Won't Echo ; IAC + WONT + ECHO
        # Suboption Negotiate About Window Size ; IAC + SB + NAWS
        # Suboption End ; IAC + SE
        # Do Echo ; IAC + DO + ECHO

        self.tn.sock.send(b"\xff\xfc\x01")
        self.tn.sock.send(b"\xff\xfa\x1f\x00\xa7\x00\x1f")
        self.tn.sock.send(b"\xff\xf0")
        self.tn.sock.sendall(b"\xff\xfd\x01")

        time.sleep(self.wait)

    def set_state(self, argdict):
        for k,v in argdict.items():
            self.state[k] = v
        if not 'var' in self.state.keys():
            self.state['var'] = self.var
        print(self.state)

    def checksum(self, values=None):
        if not values:
            values = [self.state['throttle'],self.state['rudder'],
                        self.state['elevation'],self.state['aileron'],
                        self.state['settings']]
        xor = 0
        i = 0
        while i < len(values):
            xor = xor ^ values[i]
            i += 1
        return xor

    def get_comm(self):
        abytes = bytes([
            self.state['var'],
            self.state['throttle'],
            self.state['rudder'],
            self.state['elevation'],
            self.state['aileron'],
            self.state['settings'],
            self.checksum()
        ])
        return abytes

    def send_comm(self):
        mess = str(self.get_comm())[2:-1]
        allm = 'echo -e "' + mess + '" > /dev/ttyAMA1'
        allm = allm.encode('ascii') + self.eol
        print('--allm', allm)

        self.tn.sock.send(allm)

        # self.tn.sock.sendall(b"\n")

        #print('-- sleep', self.state['time'])
        time.sleep(self.state['time'])
        print('-- read_very_eager', self.tn.read_very_eager())

        #print('-- sleep', self.state['time'])
        #print('-- expect', self.tn.expect(['ttyAMA1\r\n#'.encode('ascii')], self.state['time']))

        #print('-- read_until', self.tn.read_until('ttyAMA1\r\n#'.encode('ascii'), self.state['time']))

        '''self.tn.sock.sendall(b"\xff\xfc\x01")
        self.tn.sock.sendall(b"\xff\xfa\x1f\x00\xa7\x00\x1f")
        self.tn.sock.sendall(b"\xff\xf0")
        self.tn.sock.sendall(b"\xff\xfd\x01")
        '''

    def seq_store(self, seqname, index=0):
        self.seqs[seqname] ={}
        self.seqs[seqname][index] = self.state
        return

    def seq_get(self, seqname):
        if seqname in self.seqs:
            return self.seqs[seqname]
        return bytes([[0xfa, 0x40, 0x40, 0x40, 0x00, 0x00]])

    def seq_do(self, seqname):
        seqs = self.seq_get(seqname)
        for seq in seqs:
            self.set_state(seqs[seq])
            self.send_comm()

    def get_state(self):
        return self.state

    def url_for(self, script):
        if script in self.urls:
            return self.urls[script]
        url = 'http://{addr}:{port}/{script}'.format(
            addr=self.ipaddr, port=self.port, script=script
        )
        self.urls[script] = url
        return url

    def download(self, output, path):
        if output is None:
            output = os.path.basename(path)
        res = requests.get(
            self.url_for('get_record.cgi'),
            params=dict(path=path, json=1, **auth_params()),
            stream=True
        )

        res.raise_for_status()

        with open(output, 'w') as fd:
            for chunk in res.iter_content(chunk_size=8192):
                fd.write(chunk)

    def auth_params(self):
        return {'user': self.user, 'pwd': self.password}

    def snapshot(self,output):
        if output is None:
            now = datetime.datetime.now()
            output = 'snapshot-{}.jpg'.format(now.isoformat())

        res = requests.get(
            self.url_for('snapshot.cgi'),
            params=dict(json=1, **self.auth_params())
        )  # , **auth_params()

        res.raise_for_status()

        with open(output, 'wb') as fd:
            fd.write(res.content)

    def get_params(self): # , output, patterns
        res = requests.get(self.url_for('get_params.cgi'),
                           params=dict(json=1, **self.auth_params()))

        res.raise_for_status()
        print(res.json())

    def get_status(self): # , output, patterns
        res = requests.get(self.url_for('get_status.cgi'),
                           params=dict(json=1, **self.auth_params()))
        res.raise_for_status()
        print(res.json())

    def get_properties(self): # , output, patterns
        res = requests.get(self.url_for('get_properties.cgi'),
                           params=dict(json=1, **self.auth_params()))
        res.raise_for_status()
        print(res.json())

    def streamurl(self):
        url = self.url_for('av.asf')
        page = '{}?{}'.format(
            url, urllib.parse.urlencode(self.auth_params()))
        print(page)
        #webbrowser.open(page)

    def close(self):
        print('-- close ---')
        self.tn.close()
