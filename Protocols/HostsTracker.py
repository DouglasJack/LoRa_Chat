class HostsTracker:
    def __init__(self,msgnr):
        self.messenger = msgnr
        self.knownHosts = []
        return

    def addHost(self, address):
        if address not in self.knownHosts:
            self.knownHosts.append(address)