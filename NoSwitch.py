# -*- coding: utf-8 -*-
import struct
import socket
import random
import logging
import threading
import time
import getopt,sys

# /* Header on all OpenFlow packets. */
# struct ofp_header {
# uint8_t version; /* OFP_VERSION. */
# uint8_t type; /* One of the OFPT_ constants. */
# uint16_t length; /* Length including this ofp_header. */
# uint32_t xid; /* Transaction id associated with this packet.
# Replies use the same id as was in the request
# to facilitate pairing. */
# };
# OFP_ASSERT(sizeof(struct ofp_header) == 8);


# /* Switch features. */
# struct ofp_switch_features  {
# struct ofp_header header;
# uint64_t datapath_id;   /* Datapath unique ID.  The lower 48‐bits are for
# a MAC address, while the upper 16‐bits are
# implementer‐defined.  */
# uint32_t n_buffers;  /* Max packets buffered at once. */
# uint8_t n_tables;   /* Number of tables supported by datapath. */
# uint8_t pad[3];  /* Align to 64‐bits. */
# /* Features. */
# uint32_t capabilities;   /* Bitmap of support "ofp_capabilities".  */
# uint32_t actions;   /* Bitmap of supported "ofp_action_type"s.  */
# /* Port info.*/
# struct ofp_phy_port ports[0];  /* Port definitions.   The number of ports
# is inferred from the length field in
# the header. */
# };
# OFP_ASSERT(sizeof(struct  ofp_switch_features)  == 32);



# enum ofp_type {
# /* Immutable messages. */
# OFPT_HELLO,   /* Symmetric message */
# OFPT_ERROR,  /* Symmetric message */
# OFPT_ECHO_REQUEST,  /* Symmetric message */
# OFPT_ECHO_REPLY,  /* Symmetric message */
# OFPT_VENDOR,  /* Symmetric message */
# /* Switch configuration messages. */ OFPT_FEATURES_REQUEST,  /*
# Controller/switch message */ OFPT_FEATURES_REPLY,  /* Controller/switch message
# */  OFPT_GET_CONFIG_REQUEST,      /*  Controller/switch  message  */
# OFPT_GET_CONFIG_REPLY,   /* Controller/switch message */ OFPT_SET_CONFIG,
#   /* Controller/switch message */
# /* Asynchronous messages. */
# OFPT_PACKET_IN,   /* Async message */
# OFPT_FLOW_REMOVED,  /* Async message */
# OFPT_PORT_STATUS,   /* Async message */
# /* Controller command messages. */
# OFPT_PACKET_OUT,  /* Controller/switch message */
# OFPT_FLOW_MOD,  /* Controller/switch message */
# OFPT_PORT_MOD,  /* Controller/switch message */
# /* Statistics messages. */
# OFPT_STATS_REQUEST,  /* Controller/switch message */
# OFPT_STATS_REPLY,  /* Controller/switch message */
# /* Barrier messages. */
# OFPT_BARRIER_REQUEST,   /* Controller/switch message */
# OFPT_BARRIER_REPLY,   /* Controller/switch message */
# /* Queue Configuration messages. */ OFPT_QUEUE_GET_CONFIG_REQUEST,  /*
# Controller/switch message */ OFPT_QUEUE_GET_CONFIG_REPLY /* Controller/switch
# message */
# };



#logging.basicConfig(level=logging.DEBUG)

OF_HEADER_FORMAT  = '!BBHI'
OF_PAYLOAD_FORMAT = 'QIBxxxII'
OF_HEADER_SIZE    = struct.calcsize(OF_HEADER_FORMAT)
OFP_VERSION       = 1

OF_HELLO = 0
OFPT_ERROR = 1
OF_ECHO_REQUEST = 2
OF_ECHO_REPLY = 3
OFPT_VENDOR = 4
OF_FEATUERS_REQUEST = 5
OF_FEATURES_REPLY = 6
OF_GET_CONFIG_REQUEST = 7
OF_GET_CONFIG_REPLY = 8
OF_SET_CONFIG = 9
OFPT_PACKET_IN = 10
OFPT_FLOW_REMOVED = 11
OFPT_PORT_STATUS = 12 
OFPT_PACKET_OUT = 13 
OFPT_FLOW_MOD = 14 
OFPT_PORT_MOD = 15 
OF_STATS_REQUEST = 16
OF_STATS_REPLY = 17
OF_BARRIER_REQUEST = 18
OF_BARRIER_REPLY = 19
OFPT_QUEUE_GET_CONFIG_REQUEST = 20
OFPT_QUEUE_GET_CONFIG_REPLY= 21

class NoSwitch(object):

        def __init__(self,host,port):
              self.sock = socket.socket()
              self.sock.connect((host, port))
              self.dpid = random.randrange(1 << 64)
 
        def run(self):
              self.send_data(OF_HELLO)
              while 1:
                (recv_protocol_type,recv_tid)=self.recv_data()
                self.handle_request(recv_protocol_type,recv_tid)

              

        def send_data(self,ofp_type,payload='',tid = 0):

            length = OF_HEADER_SIZE + len(payload)

            msg = struct.pack(OF_HEADER_FORMAT,
                              OFP_VERSION,
                              ofp_type, 
                              length, 
                              tid)
            msg += payload
            self.sock.send(msg)


        def recv_data(self):
             ofp_type=0
             header = self.sock.recv(OF_HEADER_SIZE)
             length=0
             tid=0
            
             while len(header) < OF_HEADER_SIZE:
                    header += self.sock.recv(OF_HEADER_SIZE - len(header))
             version, ofp_type, length, tid = struct.unpack(
                     OF_HEADER_FORMAT, header)
             more_bytes = length - OF_HEADER_SIZE

             if more_bytes:
                  payload = self.sock.recv(more_bytes)
                  while len(payload) < more_bytes:
                      payload += self.sock.recv(more_bytes - len(payload))
             else:
                  payload = ''
  
             return (ofp_type,tid)
             

        def handle_request(self,ofp_type,tid=0):

            if(ofp_type==OF_HELLO):
                    logging.debug('OF_HELLO') 

            elif(ofp_type==OF_FEATUERS_REQUEST):
                    self.reply_features_request(OF_FEATURES_REPLY,tid)
                    logging.debug('OF_FEATURES_REQUEST')  

            elif(ofp_type==OF_SET_CONFIG):   
                    logging.debug('OF_SET_CONFIG') 

            elif(ofp_type==OF_BARRIER_REQUEST):   
                    self.send_data(OF_BARRIER_REPLY,'',tid)
                    logging.debug('OF_BARRIER_REQUEST')
                     
            else:    
                    logging.debug('Unknown OF_Protocol Type : No = {0}'.format(ofp_type))
                   

        def reply_features_request(self,ofp_type,tid):
            # 同时缓存最大包个数
            n_buffers = 0
            # 交换机支持的流表个数。
            n_tables = 0
            # 表示交换机支持的功能。
            # /* Capabilities supported by the datapath. */
            # enum ofp_capabilities {
            # OFPC_FLOW_STATS = 1 << 0, /* Flow statistics. */
            # OFPC_TABLE_STATS = 1 << 1, /* Table statistics. */
            # OFPC_PORT_STATS  = 1 << 2, /* Port statistics. */
            # OFPC_STP  = 1 << 3,  /* 802.1d spanning tree. */ 
            # OFPC_RESERVED   = 1 << 4,  /* Reserved, must be zero. */ 
            # OFPC_IP_REASM   = 1 << 5,  /* Can reassemble IP fragments. */ 
            # OFPC_QUEUE_STATS   = 1 << 6,  /* Queue statistics. */
            # OFPC_ARP_MATCH_IP   = 1 << 7  /* Match IP addresses in ARP pkts. */
            # };
            ofp_capabilities = 0x000000ef
            # 表示交换机支持的操作。
            actions = 0x00000fff

            payload = struct.pack(
                OF_PAYLOAD_FORMAT,
                self.dpid, 
                n_buffers, 
                n_tables,
                ofp_capabilities, 
                actions)

            self.send_data(ofp_type,payload,tid)


def start_ns(host,port,thread_num):

   def run_ns():

     ns=NoSwitch(host,port)
     while 1:
       ns.run()

   threads = []

   for _ in range(thread_num):
        th = threading.Thread(target=run_ns)
        time.sleep(0.01)       #太快了会报错
        th.setDaemon(True)
        th.start()
        threads.append(th)

   for t in threads:
        t.join()

   print thread_num,'connection(s) completed'


if __name__=='__main__':
    # host='127.0.0.2'
    # port=6633
    # count = 0

    try:
      options,args = getopt.getopt(sys.argv[1:],"h:p:n:",["host=","port=","count="])
    except getopt.GetoptError:
      sys.exit()
    
    for name,value in options:
      if name in ("-h","--host"):
        logging.debug('host is {0}'.format(value))
        host = value
        
      if name in ("-p","--ip"):
        port = int(value)
        logging.debug('port is {0}'.format(value))
     
      if name in ("-n","--port"):
        count = int(value)
        logging.debug('count is {0}'.format(value))
    
    print 'NoSwitch 0.0.1 By Ark'  
    try:
        start_ns(host,port,count)
    except  NameError as e:
        print 'Parameter Error'

    #cmd python NoSwitch.py -h 127.0.0.1  -p 6633  -n 10
   
