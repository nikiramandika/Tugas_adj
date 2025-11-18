#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.node import OVSSwitch

def create_topology():
    """
    Membuat topologi jaringan dengan 3 departemen
    Dept A: Switch 1 dengan Host A1, A2
    Dept B: Switch 2 dengan Host B1, B2
    Dept C: Switch 3 dengan Host C1, C2

    Aturan koneksi:
    - Dept A -> Dept B: Bisa connect
    - Dept A -> Dept C: Tidak bisa connect
    - Dept B -> Dept C: Bisa connect
    - Dept C -> Dept A: Tidak bisa connect
    """

    net = Mininet(controller=RemoteController, link=TCLink, switch=OVSSwitch)

    info("*** Adding Controller\n")
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    info("*** Adding Switches for 3 Departments\n")
    # Switch untuk setiap departemen
    switch_a = net.addSwitch('s1')  # Switch untuk Dept A
    switch_b = net.addSwitch('s2')  # Switch untuk Dept B
    switch_c = net.addSwitch('s3')  # Switch untuk Dept C

    info("*** Adding Hosts to each Department\n")
    # Department A (Switch 1)
    host_a1 = net.addHost('h1', ip='10.0.1.10/24', mac='00:00:00:00:01:01')
    host_a2 = net.addHost('h2', ip='10.0.1.11/24', mac='00:00:00:00:01:02')

    # Department B (Switch 2)
    host_b1 = net.addHost('h3', ip='10.0.2.10/24', mac='00:00:00:00:02:01')
    host_b2 = net.addHost('h4', ip='10.0.2.11/24', mac='00:00:00:00:02:02')

    # Department C (Switch 3)
    host_c1 = net.addHost('h5', ip='10.0.3.10/24', mac='00:00:00:00:03:01')
    host_c2 = net.addHost('h6', ip='10.0.3.11/24', mac='00:00:00:00:03:02')

    info("*** Creating links within departments\n")
    # Hubungkan hosts ke switch di departemen yang sama
    # Department A
    net.addLink(host_a1, switch_a)
    net.addLink(host_a2, switch_a)

    # Department B
    net.addLink(host_b1, switch_b)
    net.addLink(host_b2, switch_b)

    # Department C
    net.addLink(host_c1, switch_c)
    net.addLink(host_c2, switch_c)

    info("*** Creating inter-switch links (Physical connections)\n")
    # Hubungkan semua switch (controller akan mengatur aturan routing)
    # Fisiknya semua terhubung, tapi aturan di controller yang menentukan apa boleh connect
    net.addLink(switch_a, switch_b)  # A<->B connection
    net.addLink(switch_b, switch_c)  # B<->C connection
    net.addLink(switch_c, switch_a)  # C<->A connection

    info("*** Starting network\n")
    net.start()

    info("*** Configuring hosts\n")
    # Set default gateway untuk semua host
    host_a1.cmd('ip route add default via 10.0.1.1')
    host_a2.cmd('ip route add default via 10.0.1.1')
    host_b1.cmd('ip route add default via 10.0.2.1')
    host_b2.cmd('ip route add default via 10.0.2.1')
    host_c1.cmd('ip route add default via 10.0.3.1')
    host_c2.cmd('ip route add default via 10.0.3.1')

    info("*** Testing connectivity within departments\n")
    # Test intra-department connectivity (should work)
    print("Testing connectivity within Department A:")
    print(net.ping([host_a1, host_a2]))

    print("Testing connectivity within Department B:")
    print(net.ping([host_b1, host_b2]))

    print("Testing connectivity within Department C:")
    print(net.ping([host_c1, host_c2]))

    info("*** Network Information:\n")
    info("Department A (Switch s1):\n")
    info("  - Host h1: 10.0.1.10\n")
    info("  - Host h2: 10.0.1.11\n")

    info("Department B (Switch s2):\n")
    info("  - Host h3: 10.0.2.10\n")
    info("  - Host h4: 10.0.2.11\n")

    info("Department C (Switch s3):\n")
    info("  - Host h5: 10.0.3.10\n")
    info("  - Host h6: 10.0.3.11\n")

    info("\nConnection Rules (enforced by controller):\n")
    info("  - Dept A -> Dept B: ALLOWED\n")
    info("  - Dept A -> Dept C: BLOCKED\n")
    info("  - Dept B -> Dept C: ALLOWED\n")
    info("  - Dept C -> Dept A: BLOCKED\n")

    info("\n*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_topology()