def find_psu(self):
    for res in self.rm.list_resources():
        try:
            inst = self.rm.open_resource(res, timeout=3000)
            idn = inst.query("*IDN?").strip()
            if "RIGOL" in idn and "DP832" in idn:
                self.log_signal.emit(f"PSU connected: {idn}", False)
                return inst
            inst.close()
        except Exception:
            pass
    return None