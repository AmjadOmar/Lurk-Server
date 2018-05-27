#!/usr/bin/python3
import socket
import threading
from characters import *
from room import *
from struct import *


class Game:

    def __init__(self):
        self.rooms = {}
        self.players = {}
        self.error_message = {}
        self.description = 'You have entered the house of ghosts and monsters!'
        self.initial = None
        self.stat_limit = 150
        self.playing = False
        self.lock = threading.RLock()
        self.game_set_up()

    def send_game_description(self):
        packet = bytearray()
        aList = [(11).to_bytes(1, "little"),
                 (150).to_bytes(2, "little"),
                 self.stat_limit.to_bytes(2, "little"),
                 (len(self.description)).to_bytes(2, "little"),
                 self.description.encode('utf-8')]

        for item in aList:
            packet += item

        return packet

    def send_error_message(self, err):
        packet = bytearray()
        length = len(self.error_message[err])
        aList = [(7).to_bytes(1, "little"),
                 err.to_bytes(1, "little"), # Error code
                 length.to_bytes(2, "little"),
                 self.error_message[err].encode('utf-8')]

        for item in aList:
            packet += item

        print("Error message number %d sent " % err)

        return packet

    def start_player(self, s):
        name = ""
        is_set = False
        print("start_player called...")
        entrance_message = self.send_game_description()
        s.send(entrance_message)
        while not is_set:
            header = s.recv(1)
            print(header[0])

            if header[0] != 10:
                err = self.send_error_message(5)
                s.send(err)

            temp_name = s.recv(32)
            name = temp_name.decode('utf')

            flag = s.recv(1)
            print("Flags: ", flag)
            f = int.from_bytes(flag, 'little')
            #print("Translated flags = %d %s" % (f, bin(f)))

            attack = s.recv(2)
            attack = int.from_bytes(attack, 'little')

            defense = s.recv(2)
            defense = int.from_bytes(defense, 'little')

            regen = s.recv(2)
            regen = int.from_bytes(regen,'little')

            garbage = s.recv(6)

            desc_len = s.recv(2)
            desc_length = int.from_bytes(desc_len, 'little')

            description_l = s.recv(desc_length)
            description = description_l.decode('utf-8')

            if name in self.players:
                err = self.send_error_message(2)
                s.send(err)
                s.close()

            if attack + defense + regen > self.stat_limit:
                err = self.send_error_message(4)
                s.send(err)
            else:
                with self.lock:
                    player = Player(s, name, attack, defense, regen, description)
                    player.set_room(self.initial)
                    self.players[name] = player
                    print("Player created and added to the Players dictionary.. OK")
                    print(player)
                    is_set = True
                    message = bytearray()
                    header = (8).to_bytes(1, 'little')
                    type = (10).to_bytes(1, 'little')
                    message += header
                    message += type
                    s.send(message)
                    print(message)
                self.play_game(player)

    def play_game(self, player):
        print("\nPlaying game with player %s" % player.get_name())

        while True:
            print("Entering while True loop")
            header = player.recv_message(1)
            print("Recieved %d" % header[0])
            type = int.from_bytes(header, 'little')
            if type == 1:
                print("MESSAGE was sent")
                self.message_player(player)
            elif type == 10:
                print("character update called")
            elif type == 6:
                self.message_six(player)
            elif type == 2:
                print("CHANGEROOM called")
                if player.playing and player.alive:
                    room_number = player.recv_message(2)
                    room_number = int.from_bytes(room_number, 'little')
                    self.move_player(player, room_number)
                else:
                    err = self.send_error_message(5)
                    player.send_message(err)
            elif type == 3:
                with self.lock:
                    print("FIGHT message sent")
                    if player.playing and player.alive:
                        #try:
                        #    num = player.room.room_number
                        #except:
                        #    print("Eroor room number")
                        print(player.room)
                        r = self.rooms.get(player.get_room_number())
                        r.player_fight_monsters(player)
                        print("player snt to fight")
                        player_info = player.character_message()
                        player.send_message(player_info)
                        print(player_info)
                    else:
                        err = self.send_error_message(7)
                        player.send_message(err)
            elif type == 4:
                print("PVP message sent")
                target = player.recv_message(32)
                target = target.decode('utf-8')
                num = player.room.get_room_number()
                r = self.rooms.get(num)
                pvp = r.player_fight_player(player, target)
                print("player pvp target")
                player_info = player.character_message()
                player.send_message(player_info)
                print(player_info)
                if not pvp:
                    err = self.send_error_message(7)
                    player.send_message(err)
            elif type == 5:
                print("LOOT message sent")
                target = player.recv_message(32)
                target = target.decode('utf-8')
                loot = self.loot(player, target)
                if loot:
                    player.send_message(player.character_message())
                else:
                    err = self.send_error_message(6)
                    player.send_message(err)

            elif type == 12:
                print("LEAVE message sent")
                player.sock.close()
            else:
                print("Not implemented yet....")

    def message_six(self,player):
        print("inside 6")
        message = bytearray()
        header = (8).to_bytes(1, 'little')
        type = (10).to_bytes(1, 'little')
        message += header
        message += type
        player.send_message(message)
        player.set_playing(True)
        player_info = player.character_message()
        r = player.get_room()
        player.send_message(player_info)
        room_info = r.get_room_info()
        players_info = r.players_info()
        monsters_info = player.room.get_monster_info()
        room_conn = player.room.get_room_connections()
        print("Room info:")
        print(room_info)
        print("players in room info:")
        print(players_info)
        print("Monsters info:")
        print(monsters_info)
        print("room connections:")
        print(room_conn)
        print("About to send info")
        player.send_message(room_info)
        for info in players_info:
            player.send_message(info)
        print("players_info sent")
        for m in monsters_info:
            player.send_message(m)
        for con in room_conn:
            player.send_message(con)
        r = player.get_room()
        r.add_player(player)
        print("Player %s started playing" % player.get_name())
        return

    def loot(self, player, target):
        target = self.players[target]
        if not target.alive:
            player.gold += target.get_gold()
            return True
        else:
            return False

    def message_player(self, player):
        with self.lock:
            type = 1
            message_length = player.recv_message(2)
            recipient_name = player.recv_message(32)
            sender_name = player.recv_message(32)
            length = int.from_bytes(message_length, 'little')
            message = player.recv_message(length)

            packet = bytearray()
            header = type.to_bytes(1, 'little')
            packet.extend(header)
            packet.extend(message_length)
            packet.extend(recipient_name)
            packet.extend(sender_name)
            packet.extend(message)

            name = recipient_name.decode('utf-8')
            print("message to : %s" % name)
            p2 = self.players.get(name) # python3 get value from dictionry by key
            p2.send_message(packet)
            message = bytearray()
            header = (8).to_bytes(1, 'little')
            type = (1).to_bytes(1, 'little')
            message += header
            message += type
            player.send_message(message)

    def move_player(self, player, room):
        with self.lock:
            r = self.rooms.get(player.get_room_number())
            print(r)
            r.remove_player(player)
            r.add_player(player)
            player.change_room(room)
            infos = self.rooms[room].all_room_info()
            for info in infos:
                player.send_message(info)


    def send_all_info(self,player):
        with self.lock:
            r = player.get_room()
            #info =

    def game_set_up(self):

        self.description += '''\nGame Rules:\n1- You can message other players by sending MESSAGE message.
        \n2- You can change room by sending CHANGEROOM message.
        \n3- You can fight the monster in the room by sending FIGHT message. If you kill him you will earn his gold and vice versa
        \n4- You can fight other players in the room by sending PVPFIGHT message. If you kill him you will earn his gold and vice versa
        \n5- You can loot a dead players by sending LOOT message
        \n6- Start the game by sending START message.
        \n7- You can leave the game by sending  LEAVE message.
        \n8- Every room has amount of gold might be hidden or stated in room description. Once you kill the monster in the room you will earn that gold.
        \n This game is intend to fully implementing LURK 2.0 protocol
        \n\n Try to find your way to VIP Lounge. Pay attention to room's description'''

        self.error_message[0] = "Other (not covered by any other error code)"
        self.error_message[1] = "Bad room. Attempt to change to an inappropriate room"
        self.error_message[2] = "Player Exists. Attempt to create a player that already exists."
        self.error_message[3] = "Bad Monster. Attempt to loot a nonexistent or not present monster.."
        self.error_message[4] = "Stat error. Caused by setting inappropriate player stats."
        self.error_message[5] = "Not Ready. Caused by attempting an action too early."
        self.error_message[6] = "No target. Sent in response to attempts to loot nonexistent players."
        self.error_message[7] = "No fight."
        self.error_message[8] = "No player vs. player combat on the server."

        entrance = Room(1, "Entrance Room".ljust(32,'\00'), "Entrance room. Thee are a strong monster here to welcome you. 100 gold in here.", 100)
        bridge = Room(2, "Bridge".ljust(32,'\00'), "The bridge between rooms. Contains gold and monster. 200 gold", 200)
        rec_center = Room(3, "Recreational Center".ljust(32,'\00'), "Here you will find monsters and gold. 300 gold", 300)
        basement = Room(4, "Basement".ljust(32,'\00'), "Tha basement of the house a hidden monsters might be here",300)
        horse_barn = Room(5, "Horse Barn".ljust(32,'\00'), "The horse barn where my great grandpas horse ghost come to hunt me because he know what I did in summer 96", 600)
        elevator = Room(6, "Elevator".ljust(32,'\00'), "Your gateway to second floor and more gold.", 450)
        living_room = Room(7, "Living room".ljust(32,'\00'), "A place to chill and hide stuff", 550)
        transport = Room(8, "Transporter Room".ljust(32,'\00'), "To be filled later", 400)
        hallway = Room(9, "Hallway".ljust(32,'\00'), "A long hallway, with many frenemies ", 500)
        theatre = Room(10, "Home Theatre".ljust(32,'\00'), "A place to chill, also for vip entrance.", 1000)
        vip = Room(11, "VIP Central".ljust(32,'\00'), "Congratulation !! now kill the freak and earn 2000 gold plates!!", 2000)

        self.initial = entrance

        for room in [entrance, bridge, rec_center, basement, horse_barn, elevator, living_room, transport,
                 hallway, theatre, vip]:
            self.rooms[room.get_room_number()] = room

        entrance.add_monster(Monster(1,"Beast of Gevaudan", 200, 100, 50, "The man-eating gray wolf, dog or wolfdog"))
        bridge.add_monster(Monster(2,"Ghost of Arabia", 30,150, 200, "The ghost of arabia, strong and rich"))
        rec_center.add_monster(Monster(3,"Behemoth", 100, 240, 30, "The Devil, from before creation who will finally be defeated."))

        basement.add_monster(
            Monster(4, "Chimera", 200, 100, 40, "A lion, with the head of a goat arising from its back, and a tail that might end with a snake's head"))

        horse_barn.add_monster(
            Monster(5, "Demon", 20, 130, 100, "A supernatural and often malevolent being prevalent in religion, occultism, literature, fiction, mythology and folklore.!"))
        elevator.add_monster(Monster(6,"Frankenstein", 100, 100, 100, "Frankenstein's monster, often erroneously referred to as Frankenstein, is a fictional character who first appeared in Mary Shelley's 1818 novel Frankenstein; or, The Modern Prometheus."))
        living_room.add_monster(Monster(7, "Dragon", 30, 20, 75, "A large, serpent-like legendary creature that appears in the folklore of many cultures around world. "))

        transport.add_monster(Monster(8, "Ghoul", 70, 60, 80, "A ghoul is a demon or monster in Arabian mythology, associated with graveyards and consuming human flesh."))
        hallway.add_monster(Monster(9,"Centaur", 100,50,30, "A centaur or occasionally hippocentaur, is a mythological creature with the upper body of a human and the lower body and legs of a horse."))
        theatre.add_monster((Monster(10,"Ogre", 70, 100, 30, "An ogre is a legendary monster usually depicted as a large, hideous, man-like being that eats ordinary human beings, especially infants and children.")))
        vip.add_monster((Monster(11,"Freak", 110, 60, 80, "A freak is someone with something strikingly unusual about their appearance or behaviour.")))

        entrance.add_connection(horse_barn)
        entrance.add_connection(rec_center)
        entrance.add_connection(basement)
        entrance.add_connection(bridge)

        bridge.add_connection(entrance)
        bridge.add_connection(rec_center)

        rec_center.add_connection(bridge)
        rec_center.add_connection(elevator)
        rec_center.add_connection(horse_barn)

        basement.add_connection(rec_center)
        basement.add_connection(entrance)
        basement.add_connection(elevator)

        horse_barn.add_connection(entrance)
        horse_barn.add_connection(rec_center)

        elevator.add_connection(living_room)
        elevator.add_connection(transport)
        elevator.add_connection(hallway)
        elevator.add_connection(theatre)

        living_room.add_connection(elevator)
        living_room.add_connection(hallway)
        living_room.add_connection(transport)

        transport.add_connection(living_room)
        transport.add_connection(elevator)
        transport.add_connection(hallway)

        hallway.add_connection(transport)
        hallway.add_connection(theatre)

        theatre.add_connection(hallway)
        theatre.add_connection(vip)
        theatre.add_connection(elevator)

        vip.add_connection(theatre)
        




