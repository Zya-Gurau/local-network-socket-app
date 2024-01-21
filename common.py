""" Defines Classes used by Servers and Clients 

Author: Zya Gurau
"""

class MessageRequest:
    def __init__(self, id, name_len, reciever_len, message_len):
        self.index = 7
        self.name_len = name_len
        self.receiver_len = reciever_len
        self.message_len = message_len
        self.content = bytearray(7 + name_len + reciever_len + message_len)
        self.content[0] = 0xAE
        self.content[1] = 0x73
        self.content[2] = id
        self.content[3] = name_len
        self.content[4] = reciever_len
        self.content[5] = message_len >> 8
        self.content[6] = 0xff & message_len

    def add_name(self, name):
        for byte in name:
            self.content[self.index] = byte
            self.index += 1
    
    def add_reciever_name(self, name):
        for byte in name:
            self.content[self.index] = byte
            self.index += 1
    
    def add_message(self, message):
        for byte in message:
            self.content[self.index] = byte
            self.index += 1

class MessageResponse:
    def __init__(self, num_items, more_msgs):
        self.content = bytearray(5)
        self.content[0] = 0xAE
        self.content[1] = 0x73
        self.content[2] = 3
        self.content[3] = num_items
        self.content[4] = more_msgs

    def add_message(self, sender_name, message):
        self.content.append(len(sender_name))
        self.content.append(len(message)>>8)
        self.content.append(0xff & len(message)) 

        for byte in sender_name:
            self.content.append(byte)
        for byte in message:
            self.content.append(byte)



        