from faker.providers import BaseProvider


class CatererProvider(BaseProvider):
    __provider__ = "caterer"
    __lang__ = "en_US"

    caterers = [
        "CollectiveGreenSF",
        "TwoFish Baking Co.",
        "La PanotiQ SF",
        "Chubby Noodle",
        "Fang",
        "TRILOGI SF",
        "Choux Bakery",
        "Maite Catering",
        "Romper Room Cocktails",
        "Market & Rye",
        "Wanna-E",
        "Little Skillet",
        "Trattoria da Vittorio",
        "LaLe",
        "Baan Restaurant & Wine Bar",
        "Jardin",
        "Los Shucos",
        "Davey Jones Deli -- DO NOT USE",
        "Worldly Burgers",
        "Fine and Rare from The Hall -- DO NOT USE",
        "Zomelette",
        "Tip Top Tapas",
        "Estrellita's Snacks",
        "The Noodle Stand",
        "Uff Da Eats",
        "EGGURRITO",
        "Karina's Mexican Bakery",
        "Wise Sons Jewish Delicatessen",
        "Proper Food -- DO NOT USE",
        "Bicycle Banh Mi",
        "Sharpshooter",
        "Carmel Pizza Co",
        "Lchaim Sushi",
        "City Breakfast Club",
        "O'Mai Cafe",
        "Bissap Baobab",
    ]

    @classmethod
    def caterer(cls):
        return cls.random_element(cls.caterers)
