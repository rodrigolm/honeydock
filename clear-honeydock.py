import subprocess

INTERFACE = "eth0"

def get_local_ip():
    local_ip = subprocess.Popen(["ifconfig | grep -A 1 {interface} | grep -Eo 'inet (addr:)?([0-9]*\.){{3}}[0-9]*' | grep -Eo '([0-9]*\.){{3}}[0-9]*' | grep -v '127.0.0.1'".format(interface=INTERFACE)], stdout=subprocess.PIPE, shell=True)
    (out, err) = local_ip.communicate()
    return out.strip()

def banner():
    subprocess.Popen(["clear"], stdout=subprocess.PIPE, shell=True)
    print ""
    print "   _                                _            _     "
    print "  | |                              | |          | |    "
    print "  | |__   ___  _ __   ___ _   _  __| | ___   ___| | __ "
    print "  | '_ \ / _ \| '_ \ / _ \ | | |/ _` |/ _ \ / __| |/ / "
    print "  | | | | (_) | | | |  __/ |_| | (_| | (_) | (__|   <  "
    print "  |_| |_|\___/|_| |_|\___|\__, |\__,_|\___/ \___|_|\_\ "
    print "                           __/ |                       "
    print "                          |___/                   v0.1 "
    print ""

banner()

print "Cleaning process has started."
print "Stopping all running dockers..."
subprocess.Popen(["docker stop $(docker ps -q)"], stdout=subprocess.PIPE, shell=True)
print "Containers stopped."
print "Cleaning iptables rules..."
print "Rule #1"
subprocess.Popen(["iptables -t nat -D PREROUTING -p tcp -d {local_ip} --dport 22 -j DNAT --to {local_ip}:22222".format(local_ip=get_local_ip())], stdout=subprocess.PIPE, shell=True)
print "Rule #2"
subprocess.Popen(["iptables -D INPUT -i eth0 -p tcp --dport 22 -m state --state NEW,ESTABLISHED -j ACCEPT"], stdout=subprocess.PIPE, shell=True)
print "Rule #3"
subprocess.Popen(["iptables -D OUTPUT -o eth0 -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT"], stdout=subprocess.PIPE, shell=True)
print "Rule #4"
subprocess.Popen(["iptables -D OUTPUT -p tcp --tcp-flags SYN,ACK SYN,ACK -j LOG --log-prefix \"Connection established: \" "], stdout=subprocess.PIPE, shell=True)
print "Rules cleared."
print "Done!"

