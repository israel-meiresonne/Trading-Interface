from model.structure.database.ModelFeature import ModelFeature as _MF


class WaitingRoom:
    def __init__(self, name: str = None):
        name = name if name is not None else _MF.new_code()
        self.__name = f"Room_{name}"
        self.__room = None

    def get_name(self) -> str:
        return self.__name

    def _get_room(self) -> list:
        if self.__room is None:
            self.__room = []
        return self.__room

    def get_tickets(self) -> list:
        return list(self._get_room())

    def _push(self, ticket: str) -> None:
        self._get_room().append(ticket)

    def _generate_ticket(self) -> str:
        return f"Ticket_{self.get_name()}_{_MF.new_code()}"

    def join_room(self) -> str:
        """
        To generate and push a new ticket in the WaitingRoom\n
        Returns
        -------
        ticket: str
            The ticket to wait your turn
        """
        ticket = self._generate_ticket()
        self._push(ticket)
        return ticket

    def quit_room(self, ticket: str) -> None:
        """
        To remove a ticket from the WaitingRoom\n
        Parameters
        ----------
        ticket: str
         The ticket to remove
        """
        room = self._get_room()
        seat = room.index(ticket)
        del room[seat]

    def my_turn(self, ticket: str) -> bool:
        """
        To check if it's ticket's turn\n
        Parameters
        ----------
        ticket: str
            The ticket to check

        Returns
        -------
            True if it's ticket's turn else false
        """
        room = self._get_room()
        if len(room) == 0:
            raise Exception("Room is empty")
        return ticket == room[0]

    def treat_ticket(self, ticket: str) -> None:
        """
        To remove ticket from the WaitingRoom when it's ticket's turn\n
        Parameters
        ----------
        ticket: str
            The ticket to treat
        """
        room = self._get_room()
        if ticket not in room:
            raise IndexError(f"This ticket '{ticket}' don't exist in this room '{self.get_name()}'")
        if not self.my_turn(ticket):
            raise Exception(f"It's not this ticket's turn '{ticket}'")
        self.quit_room(ticket)
