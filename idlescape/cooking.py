class Cooking:
    """
    Outline of how cooking works:
    > Split into cooking and alchemy
    > Cooking / Alchemy breakpoints are 30 / 20

    Alchemy
    -------
    > Size controls stack count
    > Alchemy controls rarity
    > Vial type controls recipe type
    > Effective level controls bonus

    ##Small Vial
    | Potion Rarity | stackStrength | stackMultiplier |
    | ------------- | ------------- | --------------- |
    | Common        | 1.0           | 1.5             |
    | Rare          | 2.0           | 1.5             |
    | Epic          | 3.0           | 1.0             |
    | Legendary     | 4.0           | 1.0             |

    ##Medium Vial
    | Potion Rarity | stackStrength | stackMultiplier |
    | ------------- | ------------- | --------------- |
    | Common        | 1.0           | 2.5             |
    | Rare          | 2.0           | 2.5             |
    | Epic          | 3.0           | 2.5             |
    | Legendary     | 4.0           | 1.5             |

    ##Large Vial
    | Potion Rarity | stackStrength | stackMultiplier |
    | ------------- | ------------- | --------------- |
    | Common        | 2.0           | 1.0             |
    | Rare          | 3.0           | 1.0             |
    | Epic          | 4.0           | 1.0             |
    | Legendary     | ---           | ---             |
    """

    def __init__(self, player):
        self.player = player
        self.items = self.player.item_data
