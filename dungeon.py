# given time
remaining_time = '123456.0987654321' 
field_names = ['current_location', 'current_experience', 'current_date']

import datetime
import re
import json
import csv
import os.path
from decimal import *
from collections import defaultdict


class Player:
    experience_pattern = re.compile(r'exp([0-9]+)_')
    time_pattern = re.compile(r'tm([0-9.]+)')

    def __init__(self, required_experience, time_remained, player_name='R2D2'):
        self.name = player_name
        self.state = {'current_location': 'entrance', 'current_experience': 0}
        self.history = []
        self.remaining_time = Decimal(time_remained)
        self.killed_mobs = defaultdict(int)
        self._save_current_state()
        self.required_experience = required_experience
        
    def __str__(self):
        return f'Игрок {self.name} находится здесь: {self.state["current_location"]}, опыт: ' \
               f'{self.state["current_experience"]}, 'f'осталось времени: {self.remaining_time} сек.'

    def _reformat_time(self, time: datetime.datetime):
        time_format = '%d.%m.%Y %H:%M:%S'
        return time.strftime(time_format)

    def _check_the_time(self, object: str):
        match = re.search(Player.time_pattern, object)
        spent_time = Decimal(match.group(1))
        self.remaining_time -= spent_time

    def _save_current_state(self, location=None, experience=0):
        self.state['current_location'] = location if location else self.state['current_location']
        self.state['current_experience'] += experience
        self.state['current_date'] = datetime.datetime.now()
        current_state = {}
        current_state.update(self.state)
        self.history.append(current_state)

    def _get_location_as_str(self, location: (dict, str)):
        if isinstance(location, dict):
            result = tuple(location.keys())[0]
            return result

    def _get_available_actions(self, location: dict):
        location_content = location.get(self._get_location_as_str(location))
        actions = []
        mobs = defaultdict(int)
        for mob in location_content:
            if not isinstance(mob, str):
                continue
            mobs[mob] += 1
        for mob, killed_count in self.killed_mobs.items():
            mobs[mob] -= killed_count
        for action in location_content:
            row = {'action': action}
            if isinstance(action, dict):
                action_as_str = self._get_location_as_str(action)
                if self._hatch(action_as_str):
                    row['info'] = f'Выбраться через ЛЮК {action_as_str}'
                    row['type'] = 'hatch'
                else:
                    row['info'] = f'Шагнуть дальше в локацию {action_as_str}'
                    row['type'] = 'current_location'
            elif isinstance(action, str):
                if mobs[action] <= 0:
                    continue
                mobs[action] -= 1
                row['info'] = f'Сразиться с монстром {action} и получить опыт'
                row['type'] = 'mob'
            actions.append(row)
        actions.append({'info': 'Завершить текущую игру.', 'type': 'quit'})
        return actions

    def _check_user_choice(self, actions):
        while True:
            print('Введите номер: ')
            choice = input()
            if not choice.isdigit():
                print('Нельзя использовать буквы. Попробуйте снова')
            elif not (1 <= int(choice) <= len(actions)):
                print('Неверный ввод. Попробуйте снова')
            else:
                return actions[int(choice) - 1]

    def _fight_mob(self, mob: str):
        experience_gained = 0
        match = re.search(Player.experience_pattern, mob)
        if match:
            experience_gained = int(match.group(1))
            self.state['current_experience'] += experience_gained
        self._check_the_time(mob)
        self.killed_mobs[mob] += 1
        print(f'Монстр {mob} побежден, вы получаете {experience_gained} очков(-а) опыта.')

    def _hatch(self, location: str):
        return 'hatch' in location.lower()

    def handle_location(self, location: (dict, str), first_time_here=True):
        while True:
            location_as_str = self._get_location_as_str(location)
            if first_time_here:
                self.killed_mobs = defaultdict(int)
                self._check_the_time(location_as_str)
            self._save_current_state(location=location_as_str)
            if self.remaining_time <= 0:
                print('Вы не успели! Время закончилось! Игра завершена\n')
                return False
            if self._hatch(self.state['current_location']):
                print('Вы успешно добрались до люка. Игра пройдена')
                self._save_current_state(location='exit')
                return False
            actions = self._get_available_actions(location)
            if all(row['type'] == 'mob' for row in actions):
                print('Впереди нет новых локаций. Игра окончена.')
                return False
            print('Ваше текущее состояние')
            print(f'{self}\n')
            print('Выберите дальнейшее действие:')
            for i, action in enumerate(actions, start=1):
                print(f'{i}. {action["info"]}')
            chosen = self._check_user_choice(actions)
            print(f'Вы выбрали: {chosen["info"]}\n')
            if chosen['type'] == 'quit':
                return False
            elif chosen['type'] == 'current_location':
                location = chosen['action']
                self._get_available_actions(location)
                self._check_the_time(str(location))
            elif chosen['type'] == 'mob':
                mob = chosen['action']
                self._fight_mob(mob)
                self.handle_location(location, first_time_here=False)
            elif chosen['type'] == 'hatch':
                exp_lack = self.required_experience - self.state['current_experience']
                if exp_lack > 0:
                    print(f'Не хватает опыта для открытия люка: {exp_lack}, сразитесь с монстрами для увеличения опыта')
                    self._get_available_actions(location)
                self.handle_location(chosen['action'])


    def save_history(self):
        out_filename = os.path.join(os.path.dirname(__file__), f'dungeon.csv')
        out_filename = os.path.normpath(out_filename)
        with open(out_filename, 'w', newline='') as new_file:
            writer = csv.DictWriter(new_file, fieldnames=self.history[0], delimiter=',')
            writer.writeheader()
            for state in self.history:
                state['current_date'] = self._reformat_time(state['current_date'])
                writer.writerow(state)
            print(f'История игры игрока "{self.name}" сохранена в файл: {out_filename}')


def new_game(maze):
    player = Player(time_remained='123456.0987654321', required_experience=280)
    player.handle_location(maze)
    player.save_history()


def main():
    with open('rpg.json') as source:
        maze = json.load(source)
        new_game(maze)


if __name__ == '__main__':
    main()
