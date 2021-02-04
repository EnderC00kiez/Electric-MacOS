######################################################################
#                               PACKET                               #
######################################################################

class Packet:
    def __init__(self, json_name, display_name, darwin, darwin_type, install_directory):
        self.json_name = json_name
        self.display_name = display_name
        self.darwin = darwin
        self.darwin_type = darwin_type
        self.install_directory = install_directory