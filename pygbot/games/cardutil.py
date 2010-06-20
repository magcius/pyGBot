
import random

from pygbot.util import pretty_print_list

from twisted.python import log

undealt = object()

class Deck(object):
    """
    A deck of cards.

    Decks are by definition unordered.
    """

    def __init__(self):
        self.cards = self.make_deck()

    def make_deck(self):
        """
        Initialize the deck.
        """
        return []

    def get_cards(self):
        return self._cards

    def set_cards(self, value):
        self._cards = dict()
        for card in value:
            self._cards[card] = card

    cards = property(get_cards, set_cards)

    def find_card(self, uid):
        """
        Find a card by uid.
        """
        return self._cards[uid]

    @property
    def undealt_cards(self):
        return [c for c in self._cards if c.owner is undealt]

    def __contains__(self, card):
        return card in self._cards

    def __len__(self):
        return len(self._cards)

class Card(object):
    def __init__(self, title, uid):
        """
        A card. I'm pretty sure you know what
        this is.

        What this *isn't*, is a genetic suit-face
        card. A card has a title, and a unique id
        for identification purposes, and an owner
        for gameplay purposes.
        """
        self.title = title
        self.uid   = uid
        self.owner = undealt

    def free(self):
        """
        Free the card from its owner.
        """
        self.owner.remove(self)
        self.owner = None

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return "Card(%r, uid=%t)" % (self.title, uid)

    def __str__(self):
        return self.title

    def __iter__(self):
        return iter([self])

    def __getitem__(self, i):
        if i == 0:
            return self
    
class CardPile(object):
    """
    A card pile is something that contains cards.

    It could be a player's hand, a draw or discard
    pile.

    It has a name for identification purposes.
    """
    def __init__(self, name=""):
        self.cardset = dict()
        self.cards   = []
        self.name    = name
    
    def shuffle(self):
       """
       Shuffle this pile.
       """
       random.shuffle(self.cards)

    def remove(self, card):
        """
        Remove a card from this pile.
        """
        del self.cardset[card]
        self.cards.remove(card)

    def receive(self, cards):
        """
        Receive cards.
        """
        newcards = []
        for card in cards:
            card.free()
            newcard = self.receive_accept(card)
            if card is not None:
                newcards.append(newcard)
                newcard.owner = self
                self.cards.append(newcard)
                self.cardset[newcard] = newcard
        return newcards

    def receive_accept(self, card):
        """
        Given a card, choose to accept it by returning
        what's given, replace it by returning another,
        or reject it by returning None.

        This should always be called from self.receive.
        """
        return card

    def deal(self, piles, num_cards):
        """
        Deal from this pile to another.
        """
        for pile in piles:
            pile.receive(self.draw(num_cards))

    def draw(self, num_cards):
        """
        Return num_cards cards from the top of the pile.
        """
        return self.cards[:num_cards]
    
    def __contains__(self, card):
        return card in self.cardset
    
    def __iter__(self):
        return iter(self.cards[:])

    def __repr__(self):
        return self.name or object.__repr__(self)
    
    def __str__(self):
        return pretty_print_list(self.cards)
    
    def __len__(self):
        return len(self.cards)
    
    def __getitem__(self, i):
        return self.cards[i]
    
    def find_card(self, uid):
        return self.cardset[uid]
