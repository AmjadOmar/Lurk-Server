#!/usr/bin/python3


class Room:
    def __init__(self, room_number, name, description, gold):
        self.room_number = room_number
        self.name = name
        self.description = description
        self.gold = gold
        self.monsters = []
        self.players = {}
        self.connections = {}

    def get_room_number(self):
        return self.room_number

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_gold(self):
        return self.gold

    def message_all(self,message):
        for name in self.players:
            player = self.players[name]
            player.send_message(message)

    def add_player(self, player):
        if player.get_name() not in self.players:

            character = player.character_message()
            self.message_all(character)

            self.players[player.get_name()] = player

    def remove_player(self, player):
        self.players.pop(player.get_name(), None)

    def add_monster(self, monster):
        self.monsters.append(monster)

    def add_connection(self, room):
        self.connections[room.get_room_number()] = room

    def remove_connection(self, room):
        del self.connections[room.get_room_number()]

    def has_connection(self, room):
        if room.get_room_number() in self.connections:
            return True
        else:
            return False

    def player_fight_player(self, p1, p2):
        player = p1
        target = p2
        target = self.players.get(target)
        if (player.get_name() in self.players) and (target.get_name() in self.players) and target.alive:
            player.fight(target)
            if not target.alive:
                player.gold += target.gold
                target.gold = 0
            elif not player.alive:
                target.gold += player.gold
                player.gold = 0
            return True
        else:
            return False

    def player_fight_monsters(self, player):
        if (self.monsters == {}) or (player.get_name() not in self.players):
            print("Exist fight error")
            return False

        for monster in self.monsters:
            if monster.alive:
                player.fight(monster)
                if not monster.alive:
                    player.gold += self.gold

        print("Player %s fought %s" % (player.get_name(), monster.get_name()))

        if monster.get_name() == 'Freak' and not monster.alive:
            player.send_message(self.room_message(player.get_name()))


        infos = self.all_room_info()

        for info in infos:
            player.send_message(info)

        return True

    def room_message(self,recv_name):
        type = 1
        name = "Server".ljust(32)
        message = 'In 4th July, 1996, I burned my grandpa horse barn by playing with Fireworks. I blamed it on the neighbors'
        message_len = len(message)
        recipient_name = recv_name.ljust(32)

        packet = bytearray()
        header = type.to_bytes(1, 'little')
        message_len = message_len.to_bytes(2,'little')
        recipient_name = recipient_name.encode('utf-8')
        sender_name = name.encode('utf-8')
        message = message.encode('utf-8')

        packet.extend(header)
        packet.extend(message_len)
        packet.extend(recipient_name)
        packet.extend(sender_name)
        packet.extend(message)

        return packet


    def players_info(self):
        packet = bytearray()
        infos = []
        for name in self.players:
            player = self.players[name]
            info = player.character_message()
            infos.append(info)

        for info in infos:
            packet += info

        return infos

    def get_monster_info(self):
        packet = bytearray()
        infos = []
        for monster in self.monsters:
            m = monster.character_message()
            infos.append(m)
        print("Monster")
        for info in infos:
            packet += info
        return infos

    def get_room_connections(self):
        conn_list = []
        for r in self.connections.values():
            temp_num = r.get_room_number()
            temp_name = r.get_name()
            temp_desc = r.get_description()
            temp_desc_len = len(temp_desc)
            type = 13
            print("get_room_connections() called....")
            conn_list.extend([(type).to_bytes(1, "little"),
                     temp_num.to_bytes(2, "little"),
                     temp_name.encode('utf-8'),
                     temp_desc_len.to_bytes(2, "little"),
                     temp_desc.encode('utf-8')])


        #room_number = 2
        #room_name = "Bridge".ljust(32,'\00')
        #room_desc = "To be filled later"
        #desc_len = len(room_desc)
        '''
        packet = bytearray()
        infos = [(type).to_bytes(1, "little"),
                 room_number.to_bytes(2, "little"),
                 room_name.encode('utf-8'),
                 desc_len.to_bytes(2, "little"),
                 room_desc.encode('utf-8')]

        # packing room infos
        for info in infos:
            packet += info
        '''

        print("Print from inside get_room_connections()")

        return conn_list


    def get_room_info(self):
        print("get_room_info() called....")
        packet = bytearray()
        infos = [(9).to_bytes(1, "little"),
                 self.room_number.to_bytes(2, "little"),
                 self.name.encode('utf-8'),
                 len(self.description).to_bytes(2, "little"),
                 self.description.encode('utf-8')]

        # packing room infos
        for info in infos:
            packet += info

        #print(packet)
        return packet

    def all_room_info(self):
        packet = []
        # get player character message first message 10
        players = self.players_info()

        monsters = self.get_monster_info()

        for p in players:
            packet.append(p)

        for mo in monsters:
            packet.append(mo)

        # send message 9 room info
        room = self.get_room_info()

        packet.append(room)

        # message 13 room connections
        conn = self.get_room_connections()
        print("room connections sent...")

        for c in conn:
            packet.append(c)
        print(packet)
        return packet










