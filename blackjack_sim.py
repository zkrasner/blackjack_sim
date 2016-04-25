from cards import Card, Deck, Hand
import random

debug = True

class Table(object):

    def __init__(self, minimum=1, maximum=500, payout=1, hit_soft_17=True, 
                 insurance_allowed=True, insurance_payout=2,
                 num_decks=6, reshuffle_each_hand=True,
                 blackjack_payout=1.5, max_split_hands=3, 
                 surrender_allowed=True, hit_split_ace=False,
                 resplit_aces=False, split_A10_is_blackjack=False,
                 double_after_split=False, double_after_hit= False):
        # Establish table rules
        self.min = minimum if minimum > 0 else 1
        self.standard_bet = self.min
        self.max = maximum if maximum > minimum else 500
        self.payout = payout if payout > 0 else 1
        self.hit_soft_17 = hit_soft_17
        self.insurance_allowed = insurance_allowed
        self.insurance_payout = insurance_payout if insurance_payout > 0 else 2
        self.num_decks = num_decks if num_decks > 0 else 6
        self.reshuffle_each_hand = reshuffle_each_hand
        self.blackjack_payout = blackjack_payout if blackjack_payout > 0 else 1.5
        self.max_split_hands = max_split_hands if max_split_hands >= 2 else 3
        self.surrender_allowed = surrender_allowed
        self.hit_split_ace = hit_split_ace
        self.resplit_aces = resplit_aces
        self.split_A10_is_blackjack = split_A10_is_blackjack
        self.double_after_split = double_after_split
        self.double_after_hit = double_after_hit
        
        # Initialize necessary variables
        if debug:
            print "Established table"
        self.init_deck()
        self.dealer_hand = Hand("Dealer")
           
    def init_deck(self):
        self.deck = Deck(self.num_decks)
        self.deck.shuffle()

    def buy_in(self, name, chips, bet_method, play_method):
        if debug:
            print name + " bought into the table with $" + str(chips)
        self.player_name = name
        self.player_chips = chips
        self.player_hands = [Hand(name)]
        self.player_surrendered = False
        self.bets = []
        self.win_streak = 0
        self.in_play = [False]
        self.bet_method = bet_method
        self.play_method = play_method
        self.doubled = [False]

    def add_funds(self, chips):
        self.player_chips = self.player_chips + chips

    def __str__(self):
        if len(self.dealer_hand.cards) > 0:
            ret = "Dealer is showing: " + str(self.dealer_hand.cards[0]) + "\n"
            for h in range(len(self.player_hands)):
                ret = ret + str(self.player_hands[h]) + " w/ value " + str(hand_value(self.player_hands[h])) + " and $" + str(self.bets[h]) + " bet"
            return ret
        else:
            return "Waiting for hand to be dealt\n"

    def deal(self):
        if self.reshuffle_each_hand or self.deck.cards_left() < 4:
            # if debug:
                # print "Shuffling decks"
            self.init_deck()
        # if debug:
            # print "Dealing"
        self.deck.move_cards(self.dealer_hand, 2)
        self.deck.move_cards(self.player_hands[0], 2)
        self.player_hands[0].sort()
        self.in_play[0] = True

    def get_bets(self):
        bet = self.bet_method(self.player_chips)
        if bet == "rebet":
            self.place_bet(self.standard_bet)
        else:
            while not self.place_bet(bet):
                bet = self.bet_method()
                if bet == "rebet":
                    self.place_bet(self.standard_bet)

    def place_bet(self, bet):
        if bet < self.min:
            if debug:
                print "Must bet at least the minimum: " + str(self.min)
            return False
        elif bet > self.max:
            if debug:
                print "Must bet less than the maximum: " + str(self.max)
            return False
        elif bet > self.player_chips:
            if debug:
                print "Don't have funds to place bet. Current chip count: " + str(self.player_chips)
            return False
        else:
            self.bets.append(bet)
            self.doubled.append(False)
            self.player_chips = self.player_chips - bet
            self.standard_bet = bet
            if debug:
                print self.player_name + " placed bet: " + str(bet)
        return True

    def handle_player(self):
        while any(self.in_play):
            for h in range(len(self.in_play)):
                if self.in_play[h]:
                    break
            hand = self.player_hands[h]
            completed_hand = False
            minimum, maximum = hand_value(hand)
            if minimum == 21 or maximum == 21:
                completed_hand = True
                self.in_play[h] = False
            dealer_min, dealer_max = hand_value(self.dealer_hand)
            if dealer_max == 21:
                completed_hand = True
                self.in_play[h] = False
            while not completed_hand:
                insurance = False
                surrender = False
                split = False
                double = False
                stand = True
                hit = True
                if len(hand.cards) == 2:
                    if self.dealer_hand.cards[0].rank == 1:
                        insurance = True
                    if len(self.player_hands) == 1:
                        surrender = True
                    double = True
                if hand.cards[0].rank == hand.cards[1].rank:
                    if h == 0 or ((h > 0 and hand.cards[0].rank != 1) or (self.resplit_aces and hand.cards[0].rank == 1)):
                        if len(self.player_hands) < self.max_split_hands: 
                            split = True
                possible_plays = [insurance, surrender, split, double, stand, hit]
                choice = self.play_method(self.dealer_hand.cards[0], hand, possible_plays)
                if choice == "dh":
                    choice = "d" if double else "h"
                if choice == "ds":
                    choice = "d" if double else "s"
                if choice == "rh":
                    if not surrender:
                        choice = "h"
                if choice == "sp" or choice == "split":
                    choice = "h"

                if choice == "hit" or choice == "h":
                    self.hit(hand)
                elif choice == "split" or choice == "sp":
                    if split:
                        self.split(hand, self.bets[h])
                    elif hand.cards[0].rank == 1:
                        if debug:
                            print "Can't split on split Aces"
                    elif len(self.player_hands) == self.max_split_hands:
                        if debug:
                            print "Can't split hands more than " + str(self.max_split_hands) + " times"
                    else:
                        if debug:
                            print "Can only split on matching cards"
                elif choice == "double" or choice == "d":
                    self.double(h)
                elif choice == "stand" or choice == "s":
                    completed_hand = True
                    self.in_play[h] = False
                elif choice == "rh":
                    self.player_surrendered = True
                    completed_hand = True
                    self.in_play[h] = False
                else:
                    if debug:
                        print "Invalid operation"
                minimum, maximum = hand_value(hand)
                if minimum > 21:
                    completed_hand = True
                    self.in_play[h] = False

    def hit(self, hand):
        self.deck.move_cards(hand, 1)
        minimum, maximum = hand_value(hand)
        if debug:
            print str(hand) + " " + str((minimum, maximum))
        if minimum > 21:
            if debug:
                print "Busted...\n"

    def split(self, hand, bet):
        new_hand = Hand("Split")
        new_hand.add_card(hand.cards[1])
        hand.remove_card(hand.cards[1])
        self.deck.move_cards(hand, 1)
        self.deck.move_cards(new_hand, 1)
        self.player_hands.append(new_hand)
        self.player_chips = self.player_chips - bet
        self.bets.append(bet)
        self.in_play.append(True)

    def double(self, hand_index):
        self.player_chips = self.player_chips - self.bets[hand_index]
        self.bets[hand_index] = 2 * self.bets[hand_index]
        self.doubled[hand_index] = True
        self.hit(self.player_hands[hand_index])

    def handle_dealer(self):
        if debug:
            print str(self.dealer_hand) + str(hand_value(self.dealer_hand))
        minimum, maximum = hand_value(self.dealer_hand)

        if maximum == 21:
            if debug:
                print "Dealer hit blackjack..."
        elif maximum > 17:
            if debug:
                print "Dealer stands"
        else:
            while maximum < 17 or (minimum + 10 <= 17  and [c.rank for c in self.dealer_hand.cards].count(1) >= 1):
                if debug:
                    print "Dealer hits"
                self.deck.move_cards(self.dealer_hand, 1)
                if debug:
                    print str(self.dealer_hand) + str(hand_value(self.dealer_hand))
                minimum, maximum = hand_value(self.dealer_hand)

    def check_bets(self):
        wins = 0
        pushes = 0
        losses = 0
        dealer_min, dealer_max = hand_value(self.dealer_hand)
        dealer_bust = False
        if dealer_min > 21:
            dealer_bust = True
            if debug:
                print "Dealer Busted!"
        for h in range(len(self.player_hands)):
            if self.player_surrendered:
                if debug:
                    print "Player surrendered"
                self.player_chips = self.player_chips + 0.5 * self.bets[h]
                self.player_surrendered = False
                losses = 1
                break
            hand = self.player_hands[h]
            minimum, maximum = hand_value(hand)
            if minimum == 21 or maximum == 21:
                if len(self.player_hands) == 1 and len(hand.cards) == 2:
                    if dealer_max == 21 and len(self.dealer_hand.cards) == 2:
                        if debug:
                            print str(hand) + " hit Blackjack but so did dealer, so a push"
                        self.player_chips = self.player_chips + self.bets[h]
                        pushes = pushes + 1
                    else:
                        if debug:
                            print str(hand) + " hit Blackjack!"
                        self.player_chips = self.player_chips + 5*self.bets[h]/2
                        wins = wins + 1
                        if self.doubled[h]:
                            wins = wins + 1
                else:
                    if dealer_max == 21 and len(self.dealer_hand.cards) == 2:
                        if debug:
                            print str(hand) + " hit 21 but so did dealer, so a push"
                        self.player_chips = self.player_chips + self.bets[h]
                        pushes = pushes + 1
                    else:
                        if debug:
                            print str(hand) + " hit 21!"
                        self.player_chips = self.player_chips + 2*self.bets[h]
                        wins = wins + 1
                        if self.doubled[h]:
                            wins = wins + 1
            elif dealer_bust and minimum < 21:
                if debug:
                    print str(hand) + " wins " + str(self.bets[h])
                self.player_chips = self.player_chips + 2*self.bets[h]
                wins = wins + 1
                if self.doubled[h]:
                    wins = wins + 1
            else:
                if dealer_max > 22:
                    dealer_max = dealer_min
                if maximum > 21:
                    maximum = minimum
                if maximum < 21:
                    if maximum > dealer_max:
                        if debug:
                            print str(hand) + " wins " + str(self.bets[h])
                        self.player_chips = self.player_chips + 2*self.bets[h]
                        wins = wins + 1
                        if self.doubled[h]:
                            wins = wins + 1
                    elif maximum == dealer_max:
                        if debug:
                            print str(hand) + " pushed"
                        self.player_chips = self.player_chips + self.bets[h]
                        pushes = pushes + 1
                    else:
                        if debug:
                            print str(hand) + " lost"
                        losses = losses + 1
                else: 
                    if debug:
                        print str(hand) + " busted and lost"
                    losses = losses + 1
        if losses == 0:
            self.win_streak = self.win_streak + wins
        else:
            self.win_streak = 0
        self.reset()
        

    def reset(self):
        self.player_hands = [Hand(self.player_name)]
        self.in_play = [True]
        self.doubled = [False]
        self.dealer_hand = Hand("Dealer")
        self.bets = []
        self.init_deck()

################################End of Table Class#############################

def basic_strategy(dealer_showing, hand, possible_plays):
    basic = {}     # 2    3    4    5    6    7    8    9    10   A              
    basic["17+"] = ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"]
    basic["16"] =  ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"]
    basic["15"] =  ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"]
    basic["14"] =  ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"]
    basic["13"] =  ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"]
    basic["12"] =  ["h", "h", "s", "s", "s", "h", "h", "h", "h", "h"]
    basic["11"] =  ["dh","dh","dh","dh","dh","dh","dh","dh","dh","dh"]
    basic["10"] =  ["dh","dh","dh","dh","dh","dh","dh","dh", "h", "h"]
    basic["9"]  =  ["h","dh","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["8"]  =  ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"]
    basic["7"]  =  ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"]
    basic["6"]  =  ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"]
    basic["5"]  =  ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"]
    basic["A10"] = ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"]
    basic["A9"] =  ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"]
    basic["A8"] =  ["s", "s", "s", "s","ds", "s", "s", "s", "s", "s"]
    basic["A7"] =  ["ds","ds","ds","ds","ds", "s", "s", "h", "h", "h"]
    basic["A6"] =  ["h","dh","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["A5"] =  ["h", "h","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["A4"] =  ["h", "h","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["A3"] =  ["h", "h", "h","dh","dh", "h", "h", "h", "h", "h"]
    basic["A2"] =  ["h", "h", "h","dh","dh", "h", "h", "h", "h", "h"]
    basic["AA"] =  ["sp","sp","sp","sp","sp","sp","sp","sp","sp","sp"]
    basic["1010"]= ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"]
    basic["99"] =  ["sp","sp","sp","sp","sp","s", "sp","sp", "s", "s"]
    basic["88"] =  ["sp","sp","sp","sp","sp","sp","sp","sp","sp","sp"]
    basic["77"] =  ["sp","sp","sp","sp","sp","sp","h", "h", "h", "h"]
    basic["66"] =  ["sp","sp","sp","sp","sp","h", "h", "h", "h", "h"]
    basic["55"] =  ["d", "d", "d", "d", "d", "d", "d", "d", "h", "h"]
    basic["44"] =  ["h", "h", "h", "sp","sp","h", "h", "h", "h", "h"]
    basic["33"] =  ["h", "h", "sp","sp","sp","sp","h", "h", "h", "h"]
    basic["22"] =  ["h", "h", "sp","sp","sp","sp","h", "h", "h", "h"]
    
    player_key, dealer_index = translate_hands(dealer_showing, hand)
    if debug:
        print player_key, dealer_index, basic[player_key][dealer_index]
    choice = basic[player_key][dealer_index]
    if choice == "sp" and not split:
        choice = "h"
    return choice

def laszlo(dealer_showing, hand, possible_plays):
    basic = {}     # 2    3    4    5    6    7    8    9    10   A              
    basic["17+"] = ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"]
    basic["16"] =  ["s", "s", "s", "s", "s", "h", "h","rh","rh","rh"]
    basic["15"] =  ["s", "s", "s", "s", "s", "h", "h", "h","rh", "h"]
    basic["14"] =  ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"]
    basic["13"] =  ["s", "s", "s", "s", "s", "h", "h", "h", "h", "h"]
    basic["12"] =  ["h", "h", "s", "s", "s", "h", "h", "h", "h", "h"]
    basic["11"] =  ["h","dh","dh","dh","dh","dh","dh", "h", "h", "h"]
    basic["10"] =  ["h","dh","dh","dh","dh","dh", "h", "h", "h", "h"]
    basic["9"]  =  ["h","dh","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["8"]  =  ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"]
    basic["7"]  =  ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"]
    basic["6"]  =  ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"]
    basic["5"]  =  ["h", "h", "h", "h", "h", "h", "h", "h", "h", "h"]
    basic["A10"] = ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"]
    basic["A9"] =  ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"]
    basic["A8"] =  ["s", "s", "s", "s","ds", "s", "s", "s", "s", "s"]
    basic["A7"] =  ["ds","s", "s","ds","ds", "s", "s", "h", "h", "s"]
    basic["A6"] =  ["h","dh","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["A5"] =  ["h", "h","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["A4"] =  ["h", "h","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["A3"] =  ["h", "h","dh","dh","dh", "h", "h", "h", "h", "h"]
    basic["A2"] =  ["h", "h", "h", "h","dh", "h", "h", "h", "h", "h"]
    basic["AA"] =  ["sp","sp","sp","sp","sp","sp","sp","sp","sp","sp"]
    basic["1010"]= ["s", "s", "s", "s", "s", "s", "s", "s", "s", "s"]
    basic["99"] =  ["sp","sp","sp","sp","sp","s", "s","sp", "s", "s"]
    basic["88"] =  ["sp","sp","sp","sp","sp","sp","sp","rh","rh","rh"]
    basic["77"] =  ["sp","sp","sp","sp","sp","sp","h", "h", "h", "h"]
    basic["66"] =  ["sp","sp","sp","sp","sp","h", "h", "h", "h", "h"]
    basic["55"] =  ["h", "d", "d", "d", "d", "d", "h", "h", "h", "h"]
    basic["44"] =  ["h", "h", "h", "sp","sp","h", "h", "h", "h", "h"]
    basic["33"] =  ["h", "h", "sp","sp","sp","sp","h", "h", "h", "h"]
    basic["22"] =  ["h", "h", "sp","sp","sp","sp","h", "h", "h", "h"]
    
    player_key, dealer_index = translate_hands(dealer_showing, hand, possible_plays)
    if debug:
        print player_key, dealer_index, basic[player_key][dealer_index]

    return basic[player_key][dealer_index]

def translate_hands(dealer_showing, hand, possible_plays):
    dealer_index = -1
    if dealer_showing.rank == 1:
        dealer_index = 9
    else:
        dealer_index = dealer_showing.value - 2

    # Handle hands with more than 2 cards (just look at the total)
    player_key = ""
    hand.sort()
    if len(hand.cards) == 2:
        if hand.cards[0].rank == 1:
            if hand.cards[1].rank == 1:
                if possible_plays[2]:
                    player_key = "AA"
                else:
                    player_key = "12"
            else:
                player_key = "A" + str(hand.cards[1].value)
        elif hand.cards[0].rank == hand.cards[1].rank:
            player_key = str(hand.cards[0].value) + str(hand.cards[1].value)
        else:
            minimum, maximum = hand_value(hand)
            player_key = str(maximum) if maximum <= 16 else "17+"
    else:
        minimum, maximum = hand_value(hand)
        if maximum > 21:
            player_key = str(minimum) if minimum <= 16 else "17+"
        else:
            player_key = str(maximum) if maximum <= 16 else "17+"

    return player_key, dealer_index


def player_input(dealer_showing, player_hand, possible_plays):
    prompt = []
    if possible_plays[0]:
        prompt.append("insurance")
    if possible_plays[1]:
        prompt.append("surrender")
    if possible_plays[2]:
        prompt.append("split")
    if possible_plays[3]:
        prompt.append("double")
    prompt.append("stand")
    if possible_plays[5]:
        prompt.append("hit")
    
    prompt = "/".join(prompt)
    laszlo(dealer_showing, player_hand, possible_plays)

    choice = raw_input(prompt + " for hand " + str([str(c) for c in player_hand.cards]) + ": ")
    return choice

def player_bet_inputs(stack):
    bet = ""
    while not is_number(bet):
        bet = raw_input("What would you like to bet of " + str(stack) + "? ")
        if bet == "":
            return "rebet"
        if is_number(bet):
            return float(bet)

def buy_in_progression():
    buy = ""
    while not is_number(buy):
        buy = raw_input("What would you like to buy in for? ")
        if buy == "":
            return "rebet"
        if is_number(buy):
            return float(buy)


def bet_standard(stack):
    return 25

def laszlo_bet_progression(base, layer, wins):
    multi = [1,1,1.5,1.5,2,2,3,3,5,5,7,7,10,10,10,10,10,10,10]
    bet = base * layer
    if wins >= len(multi):
        bet = bet * 10
    else:
        bet = bet * multi[wins]
    return bet

def hand_value(hand):
    minimum = 0
    maximum = 0
    ace_count = 0
    for c in hand.cards:
        if c.rank == 1:
            if ace_count == 0:
                ace_count = 1
                minimum = minimum + 1
                maximum = maximum + 11
            else:
                minimum = minimum + 1
                maximum = maximum + 1
        elif c.rank in [11,12,13]:
            minimum = minimum + 10
            maximum = maximum + 10
        else:
            minimum = minimum + c.rank
            maximum = maximum + c.rank
    return minimum, maximum

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def main():
    record = []
    above = 0
    below = 0
    denom = 1000
    hands_per_round = 500
    playing = True
    layer_record = []
    streak_record = []
    cashed_out_count = 0
    for j in range(denom):
        investment = 200
        base = 25
        buy_in = 250
        layer = 1
        streak = 0
        blackjack = Table(maximum=10000)
        blackjack.buy_in("Zach", buy_in, None, laszlo)
        if debug:
            print "\n\n\n\n\n"
        for i in range(hands_per_round):
            # Play a hand
            streak_record.append(streak)
            layer_record.append(layer)
            # if blackjack.player_chips - investment > 250:
            #     print "Cashing out on top"
            #     cashed_out_count = cashed_out_count + 1
            #     break
            if debug:
                print "########################################"
            if blackjack.player_chips < base * layer:
                if debug:
                    print "Out of money"
                if playing:
                    layer_buy_ins = [250, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000]
                    buy_in = layer_buy_ins[layer]
                    layer = layer + 1
                    investment = investment + buy_in
                    blackjack.player_chips = blackjack.player_chips + buy_in
                    blackjack.reset()
                    print "Bought back in with", buy_in
            else:
                # blackjack.get_bets()
                print layer, "Streak: ", streak
                blackjack.place_bet(laszlo_bet_progression(base, layer, streak))
                blackjack.deal()
                if debug:
                    print blackjack
                blackjack.handle_player()
                blackjack.handle_dealer()
                blackjack.check_bets()
                streak = blackjack.win_streak
                if debug:
                    print blackjack.player_chips
        if blackjack.player_chips - investment > 0:
            above = above + 1
        else:
            below = below + 1
        record.append(blackjack.player_chips - investment)
        if j % 50 == 0:
            if j != 0:
                print j, ": ", float(above)/j, float(below)/j, sum(record)/len(record), min(record), max(record)
    print float(above)/denom, float(below)/denom, sum(record)/len(record), min(record), max(record)
    print max(layer_record), max(streak_record)
    print "Cashed out:", cashed_out_count



    
''' TODO:
    -handle case where player hits blackjack but dealer has ace showing
     Should allow user to make insurance bet
    -Also handle case where the player has blackjack and the dealer has 21
     with three or more cards (player should still win)
    -what about case where player has A, 2, 4? Should this be considered 
     the same as an A6 or should it be a 17?
'''


if __name__ == "__main__":
    main()