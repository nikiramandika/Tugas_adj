from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

# --- 1. DEFINISI TOPOLOGI (Resep) ---
class DeptTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Menggunakan /16 agar semua bisa saling ping (satu broadcast domain)
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

# Baris ini agar tetap bisa dipanggil pakai 'mn --custom' (Opsional)
topos = { 'dept_topo': ( lambda: DeptTopo() ) }


# --- 2. EKSEKUSI LANGSUNG (Agar bisa sudo python3 departemen_topology.py) ---
def run():
    # Buat objek Topologi
    topo = DeptTopo()
    
    # Inisialisasi Mininet dengan Remote Controller (Ryu)
    net = Mininet(topo=topo, 
                  controller=RemoteController(name='c0', ip='127.0.0.1'), 
                  switch=OVSKernelSwitch)
    
    print("\n*** Memulai Jaringan (Departemen Topology)...")
    net.start()
    
    # Masuk ke Mode CLI (mininet>) agar user bisa ketik ping/pingall
    print("*** Masuk ke CLI. Ketik 'exit' untuk keluar.")
    CLI(net)
    
    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()