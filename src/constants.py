######################################################################
#                              CONSTANTS                             #
######################################################################


from time import strftime
import platform
import sys
import os

# Set Of Constants That Can Be Used Throughout The Code

__version__ = '1.0.0a'

def get_architecture():
    if platform.machine().endswith('64'):
        return 'x64'
    if platform.machine().endswith('86'):
        return 'x32'
    

    return None


# Install Debug Headers
install_debug_headers = [
    f"Attaching debugger at {strftime('%H:%M:%S')} on install::initialization",
    f"Electric is running on {platform.platform()}",
    f"User machine name: {platform.node()}",
    f"Command line: \"{' '.join(sys.argv)}\"",
    f"Arguments: \"{' '.join(sys.argv[1:])}\"",
    f"Current directory: {os.getcwd()}",
    f"Electric version: {__version__}",
    f"System architecture detected: {get_architecture()}"
]

# Uninstall Debug Headers
uninstall_debug_headers = [
    f"Attaching debugger at {strftime('%H:%M:%S')} on uninstall::initialization",
    f"Electric is running on {platform.platform()}",
    f"User domain name: {platform.node()}",
    f"Command line: \"{' '.join(sys.argv)}\"",
    f"Arguments: \"{' '.join(sys.argv[1:])}\"",
    f"Current directory: {os.getcwd()}",
    f"Electric version: {__version__}",
    f"System architecture detected: {get_architecture()}"
]
