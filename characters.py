#!/usr/bin/python3

import random
from struct import *
import socket


class Character:
    def __init__(self, name, attack, defense, regenerate, description):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.regenerate = regenerate
        self.health = 200
        self.max_health = self.health
        self.description = description
        self.alive = True

    def get_name(self):
        return self.name

    def get_attack(self):
        return self.attack

    def get_defense(self):
        return self.defense

    def get_regenerate(self):
        return self.regenerate

    def get_health(self):
        return self.health

    def get_gold(self):
        return self.health

    def get_description(self):
        return self.description

    def regenerate(self):
        self.update_health(self.regenerate)

    def is_alive(self):
        return self.alive


    def calculate_damage(self, defense, attack):
        damage = 0
        if attack == 0:
            return 0

        elif defense == 0:
            return random.randint(1, attack)

        elif attack <= defense:
            damage = random.randint(1, attack) - (defense // attack)

        else:
            damage = random.randint(1, attack) - (attack // defense)

        if damage < 0:
            return 0
        return damage


class Player(Character):
    def __init__(self, sock, name, attack, defense, regenerate,  description):
        super().__init__(name, attack, defense, regenerate, description)
        self.sock = sock
        self.room = None
        self.flags = 200 # 0b11001000 player ready but haven't started yet
        self.gold = 15
        self.attack = attack
        self.defense = defense
        self.regenerate = regenerate
        self.health = 100
        self.playing = False
        self.description = description
        self.room_number = 0

    def __str__(self):
        s = ('Player name: %s\nAttack: %d\nDefense: %d\nRegen: %d\nHealth: %d\nGold: %d\nRoom: %d\nDescription: %s' % (self.name, self.attack, self.defense, self.regenerate,self.health, self.gold, self.room.get_room_number(),self.description))
        return s

    def get_room_number(self):
        return self.room_number

    def set_room(self, r):
        self.room = r
        self.room_number = self.room.get_room_number()

    def set_playing(self, status):
        self.playing = status
        self.flags = 216 # Player ready and started 0b11011000

    def is_playing(self):
        return self.playing

    def change_room(self, new_room):
        self.room = new_room

    def update_health(self, amount):
        if self.health + amount < 0:
            self.health = 0
            self.alive = False
            self.die()

        elif self.health + amount > self.max_health:
            self.health = self.max_health

        else:
            self.health = amount

    def fight(self, other):
        my_damage = self.calculate_damage(self.defense, other.attack)
        other_damge = self.calculate_damage(other.defense, self.attack)
        self.update_health(-my_damage)
        gold = other.update_health(-other_damge)
        if gold:
            self.gold += gold

    def get_room(self):
        return self.room

    def send_message(self, message):
        self.sock.send(message)
        return

    def recv_message(self, size):
        data = self.sock.recv(size)
        return data

    def start(self, s):
        self.sock = s
        self.playing = True

    def die(self):
        self.flags = 0

    def character_message(self):
        room_numb = self.room_number
        header = (10).to_bytes(1, "little")
        temp_name = self.name.ljust(32,'\00')
        name = temp_name.encode('utf-8')
        flags = self.flags.to_bytes(1,'little')
        attack = self.attack.to_bytes(2, 'little')
        defense = self.defense.to_bytes(2, 'little')
        regenerate = self.regenerate.to_bytes(2, 'little')
        health = self.gold.to_bytes(2, 'little')
        gold = self.gold.to_bytes(2, 'little')
        room = room_numb.to_bytes(2, 'little')
        description_length = (len(self.description)).to_bytes(2, "little")
        description = self.description.encode('utf-8')

        packet = bytearray()

        character = [header, name, flags, attack, defense, regenerate, health, gold,
                     room, description_length, description]

        for item in character:
            packet += item

        return packet

    def get_gold(self):
        return self.gold


class Monster(Character):
    def __init__(self, r, name, attack, defense, regenerate, description):
        super().__init__(name, attack, defense, regenerate, description)
        self.flags = 184
        self.gold = 100
        self.room = r
        self.name = name

    def character_message(self):
        header = (10).to_bytes(1, "little")
        temp_name = self.name.ljust(32,'\00')
        name = temp_name.encode('utf-8')
        flags = self.flags.to_bytes(1,'little')
        attack = self.attack.to_bytes(2, 'little')
        defense = self.defense.to_bytes(2, 'little')
        regenerate = self.regenerate.to_bytes(2, 'little')
        health = self.gold.to_bytes(2, 'little')
        gold = self.gold.to_bytes(2, 'little')
        room = self.room.to_bytes(2, 'little')
        description_length = (len(self.description)).to_bytes(2, "little")
        description = self.description.encode('utf-8')

        packet = bytearray()

        character = [header, name, flags, attack, defense, regenerate, health, gold,
                     room, description_length, description]

        for item in character:
            packet += item
        return packet

    def die(self):
        self.flags = 32

    def update_health(self, amount):
        if self.health + amount < 0:
            self.health = 0
            self.alive = False
            self.die()
            send_gold = self.gold
            self.gold = 0
            return send_gold

        elif self.health + amount > self.max_health:
            self.health = self.max_health
            return False

        else:
            self.health = amount
            return False