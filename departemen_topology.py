from mininet.topo import Topo

class DeptTopo(Topo):
    def build(self):
        # Membuat 3 Switch
        s1 = self.addSwitch('s1') # Dept A Switch
        s2 = self.addSwitch('s2') # Dept B Switch
        s3 = self.addSwitch('s3') # Dept C Switch

        # Membuat Host untuk Dept A (IP 10.0.1.x)
        h1 = self.addHost('h1', ip='10.0.1.1/24')
        h2 = self.addHost('h2', ip='10.0.1.2/24')
        
        # Membuat Host untuk Dept B (IP 10.0.2.x)
        h3 = self.addHost('h3', ip='10.0.2.1/24')
        h4 = self.addHost('h4', ip='10.0.2.2/24')

        # Membuat Host untuk Dept C (IP 10.0.3.x)
        h5 = self.addHost('h5', ip='10.0.3.1/24')
        h6 = self.addHost('h6', ip='10.0.3.2/24')

        # Menghubungkan Host ke Switch masing-masing
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        
        self.addLink(h3, s2)
        self.addLink(h4, s2)
        
        self.addLink(h5, s3)
        self.addLink(h6, s3)

        # Menghubungkan Switch (Trunk links)
        # S1 <-> S2 <-> S3
        self.addLink(s1, s2)
        self.addLink(s2, s3)

topos = { 'dept_topo': ( lambda: DeptTopo() ) }