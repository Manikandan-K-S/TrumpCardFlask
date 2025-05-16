import random
from db import Cricket, update_game_result
from pprint import pprint

class GamePlay:
    def __init__(self, game_id, player1_email):
        self.game_id = game_id
        self.player1 = player1_email
        self.player2 = None
        self.turn = player1_email
        self.deck1 = []
        self.deck2 = []
        self.matched = False
        self.active = True
        self.starter = None

        self.last_result = None
        self.winner_of_game = None
        # New flag to track if current turn has been processed
        self.turn_processed = False

    def join(self, player2_email):
        """
        When second player joins, shuffle and split cards into two decks.
        Store cards as plain dicts to avoid DetachedInstanceError.
        """
        self.player2 = player2_email
        self.matched = True

        cards = Cricket.query.all()
        # cards = cards[0:10]
        random.shuffle(cards)
        mid = len(cards) // 2

        # Convert SQLAlchemy objects to dictionaries
        self.deck1 = [self._card_to_dict(card) for card in cards[:mid]]
        self.deck2 = [self._card_to_dict(card) for card in cards[mid:]]

    def _card_to_dict(self, card):
        data = card.__dict__.copy()
        # Remove SQLAlchemy state
        data.pop('_sa_instance_state', None)
        return data

    def get_current_turn(self):
        return self.turn

    def get_top_card(self, player_email):
        if player_email == self.player1 and self.deck1:
            return self.deck1[0]
        elif player_email == self.player2 and self.deck2:
            return self.deck2[0]
        return None

   

    def play_turn(self, player_email, attribute):
        if player_email != self.turn:
            return  # Not this player's turn

        card1 = self.deck1[0]
        card2 = self.deck2[0]


        

        val1 = card1.get(attribute)
        val2 = card2.get(attribute)
        if val1 is None or val2 is None:
            return  # Invalid attribute

        # Determine outcome
        if val1 > val2:
            winner_email = self.player1
            loser_email = self.player2
            winner_card = card1
            loser_card = card2
        else:
            winner_email = self.player2
            loser_email = self.player1
            winner_card = card2
            loser_card = card1

        


        if winner_email == self.player1:
            self.deck1.append(self.deck1.pop(0))
            self.deck1.append(self.deck2.pop(0))
            self.turn = self.player1
        else:
            self.deck2.append(self.deck2.pop(0))
            self.deck2.append(self.deck1.pop(0))
            self.turn = self.player2



        
        # Toggle the turn between the two players
        # self.turn = self.player1 if self.turn == self.player2 else self.player2

        game_ended = False
        final_winner = None
        if not self.deck1:
            game_ended = True
            final_winner = self.player2
            self.active = False
            self.winner_of_game = final_winner
            update_game_result(self.game_id, final_winner, self.player1)
        elif not self.deck2:
            game_ended = True
            final_winner = self.player1
            self.active = False
            self.winner_of_game = final_winner
            update_game_result(self.game_id, final_winner, self.player2)    

        # Store opponent card relative to the *current turn owner* (i.e. the player who played)
        opponent_card = card2 if player_email == self.player1 else card1

        self.last_result = {
            'winner': winner_email,
            'attribute': attribute,
            'won_card': winner_card,
            'lost_card': loser_card,
            'gameOver': game_ended,
            'overallWinner': final_winner if game_ended else None,
            'next_turn': self.turn
        }

        self.turn_processed = True

    def __str__(self):
        return f"Game ID: {self.game_id}, Player 1: {self.player1}, Player 2: {self.player2}, Turn: {self.turn}, Matched: {self.matched}"
