#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
import time

# --- 1. DEFINISI TOPOLOGI ---
class DeptTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Host dengan Subnet /16
        h1 = self.addHost('h1', ip='10.0.1.1/16')
        h2 = self.addHost('h2', ip='10.0.1.2/16')
        h3 = self.addHost('h3', ip='10.0.2.1/16')
        h4 = self.addHost('h4', ip='10.0.2.2/16')
        h5 = self.addHost('h5', ip='10.0.3.1/16')
        h6 = self.addHost('h6', ip='10.0.3.2/16')

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
    topo = DeptTopo()
    # Koneksi ke Controller
    net = Mininet(topo=topo, 
                  controller=RemoteController(name='c0', ip='127.0.0.1'), 
                  switch=OVSKernelSwitch)
    
    print("\n*** Memulai Jaringan Mininet...")
    net.start()

    print("*** Menunggu 3 detik agar switch stabil...")
    time.sleep(3)

    hosts = net.hosts
    print("\n" + "="*50)
    print("   MULAI PENGECEKAN KONEKSI (PING OTOMATIS)")
    print("="*50)

    # Loop Cek Koneksi
    for src in hosts:
        for dst in hosts:
            if src == dst: 
                continue 

            # Perintah Ping (timeout 0.5 detik)
            # -c 1 : kirim 1 paket
            # -W 1 : tunggu max 1 detik
            result = src.cmd('ping -c 1 -W 1 %s' % dst.IP())
            
            status = ""
            if '1 received' in result:
                status = "✅ SUKSES"
            else:
                status = "❌ DIBLOKIR"

            # Cetak Hasil dengan Animasi
            print(f"[ {src.name} ] --(ping)--> [ {dst.name} ] : {status}")
            
            # Jeda 0.2 detik biar enak dilihat
            time.sleep(0.2)

        print("-" * 50)

    print("\n*** Simulasi Selesai. Masuk ke mode Manual CLI.")
    
    # --- 3. MASUK MODE CLI (Agar tidak langsung keluar) ---
    CLI(net)
    
    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run_simulation()