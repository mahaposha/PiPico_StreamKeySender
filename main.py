import digitalio
import board    # type: ignore
import time
import sys
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard import Keycode

"""
PINの定義
"""
# キー送信用ボタン(大ボタン)
button_pin_shortcut = [board.GP17, board.GP22, board.GP28,
                       board.GP13, board.GP10, board.GP6,
                       board.GP14, board.GP9, board.GP2]

# BGM制御用ボタンとLED
# !! 配列の要素数を一致させること
led_pin_bgm = [board.GP27, board.GP18]
button_pin_bgm = [board.GP16, board.GP21]

# ミュート制御用ボタンとLED
# !! 配列の要素数を一致させること
led_pin_mute = [board.GP11, board.GP7]
button_pin_mute = [board.GP15, board.GP5]


"""
KeyCodeの定義
"""
# !! PINの定義順と同じ並びにすること
keycode_shortcut = [
    [Keycode.ALT, Keycode.SHIFT, Keycode.ZERO],      # [GP17] [OBS] スタンバイ（シーン切替0）
    [Keycode.ALT, Keycode.SHIFT, Keycode.PERIOD],    # [GP22] [OBS] 投銭対応（シーン切替5)
    [Keycode.ALT, Keycode.SHIFT, Keycode.R],         # [GP28] [OBS] リプレイ(シーン切替6)
    [Keycode.ALT, Keycode.SHIFT, Keycode.ONE],       # [GP13] [OBS] シーン切替1
    [Keycode.ALT, Keycode.SHIFT, Keycode.TWO],       # [GP10] [OBS] シーン切替2
    [Keycode.ALT, Keycode.SHIFT, Keycode.THREE],     # [GP06] [OBS] シーン切替3
    [Keycode.ALT, Keycode.SHIFT, Keycode.FOUR],      # [GP14] [OBS] シーン切替4
    [Keycode.ALT, Keycode.SHIFT, Keycode.SEMICOLON], # [GP09] [OBS] グループ表示切替1
    [Keycode.ALT, Keycode.SHIFT, Keycode.COMMA],     # [GP02] [OBS] グループ表示切替2    
]

keycode_bgm = [
    [Keycode.ALT, Keycode.SHIFT, Keycode.A],         # [GP16] [VOICE-MOD] BGM再生/ストップ1
    [Keycode.ALT, Keycode.SHIFT, Keycode.B],         # [GP21] [VOICE-MOD] BGM再生/ストップ2    
]

keycode_mute = [
    [Keycode.ALT, Keycode.SHIFT, Keycode.D],         # [GP15] [OBS]デスクトップ音声をミュート
    [Keycode.ALT, Keycode.SHIFT, Keycode.M],         # [GP05] [OBS]マイクをミュート
]

kbd = Keyboard(usb_hid.devices)     # キーボード出力インスタンス


"""
親クラス定義
"""
# LEDのクラス
class led_class:
    def __init__(self, pin_num :board) -> None:
        self.ledPIN = digitalio.DigitalInOut(pin_num)
        self.ledPIN.direction = self.ledPIN.direction = digitalio.Direction.OUTPUT
        self.ledPIN.value = False
    
    def power_on(self) -> bool:
        # LEDを点灯させる
        self.ledPIN.value = True
        return self.ledPIN.value
        
    def power_off(self) -> bool:
        # LEDを消灯させる
        self.ledPIN.value = False
        return self.ledPIN.value
        
    def status(self) -> bool:
        return self.ledPIN.value

# ボタンのクラス
class button_class:
    def __init__(self, pin_num :board) -> None:
        self.mode = 0
        self.buttonPIN = digitalio.DigitalInOut(pin_num)
        self.buttonPIN.direction = digitalio.Direction.INPUT
        self.buttonPIN.pull = digitalio.Pull.UP
        self.pin = pin_num

    def check(self) -> bool:
        # 押しっぱなしをチェック （モード遷移）
        if self.buttonPIN.value is False:
            while self.buttonPIN.value is False:
                # ボタンを離すまで無限ループ
                time.sleep(0.05)
            return True
        return False

    def status(self) -> bool:
        return self.buttonPIN.value

# USBキーボードとしてのクラス
class USBkey_class:
    def __init__(self, key :list[Keycode]) -> None:
        self.sendkey_list = []
        for i in range(len(key)):
            self.sendkey_list.append(key[i])
    
    def send_key(self) -> None:
        kbd.send(*self.sendkey_list)


"""
子クラス定義
"""
# 大ボタン用（キー送信のみ）
class shortcut_class(button_class, USBkey_class):
    def __init__(self, 
                 button_pin :board, 
                 key_list :list[Keycode]) -> None:
        button_class.__init__(self, button_pin)
        USBkey_class.__init__(self, key_list)
        
    def check(self) -> bool:
        if button_class.check(self) is True:
            USBkey_class.send_key(self)
            return True
        return False
                          
# ミュート制御用(LEDによるモード表示)
class mute_class(button_class, led_class, USBkey_class):
    def __init__(self, 
                 button_pin :board,
                 led_pin :board, 
                 key_list :list[Keycode]) -> None:
        button_class.__init__(self, button_pin)
        led_class.__init__(self, led_pin)
        USBkey_class.__init__(self, key_list)
        self.mode = True    # [真] 再生中, [偽] ミュート状態
        
    def check(self) -> bool:
        if button_class.check(self) is True:
            self.mode_switch()
            USBkey_class.send_key(self)
            return True
        return False
    
    def mode_switch(self) -> None:
        if self.mode is True:
            led_class.power_on(self)
        else:
            led_class.power_off(self)
        self.mode = not self.mode # bool反転
        

"""
孫クラス定義
"""
# BGM制御用(LEDによるモード表示)    
class bgm_class(mute_class):
    def __init__(self, 
                 button_pin :board,
                 led_pin :board, 
                 key_list :Keycode) -> None:
        super().__init__(button_pin, led_pin, key_list)
        self.mode_bgm = False
        
    def check(self) -> bool:
        if super().check() is True:          
            return True
        return False
    
        
"""
クラス宣言
"""
# 大ボタン
button_shortcut = []
for i in range(len(button_pin_shortcut)):
    button_shortcut.append(shortcut_class(button_pin_shortcut[i], keycode_shortcut[i]))

# 小ボタン (BGM制御)    
if len(button_pin_bgm) != len(led_pin_bgm):
    print("Error:ボタンとLEDのPIN設定数が不一致 [bgm]")
    sys.exit()
button_bgm = [] 
for i in range(len(button_pin_mute)):
    button_bgm.append(bgm_class(button_pin_bgm[i], led_pin_bgm[i], keycode_bgm[i]))

# 小ボタン (ミュート制御)    
if len(button_pin_mute) != len(led_pin_mute):
    print("Error:ボタンとLEDのPIN設定数が不一致 [mute]")
    sys.exit()
button_mute = []
for i in range(len(button_pin_mute)):
    button_mute.append(mute_class(button_pin_mute[i], led_pin_mute[i], keycode_mute[i]))


"""
ループ処理
"""
while True:
    for i in range(len(button_shortcut)):
        button_shortcut[i].check()

    for i in range(len(button_bgm)):
        if button_bgm[i].check() is True:
            if button_bgm[i].mode_bgm is False:
                # 消灯中のボタンが押された場合の処理
                for j in range(len(button_bgm)):
                    # 他のBGM用ボタンを全て消灯
                    button_bgm[j].power_off()
                    button_bgm[j].mode_bgm = False
                button_bgm[i].power_on()
            button_bgm[i].mode_bgm = True   # 押されたボタンのモードをTrueに 

    for i in range(len(button_mute)):
        button_mute[i].check()
    
    time.sleep(0.1)