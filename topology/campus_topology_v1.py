from mininet.topo import Topo


class CampusTopologyV1(Topo):
    """
    Professional campus-like SDN topology.

    Layers:
    - Core layer
    - Distribution layer
    - Access layer

    Logical segments:
    - Student
    - Academic
    - Administrative
    - Guest
    - Attacker Lab
    - Server
    - Monitoring
    - Quarantine
    """

    def build(self):
        # -----------------------------
        # Switches
        # -----------------------------

        # Core
        s1_core = self.addSwitch("s1")

        # Distribution
        s2_dist_left = self.addSwitch("s2")
        s3_dist_right = self.addSwitch("s3")

        # Access
        s4_student_access = self.addSwitch("s4")
        s5_staff_guest_access = self.addSwitch("s5")
        s6_lab_server_access = self.addSwitch("s6")
        s7_monitor_quarantine_access = self.addSwitch("s7")

        # -----------------------------
        # Inter-switch links
        # -----------------------------

        # Core to distribution
        self.addLink(s1_core, s2_dist_left, bw=1000, delay="2ms")
        self.addLink(s1_core, s3_dist_right, bw=1000, delay="2ms")

        # Distribution to access
        self.addLink(s2_dist_left, s4_student_access, bw=100, delay="3ms")
        self.addLink(s2_dist_left, s5_staff_guest_access, bw=100, delay="3ms")

        self.addLink(s3_dist_right, s6_lab_server_access, bw=100, delay="3ms")
        self.addLink(s3_dist_right, s7_monitor_quarantine_access, bw=100, delay="3ms")

        # Optional redundancy links for campus-like behavior.
        # Disabled for the first version to avoid loops without STP.
        # self.addLink(s2_dist_left, s3_dist_right, bw=100, delay="5ms")
        # self.addLink(s4_student_access, s5_staff_guest_access, bw=100, delay="5ms")
        # self.addLink(s6_lab_server_access, s7_monitor_quarantine_access, bw=100, delay="5ms")

        # -----------------------------
        # Hosts by segment
        # -----------------------------

                # Student segment: 10.10.10.0/24
        h1 = self.addHost("h1", ip="10.10.10.1/24", mac="00:00:00:00:10:01", defaultRoute="via 10.10.10.254")
        h2 = self.addHost("h2", ip="10.10.10.2/24", mac="00:00:00:00:10:02", defaultRoute="via 10.10.10.254")
        h3 = self.addHost("h3", ip="10.10.10.3/24", mac="00:00:00:00:10:03", defaultRoute="via 10.10.10.254")
        h4 = self.addHost("h4", ip="10.10.10.4/24", mac="00:00:00:00:10:04", defaultRoute="via 10.10.10.254")

        # Academic segment: 10.10.20.0/24
        h5 = self.addHost("h5", ip="10.10.20.5/24", mac="00:00:00:00:20:05", defaultRoute="via 10.10.20.254")
        h6 = self.addHost("h6", ip="10.10.20.6/24", mac="00:00:00:00:20:06", defaultRoute="via 10.10.20.254")
        h7 = self.addHost("h7", ip="10.10.20.7/24", mac="00:00:00:00:20:07", defaultRoute="via 10.10.20.254")

        # Administrative segment: 10.10.30.0/24
        h8 = self.addHost("h8", ip="10.10.30.8/24", mac="00:00:00:00:30:08", defaultRoute="via 10.10.30.254")
        h9 = self.addHost("h9", ip="10.10.30.9/24", mac="00:00:00:00:30:09", defaultRoute="via 10.10.30.254")

        # Guest segment: 10.10.50.0/24
        h10 = self.addHost("h10", ip="10.10.50.10/24", mac="00:00:00:00:50:10", defaultRoute="via 10.10.50.254")
        h11 = self.addHost("h11", ip="10.10.50.11/24", mac="00:00:00:00:50:11", defaultRoute="via 10.10.50.254")

        # Attacker lab segment: 10.10.60.0/24
        h12 = self.addHost("h12", ip="10.10.60.12/24", mac="00:00:00:00:60:12", defaultRoute="via 10.10.60.254")
        h13 = self.addHost("h13", ip="10.10.60.13/24", mac="00:00:00:00:60:13", defaultRoute="via 10.10.60.254")

        # Server segment: 10.10.40.0/24
        h14 = self.addHost("h14", ip="10.10.40.14/24", mac="00:00:00:00:40:14", defaultRoute="via 10.10.40.254")

        # Monitoring segment: 10.10.70.0/24
        h15 = self.addHost("h15", ip="10.10.70.15/24", mac="00:00:00:00:70:15", defaultRoute="via 10.10.70.254")

        # Quarantine segment: 10.10.99.0/24
        h16 = self.addHost("h16", ip="10.10.99.16/24", mac="00:00:00:00:99:16", defaultRoute="via 10.10.99.254")

        # -----------------------------
        # Host-to-access links
        # -----------------------------

        # Student hosts
        for host in [h1, h2, h3, h4]:
            self.addLink(host, s4_student_access, bw=100, delay="1ms")

        # Academic, administrative, guest hosts
        for host in [h5, h6, h7, h8, h9, h10, h11]:
            self.addLink(host, s5_staff_guest_access, bw=100, delay="1ms")

        # Attacker lab and server
        for host in [h12, h13, h14]:
            self.addLink(host, s6_lab_server_access, bw=100, delay="1ms")

        # Monitoring and quarantine
        for host in [h15, h16]:
            self.addLink(host, s7_monitor_quarantine_access, bw=100, delay="1ms")


topos = {
    "campus_v1": CampusTopologyV1
}
