from typing import Union
from model.structure.database.ModelFeature import ModelFeature as _MF


class WaitingRoom:
    """
    This class implement a wait list\n
    Execussion:
    -----------
    >>> waitroom = WaitingRoom('RoomName')
    >>> ticket = waitroom.join_room()
    >>> waitroom.treat_ticket(ticket) if waitroom.my_turn(ticket) else None
    """

    def __init__(self, name: str = None):
        self.__name = None
        self.__room = None
        self._set_name(name)
    
    def _set_name(self, name: str = None) -> None:
        if (name is not None) and (not isinstance(name, str)):
            raise TypeError(f"The room's name must be of type str, instead type='{type(name)}'(name='{name}')")
        name = name if name is not None else _MF.new_code()
        self.__name = f"Room-{name}"

    def get_name(self) -> str:
        """
        To get WaitingRoom's name\n
        Returns:
        --------
        returrn: str
            WaitingRoom's name
        """ 
        return self.__name

    def _get_room(self) -> list:
        if self.__room is None:
            self.__room = []
        return self.__room

    def get_tickets(self) -> list:
        """
        To get list of ticket waiting in the room\n
        Returns:
        --------
        return: list
           List of ticket waiting in the room 
        """
        return self._get_room().copy()

    def _push(self, ticket: str) -> None:
        room = self._get_room()
        if ticket in room:
            raise ValueError(f"This ticket already exist in room: '{ticket}'")
        room.append(ticket)

    def _generate_ticket(self) -> str:
        return f"Ticket_{self.get_name()}_{_MF.new_code()}"

    def join_room(self, ticket: str = None) -> str:
        """
        To push a new ticket in the WaitingRoom
        NOTE: Generate a new ticket if ticket is None\n
        Parameters:
        -----------
        ticket: str = None
            The ticket to join room

        Returns
        -------
        ticket: str
            The ticket to wait your turn
        """
        None if (ticket is not None) and self._check_ticket(ticket) else None
        ticket = self._generate_ticket() if ticket is None else ticket
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
        self._check_ticket(ticket)
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
        self._check_ticket(ticket)
        room = self._get_room()
        if len(room) == 0:
            raise Exception("Room is empty")
        return ticket == room[0]
    
    def next(self) -> Union[str, None]:
        """
        To get next ticket\n
        Returns:
        --------
        return: : str|None
            Next ticket if there's one else None if empty
        """
        tickets = self.get_tickets()
        return tickets[0] if len(tickets) > 0 else None

    def treat_ticket(self, ticket: str) -> None:
        """
        To remove ticket from the WaitingRoom when it's ticket's turn\n
        Parameters
        ----------
        ticket: str
            The ticket to treat
        """
        self._check_ticket(ticket)
        room = self._get_room()
        if ticket not in room:
            raise IndexError(f"This ticket '{ticket}' don't exist in this room '{self.get_name()}'")
        if not self.my_turn(ticket):
            raise Exception(f"It's not this ticket's turn '{ticket}'")
        self.quit_room(ticket)

    @staticmethod
    def _check_ticket(ticket: str) -> bool:
        if not isinstance(ticket, str):
            raise TypeError(f"The ticket must be of type str, instead type='{type(ticket)}'(ticket='{ticket}')")
        return True
