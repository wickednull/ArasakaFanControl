#!/usr/bin/env python3
"""
ARASAKA FAN CONTROL - Cyberpunk Fan Controller for Raspberry Pi 5 / Hackberry Pi 5
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import threading
import json
import os
from pathlib import Path
import glob

# Try to import RPi.GPIO, but don't fail if not available
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except:
    HAS_GPIO = False

class Pi5Hardware:
    def __init__(self):
        self.fan_pwm_path = None
        self.fan_input_path = None
        self.temp_path = "/sys/class/thermal/thermal_zone0/temp"
        self.find_sysfs_paths()
        
    def find_sysfs_paths(self):
        try:
            fan_base = glob.glob("/sys/devices/platform/cooling_fan/hwmon/hwmon*")
            if fan_base:
                self.fan_pwm_path = f"{fan_base[0]}/pwm1"
                self.fan_input_path = f"{fan_base[0]}/fan1_input"
        except:
            pass
    
    def get_temperature(self):
        try:
            with open(self.temp_path, 'r') as f:
                return float(f.read().strip()) / 1000.0
        except:
            return 50.0
    
    def get_rpm(self):
        if not self.fan_input_path:
            return 0
        try:
            with open(self.fan_input_path, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    
    def set_speed(self, percent):
        if not self.fan_pwm_path:
            return False
        try:
            percent = max(0, min(100, percent))
            pwm_value = int(percent * 255 / 100)
            with open(self.fan_pwm_path, 'w') as f:
                f.write(str(pwm_value))
            return True
        except:
            return False
    
    def release(self):
        if self.fan_pwm_path:
            try:
                with open(self.fan_pwm_path, 'w') as f:
                    f.write("0")
            except:
                pass

class CoolingProfile:
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.curve_points = [(40, 0), (50, 30), (60, 60), (70, 85), (80, 100)]
        self.aggression = 50
        
    def calculate_speed(self, temp):
        if temp <= self.curve_points[0][0]:
            return self.curve_points[0][1]
        if temp >= self.curve_points[-1][0]:
            return self.curve_points[-1][1]
        
        for i in range(len(self.curve_points) - 1):
            t1, s1 = self.curve_points[i]
            t2, s2 = self.curve_points[i+1]
            if t1 <= temp <= t2:
                ratio = (temp - t1) / (t2 - t1)
                speed = s1 + ratio * (s2 - s1)
                speed = min(100, speed * (0.5 + self.aggression/100))
                return int(speed)
        return 0
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "curve_points": self.curve_points,
            "aggression": self.aggression
        }
    
    @classmethod
    def from_dict(cls, data):
        profile = cls(data["name"], data.get("description", ""))
        profile.curve_points = data["curve_points"]
        profile.aggression = data.get("aggression", 50)
        return profile

class ProfileManager:
    def __init__(self, profile_dir="profiles"):
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(exist_ok=True)
        self.profiles = {}
        self.load_all()
        
    def save_profile(self, profile):
        filepath = self.profile_dir / f"{profile.name.lower().replace(' ', '_')}.json"
        with open(filepath, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
        self.profiles[profile.name] = profile
        
    def load_all(self):
        self.profiles = {}
        for json_file in self.profile_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    profile = CoolingProfile.from_dict(data)
                    self.profiles[profile.name] = profile
            except:
                pass
        
        if not self.profiles:
            defaults = [
                CoolingProfile("Silent Work", "Low noise, moderate cooling"),
                CoolingProfile("Balanced", "Best balance of noise and cooling"),
                CoolingProfile("Gaming", "Aggressive cooling for gaming"),
                CoolingProfile("Overkill", "Maximum cooling - high noise")
            ]
            for p in defaults:
                if p.name == "Gaming":
                    p.curve_points = [(40, 20), (50, 50), (60, 80), (70, 100)]
                    p.aggression = 75
                elif p.name == "Overkill":
                    p.curve_points = [(35, 30), (45, 60), (55, 90), (65, 100)]
                    p.aggression = 100
                elif p.name == "Silent Work":
                    p.curve_points = [(40, 0), (55, 20), (70, 50), (80, 80)]
                    p.aggression = 20
                self.save_profile(p)

class ArasakaFanControl:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ARASAKA FAN CONTROL")
        self.root.geometry("700x700")  # Fits Hackberry Pi 5 screen
        self.root.configure(bg='#0a0a0f')
        
        self.hardware = Pi5Hardware()
        self.profile_manager = ProfileManager()
        self.current_profile = None
        self.running = True
        self.manual_mode = False
        self.manual_speed = 0
        
        self.temp_history = []
        self.rpm_history = []
        
        self.colors = {
            'bg': '#0a0a0f',
            'card': '#1a1a2e',
            'red': '#ff0033',
            'cyan': '#00ffff',
            'text': '#ffffff',
            'gray': '#8899aa'
        }
        
        self.setup_ui()
        
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.load_profile("Balanced")
        
    def setup_ui(self):
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header = tk.Label(main, text="▣ ARASAKA FAN CONTROL", 
                         font=('Helvetica', 18, 'bold'),
                         fg=self.colors['red'], bg=self.colors['bg'])
        header.pack(pady=10)
        
        # HUD Frame
        hud_frame = tk.Frame(main, bg=self.colors['card'], relief='ridge', bd=1)
        hud_frame.pack(fill=tk.X, pady=10)
        
        # Temperature
        temp_frame = tk.Frame(hud_frame, bg=self.colors['card'])
        temp_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        tk.Label(temp_frame, text="CPU TEMP", fg=self.colors['gray'], 
                bg=self.colors['card']).pack()
        self.temp_label = tk.Label(temp_frame, text="--.-°C", 
                                  font=('Helvetica', 32, 'bold'),
                                  fg=self.colors['cyan'], bg=self.colors['card'])
        self.temp_label.pack()
        
        # RPM
        rpm_frame = tk.Frame(hud_frame, bg=self.colors['card'])
        rpm_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        tk.Label(rpm_frame, text="FAN RPM", fg=self.colors['gray'],
                bg=self.colors['card']).pack()
        self.rpm_label = tk.Label(rpm_frame, text="----", 
                                 font=('Helvetica', 32, 'bold'),
                                 fg=self.colors['cyan'], bg=self.colors['card'])
        self.rpm_label.pack()
        
        # Speed
        speed_frame = tk.Frame(hud_frame, bg=self.colors['card'])
        speed_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        tk.Label(speed_frame, text="FAN PWM", fg=self.colors['gray'],
                bg=self.colors['card']).pack()
        self.speed_label = tk.Label(speed_frame, text="---%",
                                   font=('Helvetica', 32, 'bold'),
                                   fg=self.colors['cyan'], bg=self.colors['card'])
        self.speed_label.pack()
        
        # Graph Frame
        graph_frame = tk.Frame(main, bg=self.colors['card'])
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        plt.style.use('dark_background')
        self.fig = plt.Figure(figsize=(6, 3), facecolor=self.colors['card'], dpi=80)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.colors['card'])
        self.ax.grid(True, alpha=0.2, color=self.colors['red'])
        self.ax.set_xlabel('Time (s)', color=self.colors['gray'])
        self.ax.set_ylabel('Temp (°C)', color=self.colors['gray'])
        self.ax.tick_params(colors=self.colors['gray'])
        
        self.temp_line, = self.ax.plot([], [], color=self.colors['red'], linewidth=2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control Frame
        control_frame = tk.Frame(main, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=10)
        
        # Mode toggle
        self.mode_var = tk.StringVar(value="auto")
        auto_btn = tk.Radiobutton(control_frame, text="AUTO", variable=self.mode_var,
                                 value="auto", command=self.toggle_mode,
                                 bg=self.colors['bg'], fg=self.colors['cyan'],
                                 selectcolor=self.colors['bg'])
        auto_btn.pack(side=tk.LEFT, padx=10)
        
        manual_btn = tk.Radiobutton(control_frame, text="MANUAL", variable=self.mode_var,
                                   value="manual", command=self.toggle_mode,
                                   bg=self.colors['bg'], fg=self.colors['cyan'],
                                   selectcolor=self.colors['bg'])
        manual_btn.pack(side=tk.LEFT, padx=10)
        
        # Manual slider
        self.slider = tk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                              length=200, bg=self.colors['bg'], fg=self.colors['cyan'],
                              highlightthickness=0, state='disabled',
                              command=self.on_manual_speed)
        self.slider.pack(side=tk.LEFT, padx=20)
        self.slider_val = tk.Label(control_frame, text="0%", bg=self.colors['bg'],
                                  fg=self.colors['cyan'])
        self.slider_val.pack(side=tk.LEFT)
        
        # Profiles Frame
        profiles_frame = tk.LabelFrame(main, text="COOLING PROFILES",
                                      fg=self.colors['red'], bg=self.colors['card'],
                                      font=('Helvetica', 10, 'bold'))
        profiles_frame.pack(fill=tk.X, pady=10)
        
        # Profile buttons
        btn_frame = tk.Frame(profiles_frame, bg=self.colors['card'])
        btn_frame.pack(pady=10)
        
        profiles = ["Silent Work", "Balanced", "Gaming", "Overkill"]
        for i, profile in enumerate(profiles):
            btn = tk.Button(btn_frame, text=profile,
                           bg=self.colors['card'], fg=self.colors['cyan'],
                           relief='flat', padx=10,
                           command=lambda p=profile: self.load_profile(p))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Aggression slider
        agg_frame = tk.Frame(profiles_frame, bg=self.colors['card'])
        agg_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(agg_frame, text="AGGRESSION:", fg=self.colors['gray'],
                bg=self.colors['card']).pack(side=tk.LEFT)
        
        self.agg_slider = tk.Scale(agg_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                  length=300, bg=self.colors['card'],
                                  fg=self.colors['cyan'], highlightthickness=0,
                                  command=self.on_aggression_change)
        self.agg_slider.pack(side=tk.LEFT, padx=10)
        self.agg_val = tk.Label(agg_frame, text="50%", bg=self.colors['card'],
                               fg=self.colors['cyan'])
        self.agg_val.pack(side=tk.LEFT)
        
        # Save button
        save_btn = tk.Button(profiles_frame, text="💾 SAVE CURRENT",
                             bg=self.colors['red'], fg=self.colors['bg'],
                             relief='flat', padx=20, command=self.save_current_profile)
        save_btn.pack(pady=10)
        
        # Status bar
        self.status = tk.Label(main, text="● SYSTEM READY", fg=self.colors['cyan'],
                               bg=self.colors['bg'], font=('Helvetica', 8))
        self.status.pack(pady=5)
    
    def load_profile(self, name):
        if name in self.profile_manager.profiles:
            self.current_profile = self.profile_manager.profiles[name]
            self.agg_slider.set(self.current_profile.aggression)
            self.agg_val.config(text=f"{self.current_profile.aggression}%")
            self.status.config(text=f"● LOADED: {name}", fg=self.colors['cyan'])
            self.root.after(2000, lambda: self.status.config(text="● SYSTEM READY"))
    
    def save_current_profile(self):
        if self.current_profile:
            self.current_profile.aggression = int(self.agg_slider.get())
            self.profile_manager.save_profile(self.current_profile)
            self.status.config(text=f"● SAVED: {self.current_profile.name}", fg=self.colors['red'])
            self.root.after(2000, lambda: self.status.config(text="● SYSTEM READY"))
            messagebox.showinfo("Saved", f"Profile '{self.current_profile.name}' saved!")
    
    def toggle_mode(self):
        if self.mode_var.get() == "manual":
            self.manual_mode = True
            self.slider.config(state='normal')
            self.status.config(text="● MANUAL MODE", fg=self.colors['red'])
        else:
            self.manual_mode = False
            self.slider.config(state='disabled')
            self.status.config(text="● AUTO MODE", fg=self.colors['cyan'])
    
    def on_manual_speed(self, value):
        self.manual_speed = int(float(value))
        self.slider_val.config(text=f"{self.manual_speed}%")
        if self.manual_mode:
            self.hardware.set_speed(self.manual_speed)
    
    def on_aggression_change(self, value):
        if self.current_profile:
            self.current_profile.aggression = int(float(value))
            self.agg_val.config(text=f"{self.current_profile.aggression}%")
    
    def monitoring_loop(self):
        while self.running:
            try:
                temp = self.hardware.get_temperature()
                rpm = self.hardware.get_rpm()
                
                if not self.manual_mode and self.current_profile:
                    target = self.current_profile.calculate_speed(temp)
                    self.hardware.set_speed(target)
                    current_speed = target
                elif self.manual_mode:
                    current_speed = self.manual_speed
                else:
                    current_speed = 0
                
                # Update history
                now = time.time()
                self.temp_history.append((now, temp))
                self.rpm_history.append((now, rpm))
                
                cutoff = now - 60
                self.temp_history = [(t, v) for t, v in self.temp_history if t > cutoff]
                self.rpm_history = [(t, v) for t, v in self.rpm_history if t > cutoff]
                
                self.root.after(0, self.update_display, temp, rpm, current_speed)
                
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(1)
    
    def update_display(self, temp, rpm, speed):
        self.temp_label.config(text=f"{temp:.1f}°C")
        self.rpm_label.config(text=f"{int(rpm)}")
        self.speed_label.config(text=f"{speed}%")
        
        if temp > 75:
            self.temp_label.config(fg='#ff0033')
        elif temp > 65:
            self.temp_label.config(fg='#ff8800')
        else:
            self.temp_label.config(fg='#00ffff')
        
        self.update_graph()
    
    def update_graph(self):
        if len(self.temp_history) < 2:
            return
        
        now = time.time()
        times = [t - now for t, _ in self.temp_history]
        temps = [v for _, v in self.temp_history]
        
        self.temp_line.set_data(times, temps)
        
        if times:
            self.ax.set_xlim(min(times), 0)
            self.ax.set_ylim(20, max(temps + [100]))
        
        self.canvas.draw_idle()
    
    def on_closing(self):
        self.running = False
        self.hardware.release()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ArasakaFanControl()
    app.run()
