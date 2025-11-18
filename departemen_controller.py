#!/usr/bin/env python

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, arp, ipv4, icmp
from ryu.lib.packet import ether_types
from ryu.lib import hub

class DepartmentController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DepartmentController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}  
        self.switch_to_department = {
            1: 'A',  # Switch 1 -> Department A
            2: 'B',  # Switch 2 -> Department B
            3: 'C'   # Switch 3 -> Department C
        }
        # Department connectivity rules
        # Source -> [Destinations yang diizinkan]
        self.department_rules = {
            'A': ['A', 'B'],  # Dept A bisa konek ke A dan B
            'B': ['A', 'B', 'C'],  # Dept B bisa konek ke A, B, dan C
            'C': ['B', 'C']   # Dept C bisa konek ke B dan C
        }

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch features request to configure initial flow entries."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        # Install default L2 learning rules
        self._install_l2_learning_rules(datapath)

        self.logger.info("Switch %s connected and configured", datapath.id)

    def _install_l2_learning_rules(self, datapath):
        """Install basic L2 learning rules."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Allow ARP traffic (for network discovery)
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP)
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        self.add_flow(datapath, 1, match, actions)

        # Allow LLDP traffic (for switch discovery)
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_LLDP)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 1, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Add a flow entry to the switch."""
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

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """Handle packet-in messages."""
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                            ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        # Parse the packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Ignore LLDP packets
            return

        dst = eth.dst
        src = eth.src

        dpid = datapath.id

        # Initialize MAC table for this switch if not exists
        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}

        # Learn MAC address to avoid flooding next time
        self.mac_to_port[dpid][src] = in_port

        # Get department information
        src_dept = self._get_department_by_mac(src, dpid)
        dst_dept = self._get_department_by_mac(dst, dpid)

        # Check if this is inter-department traffic
        if src_dept and dst_dept and src_dept != dst_dept:
            if not self._is_connection_allowed(src_dept, dst_dept):
                self.logger.info("Blocked connection: Dept %s -> Dept %s",
                               src_dept, dst_dept)
                # Drop the packet by not installing a flow rule
                return

        # Handle ARP packets
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            self._handle_arp(datapath, in_port, pkt)
            return

        # Forward the packet
        self._forward_packet(datapath, in_port, dst, src)

    def _get_department_by_mac(self, mac, dpid):
        """Get department based on MAC address and switch."""
        # MAC address patterns for each department
        if mac.startswith('00:00:00:00:01:'):
            return 'A'
        elif mac.startswith('00:00:00:00:02:'):
            return 'B'
        elif mac.startswith('00:00:00:00:03:'):
            return 'C'

        # Fallback: determine department by switch
        return self.switch_to_department.get(dpid, None)

    def _is_connection_allowed(self, src_dept, dst_dept):
        """Check if connection between departments is allowed."""
        allowed_destinations = self.department_rules.get(src_dept, [])
        return dst_dept in allowed_destinations

    def _handle_arp(self, datapath, in_port, pkt):
        """Handle ARP packets."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        arp_pkt = pkt.get_protocol(arp.arp)

        if arp_pkt:
            # Flood ARP requests to all ports except incoming
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(datapath=datapath,
                                     buffer_id=ofproto.OFP_NO_BUFFER,
                                     in_port=in_port, actions=actions,
                                     data=pkt.data)
            datapath.send_msg(out)

    def _forward_packet(self, datapath, in_port, dst, src):
        """Forward packet based on learned MAC addresses."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id

        if dst in self.mac_to_port[dpid]:
            # Known destination - send to specific port
            out_port = self.mac_to_port[dpid][dst]
        else:
            # Unknown destination - flood
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow rule if destination is known and not flooding
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)

            # Check if this is inter-department traffic before installing flow
            src_dept = self._get_department_by_mac(src, dpid)
            dst_dept = self._get_department_by_mac(dst, dpid)

            if src_dept and dst_dept and src_dept != dst_dept:
                if not self._is_connection_allowed(src_dept, dst_dept):
                    # Don't install flow for blocked traffic
                    return

            # Add flow with timeout to avoid stale entries
            self.add_flow(datapath, 2, match, actions)

        # Send packet out immediately
        out = parser.OFPPacketOut(datapath=datapath,
                                 buffer_id=ofproto.OFP_NO_BUFFER,
                                 in_port=in_port, actions=actions)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """Handle switch state changes."""
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.logger.info("Switch %s has come up", datapath.id)
        elif ev.state == DEAD_DISPATCHER:
            self.logger.info("Switch %s has gone down", datapath.id)
            # Clean up MAC table for disconnected switch
            if datapath.id in self.mac_to_port:
                del self.mac_to_port[datapath.id]

    def _show_statistics(self):
        """Display network statistics."""
        self.logger.info("=== Network Statistics ===")
        for dpid, mac_table in self.mac_to_port.items():
            self.logger.info("Switch %s (%s): %d learned MAC addresses",
                           dpid, self.switch_to_department.get(dpid, "Unknown"),
                           len(mac_table))

    def print_connection_rules(self):
        """Print the current connection rules."""
        self.logger.info("=== Department Connection Rules ===")
        for src_dept, allowed_dests in self.department_rules.items():
            allowed_str = ", ".join(allowed_dests)
            self.logger.info("Dept %s -> [%s]", src_dept, allowed_str)