"""Defines the server side for a socket based networking application

allows clients to make 'read' or 'create' requests using bytearrays, using 'create' Clients can 
send messages to the server addressed to other clients that the server will then store for them.
Using a 'read' request a Client can get the server to send them up to 255 of the messages stored 
for them by the server.

Name: Zya Gurau
Student Number: 64646853
"""

from socket import *   
import sys

#the dict used to store Client messages
messages = dict()

#gets the prt number from command lines arguments and check if its valid
try:
        port = int(sys.argv[1]) # 50000
        if port < 1024 or port > 64000:
                raise ValueError()
except TypeError:
        print("ERROR - Port must be a number")
        exit()

except ValueError:
        print("ERROR - Port must be between 1024 and 64000 inclusive")
        exit()

except IndexError:
        print("ERROR - Server takes exactly one argument")
        exit()


def create_initial_response(message_response, num_items, more_msgs):
        """returns the basic packet header for a read request
        
        Args: 
                message_response (bytearray): The bytearray that will contain the message response
                num_items (int): The number of messages addressed to the client
                is_empty (bool): A flag indicating whether there are no messages addressed to the client
        
        Returns:
                message_response (bytearray): The bytearray containing the packet header for the message response
        """       
                        
        message_response.append(0xAE)
        message_response.append(0x73) 
        message_response.append(0x3)
        message_response.append(num_items)
        message_response.append(more_msgs)
        
        return message_response

def add_messages(message_response, items, num_items, s, c):
        """Adds messages to the message response bytearray

        Iterates through the messages stored for the client in range of the number of items
        able to be sent and adds them the the response 
        
        Args:
                message_response (bytearray): The bytearray containing the message response header
                items (list): The list of messages addressed to the client
                num_items (int): The number of messages able to be added to the bytearray
                s (socket): The server socket
                c (socket): The connection socket

        Returns:
                message_response (bytearray): The bytearray containing the packet header and the 
                        messages addressed to the client
        """

        try:

                for i in range(num_items):
                        message_bytes = items[i][1]
                
                        sender_bytes = items[i][0].encode("utf-8")
                                        
                        message_response.append(len(sender_bytes))
                        message_response.append(len(message_bytes)>>8)
                        message_response.append(0xff & len(message_bytes)) 
                        
                        for byte in sender_bytes:
                                message_response.append(byte)
                        for byte in message_bytes:
                                message_response.append(byte)
                return message_response
        except UnicodeEncodeError:
                print("ERROR - could not encode message")
                c.close()
                exit()

def create_response_message(sen_name, s, c):
        """Creates a message response to a 'read' request
        
        Args: 
                sen_name (str): The name of the client who sent the 'read' request
                s (socket): The server socket
                c (socket): The connection socket
        
        Returns:
                num_items (int): The number of messsages included in the message_response
                message_response (bytearray): The bytearray containing the message response
        """

        num_items = 0
        more_msgs = 0
        message_response = bytearray()

        # generates the packet header and adds the saved messages to the packet
        if sen_name in messages.keys():
                items = messages[sen_name]

                # the number of messages stored for the Client
                num_items = len(messages[sen_name]) 

                # sets a message send limit of 255 
                # If there are more than 255 messages for the client then 255 are sent with
                # a flag set indicating there are more messages available
                if num_items > 255:
                        more_msgs = 1
                        num_items = 255
                elif num_items == 0:
                        more_msgs = 0
                        num_items = 0 

                message_response = create_initial_response(message_response, num_items, more_msgs)    
                message_response = add_messages(message_response, items, num_items, s, c)    

        # generats a packet header indicating there no messages stored for the client           
        else:
                message_response = create_initial_response(message_response, num_items, more_msgs)  
        return num_items, message_response

def read_request(name_len, req_array, s, c):
        """Gathers the necessary data to handle a clients 'read' request
        
        Args:
                name_len (int): The number of bytes the clients name takes up in the message request bytearray
                req_array (bytearray): The bytearray containing the clients 'read' request
                s (socket): The server socket
                c (socket): The connection socket

        Returns:
                sen_name (str): The name of the client
                num_items (int): The number of messages included in the message response
                message_response (bytearray): The bytearray containing the message response
        """

        sen_name = get_name(req_array, 7, 7+name_len, s, c)
        num_items, message_response = create_response_message(sen_name, s, c)   
        return sen_name, num_items, message_response

def get_name(req_array, range_val_one, range_val_two, s, c):
        """Get a name from a message request array

        Uses a 'loop in range' to extract the relevant data to decode the name
        
        Args:
                req_array (bytearray): The bytearray containing the clients 'read' request
                range_val_one (int): The lower bound for the range loop
                range_val_two (int): The upper bound for the range loop
                s (socket): The server socket
                c (socket): The connection socket

        Returns:
                name (str): The decoded name
        """

        try:
                name_array = []
                for i in range(range_val_one, range_val_two):
                        name_array.append(req_array[i])
                dec_name = bytearray(name_array)
                byte_name = bytes(dec_name)
                name = byte_name.decode("utf-8")
                return name
        except UnicodeDecodeError:
                print("ERROR - could not decode")
                c.close()
                exit()

def get_message(req_array, range_val_one, range_val_two):
        """Gets the message from a clients 'create' request
        
        Uses a 'loop in range' to extract the message data

        Args:
                req_array (bytearray): The bytearray containing the clients 'create' request
                range_val_one (int): The lower bound for the range loop
                range_val_two (int): The upper bound for the range loop

        Returns:
                message (bytearray): The bytearray containing the message data
        """
        message = []
        for i in range(range_val_one, range_val_two):
                message.append(req_array[i])
        return bytearray(message)        
        
def create_request(req_array, name_len, receiver_len,s,c):
        """Handles a clients 'create' request 
        
        Args:
                req_array (bytearray): The bytearray containing the clients 'create' request
                name_len (int): The number of bytes the clients name takes up in the message request bytearray
                receiver_len (int): The number of bytes the recievers name take up in the message request bytearray
                s (socket): The server socket
                c (socket): The connection socket

        Returns: 
                send_name (str): The name of the client
                rec_name (str): The name of the reciever
        """
        
        rec_name = get_name(req_array, 7+name_len, 7+receiver_len+name_len,s,c)
        send_name = get_name(req_array, 7, 7+name_len,s,c)
          
        dec_mes = get_message(req_array, name_len + receiver_len + 7, len(req_array))
    
        # stores the recieved message under the intended recievers name
        if rec_name not in messages.keys():
                # creates array if there are no messages stored for the receiver
                messages[rec_name] = [(send_name,dec_mes)]
        else:
                # if there are already messages for the reciever then new message is added to the array
                messages[rec_name].append((send_name,dec_mes))    
        return send_name, rec_name
 
def server_loop(s):
        """listens and recieves message request froma client
        
        Decodes the message request header and handles 'read' and 'create' requests

        Args:
                s (socket): The server socket  
        """

        try:
                # accepts an incoming connection request
                c, addr = s.accept() 
                # set the timeout length for the connection socket 
                c.settimeout(1)
                print ('Got connection from', addr )
                
                # recieves a message request from the connection socket
                message_req = c.recv()
                req_array = bytearray(message_req)
                
                # uses bitwise operations on the bytearray to exract the header data
                magic_no = req_array[0]<<8 | req_array[1]
                r_id = req_array[2]
                name_len = req_array[3]
                receiver_len = req_array[4]
                message_len = req_array[5]<<8 | req_array[6]
                
                # checks the validity of the recieved data
                if magic_no != 0xAE73:
                        raise ValueError("magic number incorrect")
                if r_id != 1 and r_id != 2:
                        raise ValueError("ID incorrect")
                if name_len < 1:
                        raise ValueError("Name length less than 1")
                if (r_id == 1 and receiver_len != 0) or (r_id == 2 and receiver_len < 1):
                        raise ValueError("reciever length incorrect")
                if (r_id == 1 and message_len != 0) or (r_id == 2 and message_len < 1):
                        raise ValueError("message length incorrect")  

                # if it's a create request
                if r_id == 2:
                        send_name, rec_name = create_request(req_array, name_len, receiver_len,s,c)
                        print(send_name + " has created a message for " + rec_name)
                        c.close()
                        return None
                
                # if it's a read request
                if r_id == 1:
                        sen_name, num_items, message_response = read_request(name_len, req_array, s, c)

                        # if messages are sent info message is printed and the sent messages are removed form
                        # the message dictionary
                        if num_items > 0:
                                print("sent " + str(num_items) + " messages to " + sen_name)
                        
                                # iterates though the messages stored under the receivers name and deletes each
                                # message in the range of 0 - number of messages sent
                                for i in range(num_items):
                                        messages[sen_name].pop(0) 
                        
                        # if no messages are sent
                        else:
                                print("no messages sent")      
                        # sends a message response via the connection socket
                        c.send(message_response)
                        # closes the connection socket
                        c.close()     
                        return None   
        except OSError as err:
                print("ERROR -  " + str(err))
                c.close()
                exit()
        except TimeoutError:
                print("ERROR - timed out")
                c.close()
                exit()
        except ValueError as err:
                print("ERROR -  " + str(err))
                c.close()
                exit()

def main():
        try:
                
                # server socket is created
                s = socket(AF_INET, SOCK_STREAM)     
                # socket is bound to a given port and an ip address "0.0.0.0" is used 
                # to bind to all local interfaces    
                s.bind(('0.0.0.0', port))        
                print ("socket binded to %s" %(port))

                #Listen for connection requests
                s.listen()    
                print ("socket is listening")    
                
        except OSError as err:
                print("ERROR -  " + str(err))
                s.close()
                exit()
        while True:
                server_loop(s)

main()

    
  


