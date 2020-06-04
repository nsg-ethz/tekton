#
# This file is a work in progress, there's no guarantee that this list is complete and things
# are constantly added when necessary. There can be more defaults somewhere in the code which
# are not listed in this file
#

#Start of gns3.py file
default_dynampis_addr = '127.0.0.1:7200'
default_console_start_port = 2501
default_working_dir = '/tmp'
# default_ios_image = '/home/ahassany/GNS3/images/IOS/c7200-advipservicesk9-mz.152-4.S5.image'
default_ios_image = '/home/robin/GNS3/images/c7200-adventerprisek9-mz.124-24.T8.image'
default_router_model = '7200'
default_idlepc = '0x606e0510'
default_idelmax = '500'
default_ram = '512'
default_nvram = '512'
default_npe = 'npe-400'


#Enum used in cisco.py to identify protocol
#From synet/utils/common.py definition
#If tekton is not used with synet comment import out

from synet.utils.common import Protocols