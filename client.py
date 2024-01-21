"""Defines the client side for a socket based networking application

Allows the client to send 'create' and 'read' requests to the server. 
A 'create request allows the client to address a message for another client, 
which is then stored in the server, a 'read' request gets the server to 
send the Client all the messages addressed to them.

Author: Zya Gurau
Student Number: 64646853
"""

from socket import *
import sys

def get_response(s):
    """Gets a message response from the server

    Recieves data from the server in multiple parts, first recieves the header,
    and chacks validity, then the length of sender name and length of messages, finally
    recieves the senders name and message.
    If there is a gap while reading parts of data error handling occurs.
    
    Args:
        s (socket): the main client socket

    Returns:
        (None)
    """

    try:
        # sets a timeout of one second on the socket throws a timeout error 
        # if there is a gap in data
        s.settimeout(1)
        # recieves the first five bytes of the packet 
        mes_res = s.recv(5)
        req_array = bytearray(mes_res)
        
        # initialises variables from the recieved data
        magic_no = req_array[0]<<8 | req_array[1]
        r_id = req_array[2]
        numitems = req_array[3]
        moremsgs = req_array[4]
        
        # checks if header is valid
        if magic_no != 0xAE73:
            raise ValueError("magic number incorrect")
        if r_id != 3:
            raise ValueError("ID is not 3")
        if moremsgs not in [0,1]:
            raise ValueError("errouneous packet")
        
        # if there are no messages prints info and exit 
        if numitems == 0:
            print("no messages")
            s.close()
            exit()
        
        for i in range(numitems):
            # recieves the next three bytes from the response
            mes_res = s.recv(3)
            req_array = bytearray(mes_res)


            sender_len = req_array[0]
            message_len = req_array[1]<<8 | req_array[2]

            # checks the validity of the recieved data
            if sender_len < 1:
                raise ValueError("Length of sender name must be at least 1 - Erroneous packet")
            if message_len < 1:
                raise ValueError("Length of sender name must be at least 1 - Erroneous packet")

            # recieves the senders name and message date
            mes_res = s.recv(sender_len + message_len)
            req_array = bytearray(mes_res)

            # gets the senders name by iterating through the bytearray based on the length
            # of the senders name
            sender = []
            for i in range(sender_len):
                sender.append(req_array[i])
                
            # gets the message by iterating through the bytearray based on the length
            # of the senders name and message starting from the end of the senders name
            message = []
            for i in range(sender_len,sender_len+message_len):
                message.append(req_array[i])
            
            # decodes the senders name using utf-8
            decode_sender_one = bytearray(sender)
            decode_sender_two = bytes(decode_sender_one)
            sender_done = decode_sender_two.decode("utf-8")
            
            # decodes the message using utf-8
            decode_message_one = bytearray(message)
            decode_message_two = bytes(decode_message_one)
            message_done = decode_message_two.decode("utf-8")  
            
            print("Sender Name:")
            print(sender_done)
            print("")
            print("Message:")
            print(message_done)
            print("")
            print("")
        
        if moremsgs == 1:
            print("more messages available from server")
            print("")
        s.close()
        return None

    except ValueError as err:
        print("ERROR - " + str(err))
        s.close()
        exit()
    except OSError as err:
        print("ERROR - " + str(err))
        s.close()
        exit()
    except UnicodeDecodeError:
        print("ERROR - could not decode")
        s.close()
        exit()
    except TimeoutError:
        print("ERROR - Server timed out")
        s.close()
        exit()
    except IndexError as err:
        print("ERROR - " + str(err))
        s.close()
        exit()

def get_input(s):
    """Gets a clients input for a create request

    Uses While true loops to get input and perform validity checks.
    
    Args:
        s (socket): the main client socket
    
    Returns:
        rec_name (str): the name of the reciever
        message (str): the message written by the client
    """

    try:
        while True:
            rec_name = input("Enter Receiver Name: ")
            if len(rec_name) < 1 or len(rec_name.encode("utf-8")) >= 255:
                print("Reciever name must be at least 1 character long and must be less than 255 bytes")
                continue
            else:
                break
            
        while True:
            message = input("Enter Message: ")
            if len(message) < 1 or len(message.encode("utf-8")) >= 65535:
                print("message must be at least 1 character long and must be less than 65,535 bytes")
                continue
            else:
                break 
        return rec_name, message
    except UnicodeEncodeError:
        print("ERROR - could not encode")
        s.close()
        exit()

def create_request_main(s, name, address):
    """puts together a create request and sends it to the server
    
    Encodes data and appends it to a byte array which is then sent to the server,
    exceptions are raised if errors occur in sending and encoding.

    Args:
        s (socket): the main client socket

    Returns
        (None)
    """

    try:
        rec_name, message = get_input(s)
        rec_name_bytes = rec_name.encode("utf-8")
        message_bytes = message.encode("utf-8")

        name_bytes = name.encode("utf-8")
    except UnicodeEncodeError:
        print("ERROR - could not encode")
        s.close()
        exit()
        
    message_request = bytearray()
    message_request.append(0xAE)
    message_request.append(0x73)

    message_request.append(0x2)
    message_request.append(len(name_bytes))
    message_request.append(len(rec_name_bytes))
    message_request.append(len(message_bytes)>>8)
    message_request.append(0xff & len(message_bytes)) 

    for byte in name_bytes:
        message_request.append(byte)

    for byte in rec_name_bytes:
        message_request.append(byte)
        
    for byte in message_bytes:
        message_request.append(byte)

    try:
        s.settimeout(1)
        s.connect(address)  
        s.send(message_request)

        print("Message for " + rec_name + " Created")

        return None
    except TimeoutError:
        print("ERROR - Server timed out")
        s.close()
        exit()
    except OSError as err:
        print("ERROR -  " + str(err))
        s.close()
        exit()

def read_request_main(s, name, address):
    """Puts together a read request and sends it to the server 
    
    Args:
        s (socket): the main client socket

    Returns:
        (None)
    """

    # Name is initialised globally 
    name_bytes = name.encode("utf-8")


    message_request = bytearray()
    message_request.append(0xAE)
    message_request.append(0x73)

    message_request.append(0x1)
    message_request.append(len(name_bytes))
    message_request.append(0x0)    
    message_request.append(0x0)
    message_request.append(0x0)  

    for byte in name_bytes:
        message_request.append(byte)
    
    
    try:
        #connects to server and sends request
        s.settimeout(1)
        s.connect(address)  
        s.send(message_request)
        return None
    except TimeoutError:
        print("ERROR - Server timed out")
        s.close()
        exit()
    except OSError as err:
        print("ERROR -  " + str(err))
        s.close()
        exit()

def process_argv():
    try:
        # gets values from the arguments on the command line and preforms validity checks on them

        if len(sys.argv) != 5:
            raise ValueError("Request must include exactly four parameters")
        
        filename = sys.argv[0] # "client.py"

        port = int(sys.argv[2]) # 5000

        if port < 1024 or port > 64000:
                    raise ValueError("Port must be between 1024 and 64000 inclusive")
        
        name = sys.argv[3] # "zya gurau"

        if len(name) < 1 or len(name.encode("utf-8")) > 255:
            raise ValueError("user name must be at least one character and less than 255 bytes")

        type_rw = sys.argv[4] # "read"
        
        if type_rw != 'read' and type_rw != 'create':
            raise ValueError("request muse be of type 'read' or 'create'")
        
        services = getaddrinfo(sys.argv[1], port, AF_INET, SOCK_STREAM)
        family, type, proto, canonname, address = services[0]

        return port, name, type_rw, address

    except gaierror:
        print("ERROR - '{argv[1]}' does not exist")
        exit()

    except ValueError as err:
        print("ERROR -  " + str(err))
        exit()

    except IndexError:
        print("ERROR - Request must include exactly four parameters")
        exit()

def main():
    """Sets up read and create requests from the Client"""

    port, name, type_rw, address = process_argv()

    #creates the main socket
    s = socket(AF_INET, SOCK_STREAM)
    # handles read request
    if type_rw == 'read':
        read_request_main(s, name, address)
        get_response(s)
    # handles create request
    elif type_rw == 'create':
        create_request_main(s, name, address)
    s.close()


main()
    
    
    
