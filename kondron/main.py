import time
import telnetlib
from telnetlib import Telnet
from kondron.kondron import Kontrol


def main():
    with Telnet('192.168.1.1') as tn:
        myKontrol = Kontrol('192.168.1.1', 80, 'admin', '', tn)
        myKontrol.init_telnet_connection()

        # "\xfa\x40\x40\x40\x40\x00\x00"

        sleep = 0.3

        myKontrol.set_state({'throttle': 200, 'rudder': 64, 'elevation': 64, 'aileron': 64, 'time': sleep})
        myKontrol.send_comm()

        myKontrol.set_state({'throttle': 180, 'rudder': 64, 'elevation': 64, 'aileron': 64, 'time': sleep})
        myKontrol.send_comm()

        myKontrol.set_state({'throttle': 180, 'rudder': 64, 'elevation': 64, 'aileron': 64, 'time': sleep})
        myKontrol.send_comm()

        myKontrol.set_state({'throttle': 64, 'rudder': 64, 'elevation': 64, 'aileron': 64, 'time': sleep})
        myKontrol.send_comm()
        myKontrol.send_comm()


        time.sleep(8)


        #myKontrol.close()


        #myKontrol.url_for('get_record.cgi')
        #myKontrol.snapshot(None)
        #myKontrol.streamurl()
        #myKontrol.seq_store('seqName',1)
        #myKontrol.seq_get('seqName')
        #myKontrol.seq_do('seqName')


def trial():
    eof = b"\n"

    with Telnet('192.168.1.1') as tn:
        #tn.set_debuglevel(5)
        tn.sock.send(b"\xff\xfb\x25")
        tn.sock.send(b"\xff\xfd\x03")
        tn.sock.send(b"\xff\xfb\x18")
        tn.sock.send(b"\xff\xfb\x1f")
        tn.sock.send(b"\xff\xfb\x20")
        tn.sock.send(b"\xff\xfb\x21")
        tn.sock.send(b"\xff\xfb\x22")
        tn.sock.send(b"\xff\xfb\x27")
        tn.sock.send(b"\xff\xfd\x05")
        tn.sock.sendall(b"\xff\xfb\x23")

        tn.sock.send(b"\xff\xfc\x01")
        tn.sock.send(b"\xff\xfa\x1f\x00\xa7\x00\x1f")
        tn.sock.send(b"\xff\xf0")
        tn.sock.sendall(b"\xff\xfd\x01")

        time.sleep(0.1)

        allm = 'echo -e "\\xfa\\x40\\x40\\x40\\x40\\x00\\x00" >/dev/ttyAMA1'
        allm = allm.encode('ascii')

        tn.sock.send(allm)
        tn.sock.sendall(b"\n")

        time.sleep(0.1)

        def callb(socket, command, option):
            print(socket, command, option)
            tn.write(allm)
            tn.write(b"\r")

        tn.set_option_negotiation_callback(callb)


if __name__ == '__main__':
    main()
