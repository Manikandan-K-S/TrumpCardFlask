import random
import json
from db import get_cricket_card_by_id, update_win_stats, add_game, get_game_by_id, update_game_result

class GamePlay:
    def __init__(self, game_id, player1, player2, player1_cards, player2_cards):
        """
        Initializes the game with players and their decks.
        :param game_id: Unique game identifier.
        :param player1: Email of player1.
        :param player2: Email of player2.
        :param player1_cards: List of Cricket card IDs for player1.
        :param player2_cards: List of Cricket card IDs for player2.
        """
        self.game_id = game_id
        self.player1 = player1
        self.player2 = player2
        self.turn = player1  # Player 1 starts by default
        self.decks = {
            player1: player1_cards,
            player2: player2_cards
        }

    def get_current_turn(self):
        """Returns the player whose turn it is."""
        return self.turn

    def get_top_card(self, player):
        """Returns the top card of a player's deck."""
        if self.decks[player]:
            return get_cricket_card_by_id(self.decks[player][0])
        return None

    def play_turn(self, player, attribute):
        """
        Handles turn logic when a player selects an attribute.
        :param player: Player's email who is playing.
        :param attribute: Selected attribute to compare.
        :return: Result dictionary containing turn outcome.
        """
        if player != self.turn:
            return {"error": "Not your turn!"}

        opponent = self.player1 if player == self.player2 else self.player2

        player_card = self.get_top_card(player)
        opponent_card = self.get_top_card(opponent)

        if not player_card or not opponent_card:
            return {"error": "One of the players has no cards left!"}

        # Compare attribute values
        player_value = getattr(player_card, attribute, None)
        opponent_value = getattr(opponent_card, attribute, None)

        if player_value is None or opponent_value is None:
            return {"error": "Invalid attribute selected!"}

        # Determine winner
        if player_value > opponent_value:
            winner = player
            loser = opponent
            self.decks[winner].append(self.decks[loser].pop(0))  # Transfer opponent's card
            result = "win"
        elif player_value < opponent_value:
            winner = opponent
            loser = player
            self.decks[winner].append(self.decks[player].pop(0))  # Transfer player's card
            result = "lose"
        else:
            result = "draw"
            winner = None
            loser = None

        # Store win statistics if there's a winner
        if winner:
            update_win_stats(self.decks[winner][0], attribute)

        # Check game over condition
        if not self.decks[loser]:
            update_game_result(self.game_id, winner, loser)
            return {"game_over": True, "winner": winner, "loser": loser}

        # Switch turn
        self.turn = opponent

        return {
            "result": result,
            "winner": winner,
            "loser": loser,
            "next_turn": self.turn,
            "player_card": player_card,
            "opponent_card": opponent_card
        }
