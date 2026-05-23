#!/usr/bin/python3

import os
import subprocess
import multiprocessing.dummy
import multiprocessing
import re
import time
import socket
import argparse, sys
import threading
import psutil
import nmap
from subprocess import check_output


# https://aur.archlinux.org/packages/python-nmap/

#TODO:
#regex to get // check domain
#regex to read ttl
#regex to read packet loss
#regex to read time
#multithreading for multiple pings
#get all ips/hosts from the network with subnets
#maybe a little gui to show all infos
#nice regex but didnt work  ^PING\b[^(]*\(([^)]*)\)\s([^.]*)\..*?^(\d+\sbytes).*?icmp_seq=(\d+).*?ttl=(\d+).*?time=(.*?ms).*?(\d+)\spackets\stransmitted.*?(\d+)\sreceived.*?(\d+%)\spacket\sloss.*?time\s(\d+ms).*?=\s([^\/]*)\/([^\/]*)\/([^\/]*)\/(.*?)\sms
#https://rubular.com/r/uEDoEZwY7U
#regex test: https://rubular.com/r/uEDoEZwY7U
#curses: https://de.wikibooks.org/wiki/Python_unter_Linux:_Curses
#nmap: https://www.programcreek.com/python/example/92225/nmap.PortScanner
#some sockets: https://www.programcreek.com/python/example/266/socket.gethostname
#subnet: https://diego.assencio.com/?index=85e407d6c771ba2bc5f02b17714241e2

#mittelwert vom packet loss und von der latenz(ms) berechnen lassen
#alle hosts im netzwerk gleichzeitig/durchgehend anpingen
#übersicht der hosts mit dem zuletzt gemessenen daten, sowie den durchschnittswerten
#https://stackoverflow.com/questions/27158046/remote-os-detection-in-python

#länge für die liste 'pingData' festlegen. Z.b eine if abfrage...if(pings[address] <= 10): pings[address] = 0;done;

nm = nmap.PortScanner()

ips = []
#data = [{"id":0, "ip":"here stands ips", "icmp":"icmp data", "ptime":"ptime data", "plost": "plost data", "rip": "rip data"},]

data = {}
data2 = []
pingData = {}
pings = {}
localIPs = []
networks = []
hostnames = {}
osystems = {}
    #pingData[0][0] = 0

def help():
    print(" type !h to show this help")

def pingOLD(address):
    print("test")
    p = subprocess.Popen(["ping", "www.google.de", "-c 1"], stdout = subprocess.PIPE)
    #m = re.search("/(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]/g", p.communicate()[0])
    #m = re.search("(((([A-Za-z0-9]+){1,63}\.)|(([A-Za-z0-9]+(\-)+[A-Za-z0-9]+){1,63}\.))+){1,255}", p.communicate()[0])
    #m.group(0)
    print(p.communicate()[0])
    print("regex: ")
    #print(m)

def pingOnly(threadName, delay, address):
    c = 0
    while c != 1:

        p = subprocess.Popen(["ping", address, "-c 1"], stdout = subprocess.PIPE)
        out = str(p.communicate()[0])
        print(str(threadName) + " " + out)
        #m = re.findall(r'\s(?:www.)?(\w+.com)', str(p.communicate()[0]))

        #data = re.findall(r'^PING\b[^(]*\(([^)]*)\)\s([^.]*)\..*?^(\d+\sbytes).*?icmp_seq=(\d+).*?ttl=(\d+).*?time=(.*?ms).*?(\d+)\spackets\stransmitted.*?(\d+)\sreceived.*?(\d+%)\spacket\sloss.*?time\s(\d+ms).*?=\s([^\/]*)\/([^\/]*)\/([^\/]*)\/(.*?)\sms', out)
        #ttl = re.search(r'(?:ttl=[0-9]*)?', out)
        #ttl = re.findall(r'(?:time=([0-9]*.[0-9] ms))?', out)
        #print("domain: " + str(domain) + " ttl: " + str(ttl))
        #ttltime = re.findall(r'ttl=(\d+).*?rtt min\/avg\/max\/mdev = ([0-9.]+)\/', out)  # works
        #ptime = re.findall(r'ttl=(\d+).*?rtt min\/avg\/max\/mdev = ([0-9.]+)\/', out)
        #print("ttltime: " + str(ttltime)) #works
        #print("time: " + str(ptime))
        #data = re.findall(r"PING\b[^(]*\(([^)]*)\)\s([^.]*)\..*?^(\d+\sbytes).*?icmp_seq=(\d+).*?ttl=(\d+).*?time=(.*?ms).*?(\d+)\spackets\stransmitted.*?(\d+)\sreceived.*?(\d+%)\spacket\sloss.*?time\s(\d+ms).*?=\s([^\/]*)\/([^\/]*)\/([^\/]*)\/(.*?)\sms", out)
        icmp = re.findall(r'<?icmp_seq=(\d+)', out)
        ptime = re.findall(r'<?time=([0-9]*.[0-9])', out)
        plost = re.findall(r'<?([0-9]*%)', out)
        rip = re.findall(r'\d+\.\d+\.\d+\.\d+', out)

        print("time: " + str(ptime[0]) + "ms")
        print("icmp: " + str(icmp[0]))
        print("packet lost: " + str(plost[0]))
        print("ip: " + str(rip[0]))
        try:
            domain = re.findall(r'\s(?:www.)?(\w+.(com|org|net|de))', out)
            print("domain: " + str(domain[0][0]))
        except:
            print("no domain vorhanden")
        time.sleep(delay)

def ping(threadName, delay, address, id):
    #time.sleep(3)
    t = 0
    c = 0
    while c != 1:
        time.sleep(0.5)
        t = t + 1
        p = subprocess.Popen(["ping", address, "-c 1"], stdout = subprocess.PIPE)
        out = str(p.communicate()[0])
        #print(str(threadName) + " " + out)
        icmp = re.findall(r'<?icmp_seq=(\d+)', out)
        ptime = re.findall(r'<?time=([0-9]*.[0-9])', out)
        plost = re.findall(r'<?([0-9]*%)', out)
        rip = re.findall(r'\d+\.\d+\.\d+\.\d+', out)

        #print("time: " + str(ptime[0]) + "ms")
        #print("icmp: " + str(icmp[0]))
        #print("packet lost: " + str(plost[0]))
        #print("ip: " + str(rip[0]))

        try:
            domain = re.findall(r'\s(?:www.)?(\w+.(com|org|net|de))', out)
            #print("domain: " + str(domain[0][0]))
            #data[id][t] = str(t), str(icmp), str(ptime), str(plost), str(rip), str(domain[0][0])
            #data[id][t] = str(t), str(icmp), str(ptime), str(rip)
            #data.extend(id, [t, icmp, ptime, rip])
            #data[address + ":" + str(id)] = str(t) + ":" + str(icmp) + ":" + str(ptime) +  ":" +  str(plost) + ":" + str(rip) + ":" +  str(domain[0][0])
            #pingData[address + ":" + str(pings[address])]= "id:" + str(id) , str(t) , str(icmp), str(ptime),str(plost),str(rip)
            if len(pingData) > 1500:
                pingData.clear()

            nms = 1
            #if nms == 1:
                #nm.scan(address)
             #   pingData[address + ":" + str(pings[address])] = "id:" + str(id) ,str(t),str(icmp),str(ptime),str(plost),str(rip), str(nm[address].hostname())
            #else:
            pingData[address + ":" + str(pings[address])] = "id:" + str(id), str(t), str(icmp), str(ptime), str(plost), str(rip)

            #print("ping!2: " + str(address) + ":" + str(pings[address]))
            pings[str(address)] = pings[str(address)] + 1

            #if(address == "10.0.0.254"):
                #print("maybe ending ENDLINE 254!!!!11einsElfelf!!1111!")
             #   if(pings[address] > 0):
             #       pingData[address + ":1"] = "id:" + str(id), str(t), str(icmp), str(ptime), str(plost), str(rip)
             #   if(pings[address] <= 0):
             #       pings[address] = 1
             #       pingData[address + ":1"] = "id:" + str(id), str(t), str(icmp), str(ptime), str(plost), str(rip)

            #pingData[address + ""]
            #data2.append()

        except:
            #print("no domain vorhanden")
            #data[id][t] = str(t), str(icmp), str(ptime), str(plost), str(rip)
            #data.extend(id,[t,icmp,ptime,rip])
            #data[address + ":" + str(id)] = str(t) + ":" + str(icmp) + ":" + str(ptime) + ":" + str(plost) + ":" +str(rip)
            #print("pings[" +  str(address) +"]: " + str(pings[address]))
            #print("ping!: " + pings[address])
            pingData[address + ":" + str(pings[address])] = "id:" + str(id) ,str(t),str(icmp),str(ptime),str(plost),str(rip)
            pings[address] = pings[address] + 1
            #if(address == "10.0.0.223"):
            #    print("maybe ending ENDLINE 223!!!!11einsElfelf!!1111!")
        #time.sleep(delay)

#def ping()

def portCheck(address, port):
    #REMOTE_SERVER = address
    try:
        host= socket.gethostbyname(address)
        s = socket.create_connection((host, port), 2)
        return True
    except:
        pass
    return False


def getLocalIPS():
    ips = ""
    for ifaceName, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  # IPv4
                if "127.0.0" in str(addr.address):
                    print("127 dont add")
                    print("after addr: " + str(addr.address))
                else:
                    ips = str(ips) + " " + str(addr.address)
    localIPs = re.findall(r'[0-9]+(?:\.[0-9]+){3}', str(ips))
    #print("localIPS: " + str(localIPs[0]))
    for x in range(0, len(localIPs)):
        #print("ip" + str(x) + ":"+ str(localIPs[x]))
        network = ".".join(str(localIPs[x]).split(".")[0:-1]) + "."
        #print("network: " + str(network))
        #networks[x] = str(network)
        networks.insert(x, str(network))
    #print("nt: " + str(networks) + "len: " + str(len(networks)))
    for y in range(0, len(networks)):
        print("network"+ str(y) + ": " + str(networks[y]))
        nms = 1
        #if nms == 1:
        #    nm.scan(hosts=str(networks[y]) + ".0/24", arguments='-sP')

def getIPS(network, start, end):
    for ping in range(start, end):
        address = network + str(ping)
        res = subprocess.call(['ping', '-c', '1', address])
        if res == 0:
            print("ping to", address, "OK")
            ips.append(address)
            #nms = 1
            #if nms == 1:
            #    nm.scan(hosts=address, arguments='-sP')
        elif res == 2:
            print("no response from", address)
        else:
            print("ping to", address, "failed!")

def getPing(ip):
    success = subprocess.call(['ping', '-c', '1', ip])
    if success:
        print("{} responded".format(ip))
        #ips.append(ip)
    else:
        print("{} did not respond".format(ip))
        ips.append(ip)
        #nms = 1
        #if nms == 1:
        #    nm.scan(hosts=str(ip), arguments='-sP')
        #    time.sleep(3)
        #data.append(())
    return success

def ping_range(network,start,end):
    num_threads = 32 * multiprocessing.cpu_count()
    p = multiprocessing.dummy.Pool(num_threads)
    p.map(getPing, [network + str(x) for x in range(start,end)])
    #ips.append(network + str(x))

def printData():

    r = 0
    while r != 1:
        #print("data: " + str(pingData))
        os.system("clear")
        #print("len data: " + str(len(pingData)))
        #print("len ips: " + str(len(ips)))
        #print("data1: " + str(pingData['10.0.0.1:1']))
        leer = ""
        print(leer.ljust(75, "_"))
        for i in range(0,len(ips)):
            b = pings[ips[i]] - 1
            if(r <= 0):
                b = 1
            #print("r:" + str(r) + "some: " + str(pingData[ips[i] + ":" + str(r)]))
            try:
                #print("i:" + ips[i] + " ping: " + str(pings[ips[i]] - 1) + ":" + str(pings[ips[i]]) + "-" + str(pingData[ips[i] + ":" + str(pings[ips[i]] -1 )]))
                #sip = str(pings[ips[i]] -1).ljust(15, ".")
                sip = str(ips[i]).ljust(15," ")
                stime =  str(pingData[ips[i] + ":" + str(pings[ips[i]] -1)][3]).ljust(10," ")
                splost = str(pingData[ips[i] + ":" + str(pings[ips[i]] -1)][4]).ljust(10," ")
                #shostname = str(pingData[ips[i] + ":" + str(pings[ips[i]] -1)][6])
                #print("ip: " + ips[i] + ":" + str(pings[ips[i]] - 1) + " time: " + str(pingData[ips[i] + ":" + str(pings[ips[i]] -1)][3]) + " packet lost: " + str(pingData[ips[i] + ":" + str(pings[ips[i]] -1)][4]) )
                #print("| ip: " + sip +  " |    time: " + stime +  " |     packet lost: " + splost + " |")
                nms = 1
                if nms == 1:
                    #shostname = str(pingData[ips[i] + ":" + str(pings[ips[i]] - 1)][6])
                    #try:
                    #shostname = str(nm[ips[i]].hostname())
                    try:
                        shostname = hostnames[ips[i]]
                        #sosystem = osystems[ips[i]]
                        print("| ip: " + sip + " |    time: " + stime + " |     packet lost: " + splost + " |" + shostname + " | ")
                    except:
                        print("| ip: " + sip + " |    time: " + stime + " |     packet lost: " + splost + " | error hostname | " + str(ips[i]))
                        # maybe here start a thread for failed hostname scans
                        #if nms == 1:
                        #    nm.scan(hosts=str(sip), arguments='-Pn')
                        #    try:
                        #        #print("hostname: " + nm[sip].hostname())
                        #        hostnames[sip] = nm[sip].hostname()
                        #    except:
                        #        print("error hostname")
                else:
                    print("| ip: " + sip + " |    time: " + stime + " |     packet lost: " + splost + " |test")

            except:
                print("|                  error with ip: " + ips[i] + " ping: " + str(pings[ips[i]] - 1) + "                   | ")
        print(leer.ljust(75, "–"))
        time.sleep(5)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--domain", help='set the Domain')
    parser.add_argument("-d", help='set the Domain')
    parser.add_argument("--ip", help="set the ip")
    parser.add_argument("--subnet", help="set the subnet")
    parser.add_argument("-p", help='start Ping')
    parser.add_argument("--localIP", help="get local ips")
    parser.add_argument("-lip", help="get local ips")
    parser.add_argument("-a", help="auto scan")
    parser.add_argument("--sip", help="subnet ip (x.x.x.x/xx")
    parser.add_argument("--hostname", help="show hostnames / slower start")

    #parser.add_argument("--help", help="show the help")

    args= parser.parse_args()
    print(args)
    #print(sys)

    if str(args.domain) != "None":
        print(args.domain)
        pingOnly("ping1", 1, args.domain)

    if str(args.d) != "None":
        print(args.d)
        pingOnly("ping2", 1, args.d)

    if str(args.localIP) != "None":
        getLocalIPS()

    if str(args.a) != "None":
        getLocalIPS()
        print("start")
        for y in range(0, len(networks)):
            print("network" + str(y) + ": " + str(networks[y]))
            ping_range(networks[y], 0, 255)
        print("allIPS: " + str(ips))
        if(str(args.p) != "None"):
            for i in range(0, len(ips)):
                time.sleep(1)
                print("ping ip:" + str(ips[i]))
                pings[str(ips[i])] = 1
                t1 = threading.Thread(target=ping, args=("ping" + str(i), 1, str(ips[i]), i))
                t1.start()
            t2 = threading.Thread(target=printData)
            t2.start()

    if str(args.ip) != "None":
        print(args.ip)

        ping_range(str(args.ip),0,255)
        print("ips: " + str(ips))
        print("args.p: " + str(args.p))
        print("some ip: " + str(ips[4]) + " len: " + str(len(ips)))
        if str(args.p) != "None":
            for i in range(0,len(ips)):
                time.sleep(1)
                print("ping ip: " + str(ips[i]))
                pings[str(ips[i])] = 1
                t1 = threading.Thread(target=ping, args=("ping" + str(i), 1, str(ips[i]), i))
                t1.start()
            print("ips: " + str(ips))
            t2 = threading.Thread(target=printData)
            t2.start()

    if str(args.sip != "None"):
        if '/' in str(args.sip):
            # Get address string and CIDR string from command line
            #(addrString, cidrString) = str(args.sip).split('/')
            (addrString, cidrString) = str(args.sip).split('/')
            # Split address into octets and turn CIDR into int
            addr = addrString.split('.')
            cidr = int(cidrString)
            print("addr: " + str(addr))
            print("cidr: " + str(cidr))

            # Initialize the netmask and calculate based on CIDR mask
            mask = [0, 0, 0, 0]
            for i in range(cidr):
                try:
                    mask[i // 8] = mask[i // 8] + (1 << (7 - i % 8))
                    #print("mask: " + str(mask[i // 8]))
                except:
                    print("some error")

            # Initialize net and binary and netmask with addr to get network
            net = []
            for i in range(4):
                net.append(int(addr[i]) & mask[i])

            # Duplicate net into broad array, gather host bits, and generate broadcast
            broad = list(net)
            brange = 32 - cidr
            for i in range(brange):
                broad[3 - i // 8] = broad[3 - i // 8] + (1 << (i % 8))

            # Print information, mapping integer lists to strings for easy printing
            print("Address:   ", addrString)
            print("Netmask:   ", ".".join(map(str, mask)))
            print("Network:   ", ".".join(map(str, net)))
            print("Broadcast: ", ".".join(map(str, broad)))
            print("t network: " + str(net[2]))
            print("b network: " + str(broad[2]))
            netint = broad[2] - net[2]
            print("networks: " + str(netint))
            for i in range(netint):
                print("network " + str(i + 1))
                networkip = str(net[0]) + "." + str(net[1]) + "." + str(net[2] + i ) + "."
                print("network: " + networkip)
                ping_range(networkip, 0, 255)

            for i in range(0, len(ips)):
                time.sleep(1)
                print("ping ip:" + str(ips[i]))
                pings[str(ips[i])] = 1
                t1 = threading.Thread(target=ping, args=("ping" + str(i), 1, str(ips[i]), i))
                t1.start()
            t2 = threading.Thread(target=printData)
            t2.start()

    if len(sys.argv) == 1:
        print("test")
        getLocalIPS()
        print("start")
        for y in range(0, len(networks)):
            print("network" + str(y) + ": " + str(networks[y]))
            ping_range(networks[y], 0, 255)
        print("allIPS: " + str(ips))
        for i in range(0, len(ips)):
            nms = 1
            if nms == 1:
                try:
                    nm.scan(hosts=str(ips[i]), arguments='-sP -p 0')
                    print("hostname: " + nm[ips[i]].hostname())
                    hostnames[ips[i]] = nm[ips[i]].hostname()
                    #osystems[ips[i]] = nm[ips[i]]['osmatch'][0]['osclass'][0]['osfamily']
                except:
                    print("error hostname")
                    try:
                        nm.scan(hosts=str(ips[i]), arguments='-Pn -p 0')
                        print("hostname: " + nm[ips[i]].hostname())
                        hostnames[ips[i]] = nm[ips[i]].hostname()
                        #osystems[ips[i]] = nm[ips[i]]['osmatch'][0]['osclass'][0]['osfamily']
                    except:
                        print("fatal error hostname")

                #time.sleep(1)
            time.sleep(0.1)
            print("start ping Thread for:" + str(ips[i]))
            pings[str(ips[i])] = 1
            t1 = threading.Thread(target=ping, args=("ping" + str(i), 1, str(ips[i]), i))
            t1.start()
        t2 = threading.Thread(target=printData)
        t2.start()


if __name__ == '__main__':
    main()

