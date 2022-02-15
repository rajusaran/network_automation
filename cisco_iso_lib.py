#Author Raju Saran
#
from cgi import print_directory
from distutils.log import error
from socket import timeout
import telnetlib
import time
import re
from pprint import pprint
import logging
import yaml

def to_bytes(line):
    return f"{line}\n".encode("utf-8")

def enable_prompt(tn,enable_password):
    logging.debug("in enable_prompt")
    #handle the enable prompt
    tn.write(b"enable\n")
    index, m, output = tn.expect([b"\w+#", b"Password"])
    if index == 0:
        return True
    elif index == 1:
        tn.write(enable_password.encode('ascii')  +b"\n")
        return True
    else:
        logging.CRITICAL("FAILED: Prompt didn't match after sending 'enable' command")
        return False

def telnet_login(host = None , port = None , username = '', password = '', enable_password ='', retry = 5):
    
    result = False
    if host is None:
        return False


    if port is not None:
        tn = telnetlib.Telnet(host, port)
    else: 
        tn = telnetlib.Telnet(host)
  
    #the loop is required if password was locked/ or if there is a delay to handle that.
    for iter in range(retry):
        logging.debug("This is the iteration : %d"%iter)

        # I have noticed that, If there is no password set and user access the device via console, Needs to hit enter key to see the prompt
        tn.write(b"\n\n")
        time.sleep(2)
        try:
            index,m, output = tn.expect([b">", b"#", b"Username:", b"Password", b"Connection refused"], timeout=20)
        except Exception as error:
            continue


        if index == 0:
            if not enable_prompt(tn,enable_password):
                continue
        elif index == 1:
            logging.debug("PASS:device login")

        elif index == 2:
            tn.write(to_bytes(username))
            tn.read_until(b"Password")
            tn.write(to_bytes(password))

            #Check if user has set the enable password.
            try:
                enable_index,m, output = tn.expect([b">", b"#"], timeout=10)
            except Exception as error:
                print("FAILED: pattern match failed after login")
                print(tn.read_very_eager())
            
            if enable_index == 0:
                result = enable_prompt(tn,enable_password)
                return tn, result
            elif enable_index == 1:
                print("PASS: Login successful!")
                return tn, True
            else:
                break

            
        elif index == 4:
            logging.CRITICAL("FAILED: 'Connection refused' Clear the line ")

        else:
            logging.CRITICAL("FAILED: Pattern didn't match ")
            print(tn.read_very_eager())

    else:
        return tn, result

    return tn, result


def show_version(dev):
    dev.write(to_bytes("show version | in Soft"))
    time.sleep(2)
    out = (dev.read_very_eager().decode('ascii'))
    print(out)
    m = re.search('Cisco\s+IOS\s+Software.*Version\s(.*)', out)
    print('\n Device version {}'.format(m.group(1)))
    return m.group(1).rstrip()


def get_device_list(file):
    TestbedInfo=yaml.safe_load(open(file))
    devNameList = []
    hostList = []
    # Find the list of devices to clean
    for item in TestbedInfo['devices'].keys():
        # Fetch only the EDGENODE device roles
        if TestbedInfo['devices'][item]['role'] == "EDGENODE" or TestbedInfo['devices'][item]['role'] == "EWLC" or TestbedInfo['devices'][item]['role'] == "BORDERNODE,EXTERNAL":
            devNameList.append(item)
            ip = TestbedInfo['devices'][item]['connections']['a']['ip']
            port = str(TestbedInfo['devices'][item]['connections']['a']['port'])
            telentString = ip + " " +  port
            print(telentString)
            hostList.append(telentString)
    print(devNameList)
    print(hostList)

    return TestbedInfo, devNameList, hostList


def set_up_device(dev):
    #Set the ter len 
    dev.write("terminal length 0".encode('ascii') +b"\n")
    dev.write(to_bytes("show clock"))
    dev.write("show inv".encode('ascii') +b"\n")
    time.sleep(5)
    print(dev.read_very_eager().decode('ascii'))
    
             


