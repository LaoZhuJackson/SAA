from app.modules.water_bomb.decision import Status, Round


def get_action_and_probability(status_dict):
    """通过传入字典更新整个status对象，然后调用方法得到action"""
    # 更新 Status 对象
    round_fight = Round()
    status = Status.from_dict(status_dict)

    # 调用 win_prob 方法
    win_prob, strategy = round_fight.optimal_strategy(status)
    return win_prob, strategy

if __name__ == '__main__':
    # status_d = {'maxhp': 4,
    #           'shp': 4,
    #           'ehp': 3,
    #           'live': 0,
    #           'blank': 1,
    #           'fired': [],
    #           'sitems': ['handcuffs'],
    #           'eitems': [],
    #           'power': 1,
    #           'bullet': -1,
    #           'reversal': False,
    #           'extra_opp': False,
    #           'computer': False
    #           }
    # status_d = {
    #     'maxhp': 4,
    #     'shp': 4,
    #     'ehp': 3,
    #     'live': 0,
    #     'blank': 3,
    #     'fired': [],
    #     'sitems': ['reset_hammer', 'handcuffs', 'insight_sunglasses'],
    #     'eitems': [],
    #     'power': 1,
    #     'bullet': -1,
    #     'reversal': False, 'extra_opp': False, 'computer': False
    # }
    # status = {'maxhp': 4,
    #           'shp': 4,
    #           'ehp': 4,
    #           'live': 1,
    #           'blank': 1,
    #           'fired': [],
    #           'sitems': ['reverse_magic'],
    #           'eitems': ['unload_puppet', 'gem_of_life'],
    #           'power': 1, 'bullet': -1,
    #           'reversal': True,
    #           'extra_opp': False,
    #           'computer': False}
    # status = {'maxhp': 4,
    #           'shp': 4,
    #           'ehp': 3,
    #           'live': 2,
    #           'blank': 0,
    #           'fired': [],
    #           'sitems': ['advanced_barrel', 'gem_of_life', 'reset_hammer', 'insight_sunglasses'],
    #           'eitems': ['advanced_barrel', 'unload_puppet', 'unload_puppet', 'gem_of_life', 'handcuffs'],
    #           'power': 1,
    #           'bullet': -1,
    #           'reversal': False,
    #           'extra_opp': False,
    #           'computer': False}
    # status = {'maxhp': 3, 'shp': 2, 'ehp': 3, 'live': 0, 'blank': 1, 'fired': [], 'sitems': ['unload_puppet', 'hand_of_kaito'], 'eitems': [], 'power': 1, 'bullet': 0, 'reversal': False, 'extra_opp': False, 'computer': False}
    status = {'maxhp': 2, 'shp': 2, 'ehp': 2, 'live': 1, 'blank': 2, 'fired': [], 'sitems': ['gem_of_life', 'reset_hammer'], 'eitems': ['reverse_magic', 'reverse_magic', 'reverse_magic', 'reverse_magic', 'insight_sunglasses'], 'power': 1, 'bullet': 1, 'reversal': False, 'extra_opp': False, 'computer': False}
    win_pro,current_strategy = get_action_and_probability(status)

    print(f"状态：{status}")
    print(f"胜率：{win_pro}")
    print(f"策略：{current_strategy}")
