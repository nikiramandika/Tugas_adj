from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ether_types

class DeptFirewall(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DeptFirewall, self).__init__(*args, **kwargs)
        # Dictionary untuk MAC Address Table: {dpid: {mac: port}}
        self.mac_to_port = {}
        self.logger.info("DeptFirewall Controller Started")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.logger.info(f"Switch {datapath.id} connected")

        # Install table-miss flow entry (default flood ke controller)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        # Install drop rules untuk Dept A -> Dept C dan Dept C -> Dept A
        self.install_firewall_rules(datapath)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def install_firewall_rules(self, datapath):
        """Install flow rules untuk blocking traffic antar departemen"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Rule 1: Block Dept A (10.0.1.0/24) -> Dept C (10.0.3.0/24)
        match = parser.OFPMatch(
            eth_type=0x0800,  # IPv4
            ipv4_src=('10.0.1.0', '255.255.255.0'),  # Dept A subnet
            ipv4_dst=('10.0.3.0', '255.255.255.0')   # Dept C subnet
        )
        # Drop action (kosong = drop)
        self.add_flow(datapath, 100, match, [])
        self.logger.info("Installed rule: Block Dept A -> Dept C")

        # Rule 2: Block Dept C (10.0.3.0/24) -> Dept A (10.0.1.0/24)
        match = parser.OFPMatch(
            eth_type=0x0800,  # IPv4
            ipv4_src=('10.0.3.0', '255.255.255.0'),  # Dept C subnet
            ipv4_dst=('10.0.1.0', '255.255.255.0')   # Dept A subnet
        )
        # Drop action (kosong = drop)
        self.add_flow(datapath, 100, match, [])
        self.logger.info("Installed rule: Block Dept C -> Dept A")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignore LLDP packet (untuk discovery topology)
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        # Learn MAC address
        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
        self.mac_to_port[dpid][src] = in_port


        # Kita cek apakah paket ini IPv4
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            # Definisi Subnet (String matching)
            # Dept A = 10.0.1.x
            # Dept B = 10.0.2.x
            # Dept C = 10.0.3.x

            # ATURAN 1: Dept A -> Dept C (TIDAK BISA)
            if src_ip.startswith("10.0.1") and dst_ip.startswith("10.0.3"):
                self.logger.warning(f"BLOCKED: Dept A ({src_ip}) trying to reach Dept C ({dst_ip})")
                return # Drop packet (jangan teruskan ke logic switching)

            # ATURAN 2: Dept C -> Dept A (TIDAK BISA)
            if src_ip.startswith("10.0.3") and dst_ip.startswith("10.0.1"):
                self.logger.warning(f"BLOCKED: Dept C ({src_ip}) trying to reach Dept A ({dst_ip})")
                return # Drop packet

            # ATURAN 3: Dept A -> Dept B (DIBOLEHKAN - Default Pass)
            # ATURAN 4: Dept B -> Dept C (DIBOLEHKAN - Default Pass)
            
            # Jika lolos filter di atas, paket akan diproses oleh logic switching di bawah
            
        # ==============================================================
        # AKHIR LOGIKA FIREWALL
        # ==============================================================

        # Normal Switching Logic (L2 Learning Switch)
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow rule agar paket selanjutnya tidak perlu tanya controller lagi
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)