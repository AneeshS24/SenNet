import os
import logging

def block_ip(ip):
    os.system(f'netsh advfirewall firewall add rule name="Block {ip}" dir=in action=block remoteip={ip}')
    logging.info(f"Blocked IP: {ip}")
    print(f"Blocked IP: {ip}")
