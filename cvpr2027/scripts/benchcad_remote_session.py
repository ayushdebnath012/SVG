"""Password-free-on-disk SSH transport; authenticate interactively once per session."""
import argparse
import getpass
import json
import sys
import termios
import paramiko


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--host',required=True)
    p.add_argument('--user',required=True)
    a=p.parse_args()
    password=getpass.getpass('SSH password: ')
    c=paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(a.host,username=a.user,password=password,timeout=15,banner_timeout=15,auth_timeout=15,look_for_keys=False,allow_agent=False)
    del password
    # macOS canonical PTYs can truncate long JSON lines. Read raw transport
    # bytes after authentication; also keep routine command bodies out of echo.
    if sys.stdin.isatty():
        settings=termios.tcgetattr(sys.stdin.fileno())
        settings[3] &= ~(termios.ICANON | termios.ECHO)
        settings[6][termios.VMIN]=1
        settings[6][termios.VTIME]=0
        termios.tcsetattr(sys.stdin.fileno(),termios.TCSANOW,settings)
    print('Authenticated; ready for JSON transport operations.',flush=True)
    try:
        for line in sys.stdin:
            try:
                op=json.loads(line)
                if op['action']=='close':break
                if op['action']=='run':
                    _,o,e=c.exec_command(op['command'],timeout=op.get('timeout',45))
                    stdout=o.read().decode();stderr=e.read().decode();status=o.channel.recv_exit_status()
                    print(json.dumps(dict(exit_code=status,stdout=stdout,stderr=stderr)),flush=True)
                elif op['action'] in ('put','get'):
                    with c.open_sftp() as s:
                        if op['action']=='put':s.put(op['local'],op['remote'])
                        else:s.get(op['remote'],op['local'])
                    print(json.dumps(dict(status='ok',action=op['action'])),flush=True)
                else:raise ValueError('Unknown transport action')
            except Exception as e:print(json.dumps(dict(error=type(e).__name__+': '+str(e))),flush=True)
    finally:c.close()


if __name__=='__main__':main()
