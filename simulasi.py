#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
import time

# --- BAGIAN 1: DEFINISI TOPOLOGI ---
class DeptTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # PERBAIKAN DISINI: WAJIB MENGGUNAKAN /16
        # Jika pakai /24, host beda departemen tidak bisa ping (Unreachable)
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

# --- BAGIAN 2: FUNGSI SIMULASI CEK KONEKSI ---
def run_simulation():
    # Inisialisasi Mininet
    topo = DeptTopo()
    # Menghubungkan ke Remote Controller (Ryu yang sedang jalan)
    net = Mininet(topo=topo, 
                  controller=RemoteController(name='c0', ip='127.0.0.1'), 
                  switch=OVSKernelSwitch)
    
    print("\n*** Memulai Jaringan...")
    net.start()

    # Tunggu sebentar agar controller dan switch 'kenalan' (handshake)
    print("*** Menunggu 3 detik agar switch stabil...")
    time.sleep(3)

    hosts = net.hosts
    print("\n" + "="*40)
    print("   MULAI SIMULASI CEK KONEKSI OTOMATIS")
    print("="*40)

    # Loop untuk setiap host mengecek host lain
    for src in hosts:
        for dst in hosts:
            if src == dst:
                continue # Jangan ping diri sendiri

            # Kirim 1 paket ping, timeout 0.5 detik (biar cepat kalau gagal)
            # Menggunakan -W 1 agar tidak menunggu lama jika diblokir firewall
            result = src.cmd('ping -c 1 -W 1 %s' % dst.IP())
            
            # Cek apakah ping berhasil (mencari kata "1 received")
            status = ""
            if '1 received' in result:
                status = "✅ SUKSES (Terhubung)"
            else:
                status = "❌ GAGAL  (Diblokir/Putus)"

            # Tampilkan Animasi Panah Teks
            print(f"[ {src.name} ] --(ping)--> [ {dst.name} ] : {status}")
            
            # Jeda sedikit biar terlihat efek animasinya
            time.sleep(0.1) 

        print("-" * 40) # Garis pemisah per host

    print("\n*** Simulasi Selesai.")
    print("*** Masuk ke CLI Mininet (ketik 'exit' untuk keluar)")
    
    # Masuk ke mode CLI supaya kamu bisa cek manual kalau mau
    CLI(net)
    
    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run_simulation()