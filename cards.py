import random 

class Card(object):
    """Represents a standard playing card.
    
    Attributes:
      suit: integer 0-3
      rank: integer 1-13
    """

    suit_names = ["Clubs", "Diamond", "Hearts", "Spades"]
    rank_names = [None, "Ace", "2", "3", "4", "5", "6", "7", 
              "8", "9", "10", "Jack", "Queen", "King"]

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank 
        self.value = rank if rank < 10 else 10


    def __str__(self):
        """Returns a human-readable string representation."""
        return Card.rank_names[self.rank] + " of " + Card.suit_names[self.suit]

    def __cmp__(self, other, check_suit=False):
        """Compares this card to other, first by suit, then rank.

        Returns a positive number if this > other; negative if other > this;
        and 0 if they are equivalent.
        """
        if check_suit:
            t1 = self.suit, self.rank
            t2 = other.suit, other.rank
            return cmp(t1, t2)
        else:
            return self.rank - other.rank

class Deck(object):
    """Represents a deck of cards.

    Attributes:
      cards: list of Card objects.
    """
    
    def __init__(self, num_decks=1):
        self.cards = []
        for decks in range(num_decks):
            for suit in range(4):
                for rank in range(1,14):
                    card = Card(suit, rank)
                    self.cards.append(card)

    def __str__(self):
        res = []
        for card in self.cards:
            res.append(str(card))
        return '\n'.join(res)

    def add_card(self, card):
        """Adds a card to the deck."""
        self.cards.append(card)

    def remove_card(self, card):
        """Removes a card from the deck."""
        self.cards.remove(card)

    def pop_card(self, i=0):
        """Removes and returns a card from the deck.

        i: index of the card to pop; by default, pops the last card.
        """
        return self.cards.pop(i)

    def shuffle(self):
        """Shuffles the cards in this deck."""
        random.shuffle(self.cards)

    def sort(self):
        """Sorts the cards in ascending order."""
        self.cards.sort()

    def move_cards(self, hand, num):
        """Moves the given number of cards from the deck into the Hand.

        hand: destination Hand object
        num: integer number of cards to move
        """
        for i in range(num):
            hand.add_card(self.pop_card())

    def get_cards(self):
        return self.cards

    def cards_left(self):
        return len(self.cards)


class Hand(Deck):
    """Represents a hand of playing cards."""
    
    def __init__(self, label=''):
        self.cards = []
        self.label = label

    def __str__(self):
        return self.label + "'s hand: " + str([str(c) for c in self.cards])





