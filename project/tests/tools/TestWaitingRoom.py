import unittest

from model.tools.WaitingRoom import WaitingRoom


class TestWaitingRoom(unittest.TestCase):
    def setUp(self) -> None:
        self.room1 = WaitingRoom('Test')

    def test_get_tickets(self) -> None:
        room = self.room1
        self.assertNotEqual(id(room._get_room()), id(room.get_tickets()))

    def test_join_room(self):
        room = self.room1
        exp1 = [
            room.join_room(),
            room.join_room(),
            room.join_room()
        ]
        result1 = room._get_room()
        self.assertListEqual(exp1, result1)

    def test_quit_room(self) -> None:
        room = self.room1
        seat = 1
        exp1 = [
            room.join_room(),
            room.join_room(),
            room.join_room()
        ]
        room.quit_room(exp1[seat])
        del exp1[seat]
        result1 = room._get_room()
        self.assertListEqual(exp1, result1)

    def test_my_turn(self) -> None:
        room = self.room1
        # Room is empty
        with self.assertRaises(Exception):
            room.my_turn('')
        # Not my turn
        tickets = [
            room.join_room(),
            room.join_room(),
            room.join_room()
        ]
        self.assertFalse(room.my_turn(tickets[1]))
        # It's my turn
        self.assertTrue(room.my_turn(tickets[0]))

    def test_treat_ticket(self) -> None:
        room = self.room1
        tickets = [
            room.join_room(),
            room.join_room(),
            room.join_room()
        ]
        # Treat ticket
        exp1 = list(tickets)
        del exp1[0]
        room.treat_ticket(tickets[0])
        result1 = room._get_room()
        self.assertListEqual(exp1, result1)
        # Ticket don't exist
        with self.assertRaises(IndexError):
            room.treat_ticket(tickets[0])
        # Not my turn
        with self.assertRaises(Exception):
            room.treat_ticket(tickets[2])


if __name__ == '__main__':
    unittest.main()
