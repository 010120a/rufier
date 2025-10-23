from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.properties import BooleanProperty, NumericProperty
from kivy.core.window import Window

# Убраны глобальные переменные, они будут храниться в классе приложения

white = (1, 1, 1, 1)  # Исправлен цвет - Kivy использует значения от 0 до 1
Window.clearcolor = white

# === Инструкции ===
txt_test1 = '[color=000000]' + 'Замерьте пульс за 15 секунд.\nРезультат запишите в \nсоответствующее поле.' + '[/color]'
txt_test2 = '[color=000000]' + 'Выполните 30 приседаний за 45 секунд.\nНажмите кнопку "Начать",\n чтобы запустить счётчик приседаний.\nДелайте приседания со скоростью счётчика.' + '[/color]'
txt_test3 = '[color=000000]' + 'В течение минуты замерьте пульс два \nраза: за первые 15 секунд \nминуты, затем за последние 15 секунд.\nРезультаты запишите в соответствующие поля.' + '[/color]'
txt_pulse = '[color=000000]' + 'Введите пульс' + '[/color]'

''' Модуль для расчета результатов пробы Руфье. '''
# здесь задаются строки, с помощью которых изложен результат:
txt_index = "Ваш индекс Руфье: "
txt_workheart = "Работоспособность сердца: "
txt_nodata = '''
нет данных для такого возраста'''
txt_res = []
txt_res.append('''низкая.
Срочно обратитесь к врачу!''')
txt_res.append('''удовлетворительная.
Обратитесь к врачу!''')
txt_res.append('''средняя.
Возможно, стоит дополнительно обследоваться у врача.''')
txt_res.append('''
выше среднего''')
txt_res.append('''
высокая''')


def ruffier_index(P1, P2, P3):
   ''' возвращает значение индекса по трем показателям пульса для сверки с таблицей'''
   return (4 * (P1+P2+P3) - 200) / 10


def neud_level(age):
   ''' варианты с возрастом меньше 7 и взрослым надо обрабатывать отдельно,
   здесь подбираем уровень "неуд" только внутри таблицы:
   в возрасте 7 лет "неуд" - это индекс 21, дальше каждые 2 года он понижается на 1.5 до значения 15 в 15-16 лет '''
   norm_age = (min(age, 15) - 7) // 2  # каждые 2 года разницы от 7 лет превращаются в единицу - вплоть до 15 лет
   result = 21 - norm_age * 1.5 # умножаем каждые 2 года разницы на 1.5, так распределены уровни в таблице
   return result

def ruffier_result(r_index, level):
   ''' функция получает индекс Руфье и интерпретирует его,
   возвращает уровень готовности: число от 0 до 4
   (чем выше уровень готовности, тем лучше).  '''
   if r_index >= level:
       return 0
   level = level - 4 # это не будет выполняться, если мы уже вернули ответ "неуд"
   if r_index >= level:
       return 1
   level = level - 5 # аналогично, попадаем сюда, если уровень как минимум "уд"
   if r_index >= level:
       return 2
   level = level - 5.5 # следующий уровень
   if r_index >= level:
       return 3
   return 4 # здесь оказались, если индекс меньше всех промежуточных уровней, т.е. тестируемый крут.


def test(P1, P2, P3, age):
   ''' эту функцию можно использовать снаружи модуля для подсчетов индекса Руфье.
   Возвращает готовые тексты, которые остается нарисовать в нужном месте
   Использует для текстов константы, заданные в начале этого модуля. '''
   if age < 7:
       return (txt_index + "0", txt_nodata) # тайна сия не для теста сего
   else:
       ruff_index = ruffier_index(P1, P2, P3) # расчет
       result = txt_res[ruffier_result(ruff_index, neud_level(age))] # интерпретация, перевод числового уровня подготовки в текстовые данные
       res = txt_index + str(ruff_index) + '\n' + txt_workheart + result
       return res


# === Таймер с событием done ===
class Seconds(Label):
    done = BooleanProperty(False)
    current = NumericProperty(0)

    def __init__(self, total, **kwargs):
        super().__init__(**kwargs)
        self.total = total
        self.current = 0
        self.markup = True
        self.text = f'[color=000000]Прошло секунд: {self.current}[/color]'

    def start(self):
        self.done = False
        self.current = 0
        Clock.schedule_interval(self.change, 1)

    def change(self, dt):
        self.current += 1
        self.markup = True
        self.text = f'[color=000000]Прошло секунд: {self.current}[/color]'
        if self.current >= self.total:
            self.done = True
            return False

    def restart(self, total):
        self.total = total
        self.current = 0
        self.start()


# === Проверка целого числа ===
def check_int(peremennaja):
    try:
        return int(peremennaja)
    except:
        return False


# === Кнопка для переключения экранов с валидацией ===
class ScrButton(Button):
    def __init__(self, screen, direction='right', goal='main', validator=None, **kwargs):
        super().__init__(**kwargs)
        self.screen = screen
        self.direction = direction
        self.goal = goal
        self.validator = validator

    def on_press(self):
        if self.validator:
            valid, message = self.validator()
            if not valid:
                popup = Popup(title="Ошибка ввода", content=Label(text=message),
                              size_hint=(0.7, 0.3))
                popup.open()
                return
        self.screen.manager.transition.direction = self.direction
        self.screen.manager.current = self.goal


# === Главный экран ===
class MainScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vl = BoxLayout(orientation='vertical', padding=8, spacing=8)
        hl = BoxLayout()
        txt = Label(text='[color=000000]' +'Выбери экран'+ '[/color]', markup = True)
        vl.add_widget(ScrButton(self, direction='down', goal='first', text="1"))
        vl.add_widget(ScrButton(self, direction='left', goal='second', text="2"))
        vl.add_widget(ScrButton(self, direction='up', goal='third', text="3"))
        vl.add_widget(ScrButton(self, direction='right', goal='fourth', text="4"))
        hl.add_widget(txt)
        hl.add_widget(vl)
        self.add_widget(hl)


# === Первый экран ===
class FirstScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vl = BoxLayout(orientation='vertical', size_hint=(.5, .5), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        btn = Button(text='Выбор: 1')
        btn_back = ScrButton(self, direction='up', goal='main', text="Назад")
        vl.add_widget(btn)
        vl.add_widget(btn_back)
        self.add_widget(vl)


# === Экран ввода имени и возраста ===
class SecondScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vl = BoxLayout(orientation='vertical')

        line_0 = BoxLayout(size_hint=(0.8, None), height='30sp')
        line_05 = BoxLayout(size_hint=(0.8, None), height='30sp')
        lbl1 = Label(text='[color=000000]' + 'Введите имя:' + '[/color]', halign='right', markup=True)
        lbl2 = Label(text='[color=000000]' + 'Введите возраст:' + '[/color]', halign='right', markup=True)
        self.input_name = TextInput(multiline=False)
        self.input_age = TextInput(multiline=False)

        line_0.add_widget(lbl1)
        line_05.add_widget(lbl2)
        line_0.add_widget(self.input_name)
        line_05.add_widget(self.input_age)
        vl.add_widget(line_0)
        vl.add_widget(line_05)

        hl = BoxLayout(size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5})
        btn_next = ScrButton(self, direction='right', goal='puls', text="OK", validator=self.validate, size_hint=(0.7, 0.1))
        hl.add_widget(btn_next)
        vl.add_widget(hl)
        self.add_widget(vl)

    def validate(self):
        name = self.input_name.text.strip()
        age_text = self.input_age.text.strip()
        if not name:
            return False, "Введите имя"
        if not age_text.isdigit():
            return False, "Возраст должен быть числом"
        age = int(age_text)
        if age < 7:
            return False, "Возраст должен быть не меньше 7"
        
        # Сохраняем данные в приложении
        app = App.get_running_app()
        app.user_name = name
        app.user_age = age
        
        return True, ""


# === Экран ввода пульса ===
class InputPulsScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vl = BoxLayout(orientation='vertical')
        instr = Label(text=txt_test1, markup=True)
        vl.add_widget(instr)

        # Таймер — не запускаем сразу
        self.lbl_sec = Seconds(15)  # 15 секунд для первого измерения
        self.lbl_sec.bind(done=self.sec_finished)
        vl.add_widget(self.lbl_sec)

        # Поле ввода пульса — выключено до окончания таймера
        line_0 = BoxLayout(size_hint=(0.8, None), height='30sp')
        lbl1 = Label(text=txt_pulse, halign='right', markup=True)
        self.input_puls = TextInput(multiline=False, disabled=True)

        line_0.add_widget(lbl1)
        line_0.add_widget(self.input_puls)
        vl.add_widget(line_0)

        # Кнопка с надписью "Начать" и двойной логикой
        hl = BoxLayout(size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5})
        self.btn_NEXT = Button(text="Начать")
        self.btn_NEXT.bind(on_press=self.on_btn_next_press)
        hl.add_widget(self.btn_NEXT)

        vl.add_widget(hl)
        self.add_widget(vl)

        self.timer_started = False  # состояние кнопки

    def on_btn_next_press(self, instance):
        if not self.timer_started:
            # Если таймер ещё не был запущен, запускаем его
            self.timer_started = True
            self.lbl_sec.start()
            self.btn_NEXT.disabled = True  # блокируем кнопку до окончания таймера
        else:
            # Если таймер уже прошёл — проверяем ввод и переходим
            valid, message = self.validate()
            if not valid:
                popup = Popup(title="Ошибка ввода", content=Label(text=message),
                              size_hint=(0.7, 0.3))
                popup.open()
                return
            
            # Сохраняем данные в приложении
            app = App.get_running_app()
            app.p1 = int(self.input_puls.text)
            
            self.manager.transition.direction = 'right'
            self.manager.current = 'sits'

    def sec_finished(self, *args):
        # Когда таймер завершился, меняем кнопку и включаем поле
        self.input_puls.disabled = False
        self.btn_NEXT.text = "Продолжить"
        self.btn_NEXT.disabled = False

    def validate(self):
        text = self.input_puls.text.strip()
        if not text.isdigit():
            return False, "Пульс должен быть целым числом"
        if int(text) <= 0:
            return False, "Пульс должен быть положительным числом"
        return True, ""


# === Экран приседаний ===
class InputPulsExScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vl = BoxLayout(orientation='vertical')
        self.txt = Label(text=txt_test2, markup=True)
        vl.add_widget(self.txt)

        self.lbl_sec = Seconds(15)  # 45 секунд для приседаний
        self.lbl_sec.bind(done=self.sec_finished)
        vl.add_widget(self.lbl_sec)

        line_0 = BoxLayout(size_hint=(0.8, None), height='30sp')
        lbl1 = Label(text=txt_pulse, halign='right', markup=True)
        self.input_puls = TextInput(multiline=False, disabled=True)

        line_0.add_widget(lbl1)
        line_0.add_widget(self.input_puls)
        vl.add_widget(line_0)

        hl = BoxLayout(size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5})
        self.btn_NEXT = Button(text="Начать")
        self.btn_NEXT.bind(on_press=self.on_btn_next_press)
        hl.add_widget(self.btn_NEXT)
        vl.add_widget(hl)
        self.add_widget(vl)

        self.timer_started = False

    def on_btn_next_press(self, instance):
        if not self.timer_started:
            self.timer_started = True
            self.lbl_sec.start()
            self.btn_NEXT.disabled = True
        else:
            valid, message = self.validate()
            if not valid:
                popup = Popup(title="Ошибка ввода", content=Label(text=message),
                              size_hint=(0.7, 0.3))
                popup.open()
                return
            
            # Сохраняем данные в приложении
            app = App.get_running_app()
            app.p2 = int(self.input_puls.text)
            
            self.manager.transition.direction = 'right'
            self.manager.current = 'otdih'

    def sec_finished(self, *args):
        self.input_puls.disabled = False
        self.btn_NEXT.text = "Продолжить"
        self.btn_NEXT.disabled = False

    def validate(self):
        text = self.input_puls.text.strip()
        if not text.isdigit():
            return False, "Пульс должен быть целым числом"
        if int(text) <= 0:
            return False, "Пульс должен быть положительным числом"
        return True, ""


# === Экран пульса после отдыха ===
class InputPulsOtScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vl = BoxLayout(orientation='vertical')
        self.txt = Label(text=txt_test3, markup=True)
        vl.add_widget(self.txt)

        self.lbl_sec = Seconds(10)  # 60 секунд отдыха
        self.lbl_sec.bind(done=self.sec_finished)
        vl.add_widget(self.lbl_sec)

        line_0 = BoxLayout(size_hint=(0.8, None), height='30sp')
        lbl1 = Label(text=txt_pulse, halign='right', markup=True)
        self.input_puls = TextInput(multiline=False, disabled=True)

        line_0.add_widget(lbl1)
        line_0.add_widget(self.input_puls)
        vl.add_widget(line_0)

        hl = BoxLayout(size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5})
        self.btn_NEXT = Button(text="Начать")
        self.btn_NEXT.bind(on_press=self.on_btn_next_press)
        hl.add_widget(self.btn_NEXT)
        vl.add_widget(hl)
        self.add_widget(vl)

        self.timer_started = False

    def on_btn_next_press(self, instance):
        if not self.timer_started:
            self.timer_started = True
            self.lbl_sec.start()
            self.btn_NEXT.disabled = True
        else:
            valid, message = self.validate()
            if not valid:
                popup = Popup(title="Ошибка ввода", content=Label(text=message),
                              size_hint=(0.7, 0.3))
                popup.open()
                return
            
            # Сохраняем данные в приложении
            app = App.get_running_app()
            app.p3 = int(self.input_puls.text)
            
            self.manager.transition.direction = 'right'
            self.manager.current = 'rezult'

    def sec_finished(self, *args):
        self.input_puls.disabled = False
        self.btn_NEXT.text = "Продолжить"
        self.btn_NEXT.disabled = False

    def validate(self):
        text = self.input_puls.text.strip()
        if not text.isdigit():
            return False, "Пульс должен быть целым числом"
        if int(text) <= 0:
            return False, "Пульс должен быть положительным числом"
        return True, ""


# === Экран результата ===
# === Экран результата ===
class ResultScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vl = BoxLayout(orientation='vertical')
        self.lbl_index = Label(text='Ваш индекс:', color=(0, 0, 0, 1))
        self.lbl_result = Label(text='Результат:', color=(0, 0, 0, 1))
        vl.add_widget(self.lbl_index)
        vl.add_widget(self.lbl_result)

        hl = BoxLayout(size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5})
        btn_NEXT = ScrButton(self, direction='right', goal='main', text="Завершить")
        hl.add_widget(btn_NEXT)
        vl.add_widget(hl)
        self.add_widget(vl)

    def on_enter(self):
        # Получаем данные из приложения
        app = App.get_running_app()
        result_text = test(app.p1, app.p2, app.p3, app.user_age)
        
        # Разделяем результат на части
        result_parts = result_text.split('\n')
        
        # Устанавливаем тексты для меток
        self.lbl_index.text = f"Ваш индекс Руфье: {result_parts[0]}"
        self.lbl_result.text = f"Работоспособность сердца: {result_parts[1] if len(result_parts) > 1 else ''}"

# === Прочие экраны ===
class ThirdScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        test_label = Label(text="Всё плохо")
        btn_back = ScrButton(self, direction='down', goal='main', text="Назад")
        layout.add_widget(test_label)
        layout.add_widget(btn_back)
        self.add_widget(layout)


class FourthScr(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vl = BoxLayout(orientation='vertical', spacing=8)
        a = 'START ' + 'очень плохо ' * 200
        test_label = Label(text="Дополнительное задание", size_hint=(0.3, None))
        btn_back = ScrButton(self, direction='left', goal='main', text="Назад", size_hint=(1, .2))
        self.label = Label(text=a, size_hint_y=None, font_size='24sp', halign='left', valign='top')
        self.label.bind(size=self.resize)
        self.scroll = ScrollView(size_hint=(1, 1))
        self.scroll.add_widget(self.label)

        vl.add_widget(test_label)
        vl.add_widget(btn_back)
        vl.add_widget(self.scroll)
        self.add_widget(vl)

    def resize(self, *args):
        self.label.text_size = (self.label.width, None)
        self.label.texture_update()
        self.label.height = self.label.texture_size[1]


# === Приложение ===
class MyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Инициализируем переменные для хранения данных пользователя
        self.user_name = ""
        self.user_age = 0
        self.p1 = 0
        self.p2 = 0
        self.p3 = 0

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScr(name='main'))
        sm.add_widget(FirstScr(name='first'))
        sm.add_widget(SecondScr(name='second'))
        sm.add_widget(InputPulsScr(name='puls'))
        sm.add_widget(InputPulsExScr(name='sits'))
        sm.add_widget(InputPulsOtScr(name='otdih'))
        sm.add_widget(ResultScr(name='rezult'))
        sm.add_widget(ThirdScr(name='third'))
        sm.add_widget(FourthScr(name='fourth'))
        return sm


if __name__ == '__main__':
    MyApp().run()