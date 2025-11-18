from mininet.topo import Topo

class DeptTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1') # Switch Dept A
        s2 = self.addSwitch('s2') # Switch Dept B
        s3 = self.addSwitch('s3') # Switch Dept C

        # Perhatikan: IP menggunakan /16, bukan /24
        # Dept A
        h1 = self.addHost('h1', ip='10.0.1.1/16')
        h2 = self.addHost('h2', ip='10.0.1.2/16')
        
        # Dept B
        h3 = self.addHost('h3', ip='10.0.2.1/16')
        h4 = self.addHost('h4', ip='10.0.2.2/16')

        # Dept C
        h5 = self.addHost('h5', ip='10.0.3.1/16')
        h6 = self.addHost('h6', ip='10.0.3.2/16')

        # Link Host ke Switch
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s2)
        self.addLink(h5, s3)
        self.addLink(h6, s3)

        # Link Antar Switch
        self.addLink(s1, s2)
        self.addLink(s2, s3)

topos = { 'dept_topo': ( lambda: DeptTopo() ) }