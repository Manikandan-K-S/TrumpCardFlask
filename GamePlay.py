import random
from db import db, Cricket, Games  

class GamePlay:
    def __init__(self, player1_email, player2_email):
        self.player1 = player1_email
        self.player2 = player2_email
        
        self.cards = Cricket.query.all()
        random.shuffle(self.cards)
        
        mid = len(self.cards) // 2
        self.player1_deck = self.cards[:mid]
        self.player2_deck = self.cards[mid:]
        
        self.current_turn = self.player1
        
        new_game = Games(player1=self.player1, player2=self.player2)
        db.session.add(new_game)
        db.session.commit()
  
        self.game_id = new_game.id
        
    def play_turn(self, chosen_stat):
      
        if not self.player1_deck or not self.player2_deck:
            return self.check_winner()
        
        card1 = self.player1_deck.pop(0)
        card2 = self.player2_deck.pop(0)
        
        value1 = getattr(card1, chosen_stat, 0)
        value2 = getattr(card2, chosen_stat, 0)
        
        if value1 > value2:
            self.player1_deck.append(card1)
            self.player1_deck.append(card2)
            winner = self.player1
        elif value2 > value1:
            self.player2_deck.append(card1)
            self.player2_deck.append(card2)
            winner = self.player2
        else:
            self.player1_deck.append(card1)
            self.player2_deck.append(card2)
            winner = None
        
        self.current_turn = self.player1 if self.current_turn == self.player2 else self.player2
        
        return {
            "winner": winner,
            "next_turn": self.current_turn,
            "remaining_cards": {self.player1: len(self.player1_deck), self.player2: len(self.player2_deck)}
        }
    
    def check_winner(self):
   
        if not self.player1_deck:
            return {"game_over": True, "winner": self.player2}
        elif not self.player2_deck:
            return {"game_over": True, "winner": self.player1}
        return {"game_over": False}
    
    def get_game_state(self):

        return {
            "game_id": self.game_id,
            "player1": self.player1,
            "player2": self.player2,
            "turn": self.current_turn,
            "player1_cards": len(self.player1_deck),
            "player2_cards": len(self.player2_deck)
        }
