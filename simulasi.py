#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
import time
import os
import sys

# --- 1. DEFINISI TOPOLOGI ---
class DeptTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Host dengan Subnet /24 (konsisten dengan departemen_topology.py)
        h1 = self.addHost('h1', ip='10.0.1.1/24')
        h2 = self.addHost('h2', ip='10.0.1.2/24')
        h3 = self.addHost('h3', ip='10.0.2.1/24')
        h4 = self.addHost('h4', ip='10.0.2.2/24')
        h5 = self.addHost('h5', ip='10.0.3.1/24')
        h6 = self.addHost('h6', ip='10.0.3.2/24')

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s2)
        self.addLink(h5, s3)
        self.addLink(h6, s3)

        self.addLink(s1, s2)
        self.addLink(s2, s3)

# --- 2. LOGIKA SIMULASI OTOMATIS ---
def run_simulation():
    print("\n" + "="*60)
    print("    FIREWALL DEPARTEMEN")
    print("="*60)
    print("\n📋 ATURAN FIREWALL:")
    print("✅ Dept A (10.0.1.x) -> Dept B (10.0.2.x) = DIBOLEHKAN")
    print("✅ Dept B (10.0.2.x) -> Dept C (10.0.3.x) = DIBOLEHKAN")
    print("❌ Dept A (10.0.1.x) -> Dept C (10.0.3.x) = DIBLOKIR")
    print("❌ Dept C (10.0.3.x) -> Dept A (10.0.1.x) = DIBLOKIR")
    print("\n⚠️  PASTIKAN RYU CONTROLLER SUDAH BERJALAN:")
    print("   ryu-manager departemen_controller.py")
    print("="*60)

    input("\nTekan ENTER untuk melanjutkan...")

    topo = DeptTopo()
    # Koneksi ke Controller
    net = Mininet(topo=topo,
                  controller=RemoteController(name='c0', ip='127.0.0.1', port=6653),
                  switch=OVSKernelSwitch,
                  buildWait=True)

    print("\n*** Memulai Jaringan Mininet...")
    net.start()

    print("*** Menunggu koneksi ke controller...")
    time.sleep(5)

    # Cek status koneksi controller
    print("\n" + "="*50)
    print("   STATUS KONEKSI CONTROLLER")
    print("="*50)
    for switch in net.switches:
        if switch.connected():
            print(f"✅ Switch {switch.name} terhubung ke controller")
        else:
            print(f"❌ Switch {switch.name} TIDAK terhubung ke controller")

    # Test spesifik sesuai aturan firewall
    print("\n" + "="*50)
    print("   TESTING FIREWALL RULES")
    print("="*50)

    test_cases = [
        ('h1', 'h3', "Dept A -> Dept B (HARUS BISA)", True),
        ('h3', 'h5', "Dept B -> Dept C (HARUS BISA)", True),
        ('h1', 'h5', "Dept A -> Dept C (HARUS DIBLOKIR)", False),
        ('h5', 'h1', "Dept C -> Dept A (HARUS DIBLOKIR)", False),
        ('h2', 'h4', "Dept A -> Dept B (HARUS BISA)", True),
        ('h6', 'h2', "Dept C -> Dept A (HARUS DIBLOKIR)", False)
    ]

    for src_name, dst_name, description, should_pass in test_cases:
        src_host = net.get(src_name)
        dst_host = net.get(dst_name)

        print(f"\n🧪 {description}")
        print(f"   {src_name} ({src_host.IP()}) --> {dst_name} ({dst_host.IP()})")

        # Lakukan ping
        result = src_host.cmd(f'ping -c 2 -W 2 {dst_host.IP()}')

        success = '2 received' in result
        if success == should_pass:
            status = "✅ BENAR"
            if success:
                print(f"   {status} - Paket diteruskan")
            else:
                print(f"   {status} - Paket diblokir firewall")
        else:
            status = "❌ SALAH"
            if success:
                print(f"   {status} - Seharusnya diblokir tapi paket lolos!")
            else:
                print(f"   {status} - Seharusnya lolos tapi paket diblokir!")

        time.sleep(1)

    print("\n" + "="*50)
    print("   SIMULASI SELESAI. MASUK KE MODE MANUAL.")
    print("   Ketik 'exit' untuk keluar dari Mininet")
    print("="*50)

    # --- 3. MASUK MODE CLI (Agar tidak langsung keluar) ---
    CLI(net)

    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run_simulation()